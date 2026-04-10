import json
import os
import re
from typing import Any, Dict, List

INPUT = "data/data.json"
OUTPUT = "output/jobs.normalized.json"


def ensure_output_dir() -> None:
    os.makedirs("output", exist_ok=True)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    return re.sub(r"\s+", " ", str(value)).strip()


def deep_get(obj: Dict[str, Any], keys: List[str], default: str = "") -> str:
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            if isinstance(value, list):
                return " ".join(clean_text(v) for v in value)
            return clean_text(value)
    return default


def walk_records(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ["data", "jobs", "list", "rows", "items", "result"]:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return [data]
    return []


def normalize_job(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    job_title = deep_get(item, ["job_title", "title", "positionName", "name", "岗位名称"])
    job_desc = deep_get(item, ["job_desc", "description", "jd", "detail", "岗位描述"])
    company = deep_get(item, ["company", "company_name", "companyName", "企业"])
    city = deep_get(item, ["city", "location", "job_city", "工作地点"])
    salary = deep_get(item, ["salary", "salary_range", "薪资"])
    degree = deep_get(item, ["degree", "education", "学历要求"])
    experience = deep_get(item, ["experience", "exp", "经验要求"])
    skills = deep_get(item, ["skills", "skill_tags", "tags", "keywords"])
    url = deep_get(item, ["url", "link", "job_url"])
    job_id = deep_get(item, ["job_id", "id", "positionId"]) or f"job-{index}"

    full_text = " ".join([job_title, job_desc, skills, degree, experience]).strip()

    return {
        "job_id": job_id,
        "job_title": job_title,
        "job_desc": job_desc,
        "company": company,
        "city": city,
        "salary": salary,
        "degree": degree,
        "experience": experience,
        "skills": skills,
        "url": url,
        "full_text": full_text,
        "raw": item,
    }


def main() -> None:
    ensure_output_dir()
    data = load_json(INPUT)
    records = walk_records(data)
    normalized = []
    seen = set()

    for idx, item in enumerate(records, start=1):
        row = normalize_job(item, idx)
        key = (row["job_id"], row["job_title"], row["company"])
        if not row["job_title"] and not row["job_desc"]:
            continue
        if key in seen:
            continue
        seen.add(key)
        normalized.append(row)

    normalized.sort(key=lambda x: (x["job_title"], x["company"], x["job_id"]))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
