import json
import os


MAJORS_JSON = "output/majors.normalized.json"
JOBS_JSON = "output/jobs.normalized.json"
RULES_JSON = "output/major_job_rules.auto.json"
AI_RULES_JSON = "config/ai_replace_rules.json"

OUTPUT_FILE = "output/major_ai_rate.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clamp(x, lo=0, hi=1):
    return max(lo, min(hi, x))


def score_job(job, replace_rules):
    text = (
        str(job.get("job_title", "")) + " " +
        str(job.get("category", "")) + " " +
        str(job.get("job_desc", ""))
    ).lower()

    score = replace_rules.get("base", 0.35)

    for kw in replace_rules.get("high_plus", []):
        if kw.lower() in text:
            score += 0.12

    for kw in replace_rules.get("mid_plus", []):
        if kw.lower() in text:
            score += 0.06

    for kw in replace_rules.get("minus", []):
        if kw.lower() in text:
            score -= 0.10

    exposure = job.get("exposure", 0)
    if isinstance(exposure, int):
        score += min(exposure, 5) * 0.03

    return round(clamp(score), 4)


def match_jobs_for_major(rule, jobs):
    include_titles = set(rule.get("include_titles", []))
    include_categories = set(rule.get("include_categories", []))
    exclude_titles = set(rule.get("exclude_titles", []))

    matched = []
    for job in jobs:
        jt = job.get("job_title", "")
        jc = job.get("category", "")

        if jt in exclude_titles:
            continue

        if jt in include_titles or jc in include_categories:
            matched.append(job)

    return matched


def main():
    majors = load_json(MAJORS_JSON)
    jobs = load_json(JOBS_JSON)
    rules_data = load_json(RULES_JSON)
    replace_rules = load_json(AI_RULES_JSON)

    code_rules = rules_data.get("major_code_rules", {})

    scored_jobs = []
    for job in jobs:
        job = dict(job)
        job["ai_replace_score"] = score_job(job, replace_rules)
        scored_jobs.append(job)

    result = []
    for major in majors:
        code = major["major_code"]
        rule = code_rules.get(code, {"include_titles": [], "include_categories": [], "exclude_titles": []})
        matched_jobs = match_jobs_for_major(rule, scored_jobs)

        if matched_jobs:
            replace_rate = round(sum(j["ai_replace_score"] for j in matched_jobs) / len(matched_jobs), 4)
        else:
            replace_rate = 0.0

        job_titles = sorted(list({j["job_title"] for j in matched_jobs}))[:20]

        result.append({
            "major_code": code,
            "major_name": major["major_name"],
            "degree_level": major.get("degree_level", ""),
            "discipline": major.get("discipline", ""),
            "major_category": major.get("major_category", ""),
            "replace_rate": replace_rate,
            "job_count": len(matched_jobs),
            "matched_job_titles_sample": job_titles,
            "confidence": "high" if len(matched_jobs) >= 8 else "medium" if len(matched_jobs) >= 3 else "low"
        })

    result.sort(key=lambda x: (-x["replace_rate"], -x["job_count"], x["major_code"]))
    save_json(OUTPUT_FILE, result)
    print(f"generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()