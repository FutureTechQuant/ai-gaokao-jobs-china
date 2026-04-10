import json
import os


MAJORS_FILE = "output/majors.normalized.json"
JOBS_FILE = "output/jobs.normalized.json"
MAJOR_JOB_RULES_FILE = "config/major_job_rules.json"
AI_RULES_FILE = "config/ai_replace_rules.json"

OUTPUT_FILE = "output/major_ai_rate.json"
DEBUG_FILE = "output/major_ai_rate.debug.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def contains_any(text, keywords):
    text = (text or "").lower()
    for kw in keywords:
        if kw.lower() in text:
            return True
    return False


def score_job(job, ai_rules):
    exposure = int(job.get("exposure", 0) or 0)
    base = exposure / 10.0

    text = " ".join([
        job.get("job_title", ""),
        job.get("category", ""),
        job.get("job_desc", ""),
        job.get("avg_salary", "")
    ]).lower()

    score = base
    reasons = [f"base_from_exposure:{exposure}/10"]

    for item in ai_rules.get("plus_if_contains", []):
        keywords = item.get("keywords", [])
        delta = float(item.get("score", 0))
        if contains_any(text, keywords):
            score += delta
            reasons.append(f"+{delta}:{'/'.join(keywords)}")

    for item in ai_rules.get("minus_if_contains", []):
        keywords = item.get("keywords", [])
        delta = float(item.get("score", 0))
        if contains_any(text, keywords):
            score -= delta
            reasons.append(f"-{delta}:{'/'.join(keywords)}")

    for item in ai_rules.get("title_set_score", []):
        keywords = item.get("keywords", [])
        set_score = float(item.get("set_score", score))
        if contains_any(job.get("job_title", ""), keywords):
            score = set_score
            reasons.append(f"set:{set_score}:{'/'.join(keywords)}")

    if job.get("highlighted"):
        bonus = float(ai_rules.get("highlighted_bonus", 0))
        score += bonus
        reasons.append(f"+{bonus}:highlighted")

    return clamp(score), reasons


def confidence(job_count, total_workers):
    if job_count >= 8 and total_workers >= 5000000:
        return "high"
    if job_count >= 4 and total_workers >= 1000000:
        return "medium"
    return "low"


def get_rule_for_major(major, rules_data):
    code_rules = rules_data.get("major_code_rules", {})
    category_rules = rules_data.get("major_category_rules", {})
    discipline_rules = rules_data.get("discipline_rules", {})

    major_code = major.get("major_code", "")
    major_category = major.get("major_category", "")
    discipline = major.get("discipline", "")

    if major_code in code_rules:
        return code_rules[major_code], "major_code", major_code

    if major_category in category_rules:
        return category_rules[major_category], "major_category", major_category

    if discipline in discipline_rules:
        return discipline_rules[discipline], "discipline", discipline

    return None, None, None


def match_jobs_by_rule(scored_jobs, rule):
    include_categories = rule.get("include_categories", [])
    include_titles = rule.get("include_titles", [])
    exclude_titles = rule.get("exclude_titles", [])

    matched = []
    for job in scored_jobs:
        hit_category = job["category"] in include_categories if include_categories else False
        hit_title = contains_any(job["job_title"], include_titles) if include_titles else False
        excluded = contains_any(job["job_title"], exclude_titles) if exclude_titles else False

        if excluded:
            continue

        if hit_category or hit_title:
            matched.append(job)

    return matched


def main():
    os.makedirs("output", exist_ok=True)

    majors = load_json(MAJORS_FILE)
    jobs = load_json(JOBS_FILE)
    rules_data = load_json(MAJOR_JOB_RULES_FILE)
    ai_rules = load_json(AI_RULES_FILE)

    scored_jobs = []
    for job in jobs:
        score, reasons = score_job(job, ai_rules)
        one = dict(job)
        one["ai_replace_score"] = round(score, 4)
        one["ai_score_reasons"] = reasons
        scored_jobs.append(one)

    results = []
    debug = []

    for major in majors:
        code = major["major_code"]
        name = major["major_name"]

        rule, rule_level, rule_key = get_rule_for_major(major, rules_data)

        if not rule:
            results.append({
                "major_code": code,
                "major_name": name,
                "degree_level": major["degree_level"],
                "discipline": major["discipline"],
                "major_category": major["major_category"],
                "rule_level": None,
                "rule_key": None,
                "replace_rate": None,
                "exposure_score": None,
                "matched_jobs": 0,
                "total_workers": 0,
                "confidence": "unmapped",
                "sample_matches": []
            })
            continue

        matched = match_jobs_by_rule(scored_jobs, rule)

        total_workers = sum(x.get("employment_workers", 0) for x in matched)
        weighted_score_sum = sum(
            x.get("employment_workers", 0) * x.get("ai_replace_score", 0)
            for x in matched
        )

        if total_workers > 0:
            replace_rate = round(weighted_score_sum / total_workers, 4)
            exposure_score = round(replace_rate * 100, 2)
        else:
            replace_rate = None
            exposure_score = None

        sample_matches = []
        for x in sorted(matched, key=lambda z: z.get("employment_workers", 0), reverse=True)[:8]:
            sample_matches.append({
                "job_title": x["job_title"],
                "category": x["category"],
                "employment_workers": x["employment_workers"],
                "exposure": x["exposure"],
                "ai_replace_score": x["ai_replace_score"]
            })

        results.append({
            "major_code": code,
            "major_name": name,
            "degree_level": major["degree_level"],
            "discipline": major["discipline"],
            "major_category": major["major_category"],
            "rule_level": rule_level,
            "rule_key": rule_key,
            "replace_rate": replace_rate,
            "exposure_score": exposure_score,
            "matched_jobs": len(matched),
            "total_workers": total_workers,
            "confidence": confidence(len(matched), total_workers),
            "sample_matches": sample_matches
        })

        debug.append({
            "major_code": code,
            "major_name": name,
            "discipline": major["discipline"],
            "major_category": major["major_category"],
            "rule_level": rule_level,
            "rule_key": rule_key,
            "matched_job_titles": [x["job_title"] for x in matched]
        })

    results.sort(key=lambda x: (
        x["replace_rate"] is None,
        -(x["replace_rate"] or -1),
        x["major_code"]
    ))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        json.dump(debug, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
