import json
import os
import re
from typing import Any, Dict, List

INPUT = "data/all.json"
OUTPUT = "output/majors.normalized.json"


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
            return clean_text(value)
    return default


def walk_records(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ["data", "list", "rows", "result", "items"]:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return [data]
    return []


def normalize_major(item: Dict[str, Any]) -> Dict[str, Any]:
    major_code = deep_get(item, ["major_code", "code", "zydm", "special_id", "specialCode"])
    major_name = deep_get(item, ["major_name", "name", "zymc", "title", "specialName"])
    discipline = deep_get(item, ["discipline", "门类", "mldm_name", "level1_name", "category"])
    major_category = deep_get(item, ["major_category", "专业类", "zyldm_name", "level2_name", "class_name"])
    degree_level = deep_get(item, ["degree_level", "level", "层次", "bkcc", "education_level"])
    select_requirements = deep_get(item, ["select_requirements", "xk_requirements", "选科要求", "subject_requirements"])
    detail_url = deep_get(item, ["detail_url", "url", "detailUrl", "link"])
    spec_id = deep_get(item, ["spec_id", "specId", "special_id"])

    if not major_code:
        m = re.search(r"\b(\d{6})\b", json.dumps(item, ensure_ascii=False))
        if m:
            major_code = m.group(1)

    if not spec_id and detail_url:
        m = re.search(r"detail(\d+)", detail_url)
        if m:
            spec_id = m.group(1)

    return {
        "major_code": major_code,
        "major_name": major_name,
        "discipline": discipline,
        "major_category": major_category,
        "degree_level": degree_level,
        "select_requirements": select_requirements,
        "spec_id": spec_id,
        "detail_url": detail_url,
        "raw": item,
    }


def main() -> None:
    ensure_output_dir()
    data = load_json(INPUT)
    records = walk_records(data)
    normalized = []
    seen = set()

    for item in records:
        row = normalize_major(item)
        key = (row["major_code"], row["major_name"])
        if not row["major_code"] and not row["major_name"]:
            continue
        if key in seen:
            continue
        seen.add(key)
        normalized.append(row)

    normalized.sort(key=lambda x: (x["major_code"], x["major_name"]))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
