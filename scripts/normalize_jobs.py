import json
import os
import re
from typing import Any, Dict, List


INPUT_FILE = "data/data.json"
OUTPUT_FILE = "output/jobs.normalized.json"


def ensure_output() -> None:
    os.makedirs("output", exist_ok=True)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_job_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        for key in ["occupations", "data", "jobs", "list", "rows", "items", "result"]:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        if "title" in data and "category" in data:
            return [data]

    raise ValueError(
        "data.json 无法识别岗位列表结构；支持 list，或 dict 中包含 occupations/data/jobs/list/rows/items/result"
    )


def parse_int(v: Any, default: int = 0) -> int:
    if v is None or v == "":
        return default
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).replace(",", "").strip()
    m = re.search(r"-?\d+", s)
    return int(m.group()) if m else default


def parse_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    return s in {"true", "1", "yes", "y", "是"}


def parse_salary_mid(s: Any):
    if not s:
        return None

    text = str(s).strip()
    text = text.replace("＋", "+").replace("—", "-").replace("–", "-")
    text = text.replace("万+", "万")

    nums = re.findall(r"(\d+(?:\.\d+)?)", text)
    if not nums:
        return None

    vals = [float(x) for x in nums]
    if len(vals) == 1:
        return vals[0]
    return round((vals[0] + vals[1]) / 2, 2)


def normalize_one(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    title = str(item.get("title", "")).strip()
    category = str(item.get("category", "")).strip()
    employment_workers = parse_int(item.get("employment_workers", 0), 0)
    exposure = parse_int(item.get("exposure", 0), 0)
    highlighted = parse_bool(item.get("highlighted", False))
    avg_salary = str(item.get("avgSalary", "")).strip()
    detail = str(item.get("detail", "")).strip()
    source_url = str(item.get("source_url", "")).strip()

    salary_mid = parse_salary_mid(avg_salary)

    full_text = " ".join([title, category, detail, avg_salary]).strip()

    return {
        "job_id": f"job-{idx}",
        "job_title": title,
        "category": category,
        "employment_workers": employment_workers,
        "exposure": exposure,
        "highlighted": highlighted,
        "avg_salary": avg_salary,
        "salary_mid_wan": salary_mid,
        "job_desc": detail,
        "source_url": source_url,
        "full_text": full_text
    }


def main() -> None:
    ensure_output()
    data = load_json(INPUT_FILE)
    raw_jobs = extract_job_list(data)

    rows = []
    for idx, item in enumerate(raw_jobs, start=1):
        row = normalize_one(item, idx)
        if not row["job_title"]:
            continue
        rows.append(row)

    rows.sort(key=lambda x: (x["category"], x["job_title"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"jobs normalized: {len(rows)}")


if __name__ == "__main__":
    main()