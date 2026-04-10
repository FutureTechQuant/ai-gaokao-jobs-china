import json
import math
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

MAJORS_INPUT = "output/majors.normalized.json"
JOBS_INPUT = "output/jobs.normalized.json"
RULES_INPUT = "config/major_job_rules.json"
AI_RULES_INPUT = "config/ai_replace_rules.json"
OUTPUT_JSON = "output/major_ai_rate.json"
OUTPUT_DEBUG = "output/major_ai_rate.debug.json"


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def contains_keyword(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if keyword in text:
        return True
    if any(ch in keyword for ch in "|,+"):
        parts = [x.strip() for x in re.split(r"[|,+]", keyword) if x.strip()]
        return all(part in text for part in parts)
    return False


def score_job(job: Dict[str, Any], rules: Dict[str, Any]) -> Tuple[float, List[str]]:
    text = " ".join([
        str(job.get("job_title", "")),
        str(job.get("job_desc", "")),
        str(job.get("skills", "")),
        str(job.get("degree", "")),
        str(job.get("experience", "")),
    ]).lower()

    score = float(rules.get("base", 0.35))
    reasons: List[str] = []

    for item in rules.get("high_plus", []):
        kw = item["keyword"] if isinstance(item, dict) else str(item)
        delta = float(item.get("score", 0.12)) if isinstance(item, dict) else 0.12
        if contains_keyword(text, kw):
            score += delta
            reasons.append(f"+{delta:.2f}:{kw}")

    for item in rules.get("mid_plus", []):
        kw = item["keyword"] if isinstance(item, dict) else str(item)
        delta = float(item.get("score", 0.06)) if isinstance(item, dict) else 0.06
        if contains_keyword(text, kw):
            score += delta
            reasons.append(f"+{delta:.2f}:{kw}")

    for item in rules.get("minus", []):
        kw = item["keyword"] if isinstance(item, dict) else str(item)
        delta = float(item.get("score", 0.10)) if isinstance(item, dict) else 0.10
        if contains_keyword(text, kw):
            score -= delta
            reasons.append(f"-{delta:.2f}:{kw}")

    for item in rules.get("title_overrides", []):
        kw = item["keyword"]
        value = float(item["set_score"])
        if contains_keyword(str(job.get("job_title", "")).lower(), kw):
            score = value
            reasons.append(f"set:{value:.2f}:{kw}")

    return clamp(score), reasons


def confidence_label(job_count: int, matched_weight: float) -> str:
    if job_count >= 30 and matched_weight >= 10:
        return "high"
    if job_count >= 10 and matched_weight >= 3:
        return "medium"
    return "low"


def main() -> None:
    os.makedirs("output", exist_ok=True)

    majors: List[Dict[str, Any]] = load_json(MAJORS_INPUT)
    jobs: List[Dict[str, Any]] = load_json(JOBS_INPUT)
    major_rules: Dict[str, List[Dict[str, Any]]] = load_json(RULES_INPUT)
    ai_rules: Dict[str, Any] = load_json(AI_RULES_INPUT)

    scored_jobs: List[Dict[str, Any]] = []
    for job in jobs:
        score, reasons = score_job(job, ai_rules)
        item = dict(job)
        item["ai_replace_score"] = round(score, 4)
        item["ai_score_reasons"] = reasons
        scored_jobs.append(item)

    result: List[Dict[str, Any]] = []
    debug_rows: List[Dict[str, Any]] = []

    for major in majors:
        code = major.get("major_code", "")
        name = major.get("major_name", "")
        mappings = major_rules.get(code, [])

        weighted_sum = 0.0
        weight_sum = 0.0
        job_count = 0
        matched_titles = []

        for rule in mappings:
            keyword = str(rule.get("job_keyword", "")).lower().strip()
            weight = float(rule.get("weight", 0))
            if not keyword or weight <= 0:
                continue

            matched_for_rule = 0
            for job in scored_jobs:
                haystack = " ".join([
                    str(job.get("job_title", "")),
                    str(job.get("job_desc", "")),
                    str(job.get("skills", "")),
                ]).lower()
                if contains_keyword(haystack, keyword):
                    weighted_sum += float(job["ai_replace_score"]) * weight
                    weight_sum += weight
                    job_count += 1
                    matched_for_rule += 1
                    if len(matched_titles) < 20:
                        matched_titles.append({
                            "job_title": job.get("job_title", ""),
                            "company": job.get("company", ""),
                            "keyword": keyword,
                            "score": job.get("ai_replace_score", 0),
                        })

            debug_rows.append({
                "major_code": code,
                "major_name": name,
                "job_keyword": keyword,
                "weight": weight,
                "matched_jobs": matched_for_rule,
            })

        replace_rate = round((weighted_sum / weight_sum), 4) if weight_sum > 0 else 0.0
        exposure_score = round(replace_rate * 100, 2)

        result.append({
            "major_code": code,
            "major_name": name,
            "discipline": major.get("discipline", ""),
            "major_category": major.get("major_category", ""),
            "degree_level": major.get("degree_level", ""),
            "replace_rate": replace_rate,
            "exposure_score": exposure_score,
            "job_count": job_count,
            "matched_weight": round(weight_sum, 4),
            "confidence": confidence_label(job_count, weight_sum),
            "sample_matches": matched_titles,
        })

    result.sort(key=lambda x: (-x["replace_rate"], x["major_code"], x["major_name"]))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DEBUG, "w", encoding="utf-8") as f:
        json.dump({
            "rules_count": len(major_rules),
            "majors_count": len(majors),
            "jobs_count": len(scored_jobs),
            "debug_rows": debug_rows,
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
