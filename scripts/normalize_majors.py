import json
import os
from typing import Any, Dict, List, Optional


INPUT_FILE = "data/all.json"
OUTPUT_FILE = "output/majors.normalized.json"


def ensure_output() -> None:
    os.makedirs("output", exist_ok=True)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def to_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float, bool)):
        return str(v).strip()
    return json.dumps(v, ensure_ascii=False).strip()


def recursive_find_first(obj: Any, target_keys: List[str]) -> Optional[Any]:
    if isinstance(obj, dict):
        for k in target_keys:
            if k in obj and obj[k] not in (None, "", [], {}):
                return obj[k]
        for v in obj.values():
            found = recursive_find_first(v, target_keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = recursive_find_first(item, target_keys)
            if found not in (None, "", [], {}):
                return found
    return None


def extract_employment_direction(major: Dict[str, Any]) -> str:
    direct = pick(
        major,
        "已毕业人员从业方向",
        "就业方向",
        "从业方向",
        "毕业去向",
        default=None
    )

    if isinstance(direct, dict):
        raw = pick(direct, "原始文本", default="")
        arr = pick(direct, "列表", default=[])
        if raw:
            return to_text(raw)
        if isinstance(arr, list) and arr:
            return "".join([to_text(x) for x in arr if x]).strip()

    if isinstance(direct, list):
        return "".join([to_text(x) for x in direct if x]).strip()

    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    found = recursive_find_first(
        major,
        ["已毕业人员从业方向", "就业方向", "从业方向", "毕业去向"]
    )

    if isinstance(found, dict):
        raw = pick(found, "原始文本", default="")
        arr = pick(found, "列表", default=[])
        if raw:
            return to_text(raw)
        if isinstance(arr, list) and arr:
            return "".join([to_text(x) for x in arr if x]).strip()

    if isinstance(found, list):
        return "".join([to_text(x) for x in found if x]).strip()

    if isinstance(found, str):
        return found.strip()

    return ""


def extract_degree_levels(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        for key in ["培养层次列表", "data", "list", "items", "rows", "result"]:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    raise ValueError("all.json 无法识别培养层次列表结构")


def normalize_major(
    major: Dict[str, Any],
    degree_level: str,
    discipline: str,
    major_category: str
) -> Dict[str, Any]:
    return {
        "major_code": to_text(pick(major, "专业代码", "code", "major_code", "zydm", default="")),
        "major_name": to_text(pick(major, "专业名称", "name", "major_name", "zymc", default="")),
        "degree_level": degree_level,
        "discipline": discipline,
        "major_category": major_category,
        "duration": to_text(pick(major, "修业年限", "duration", default="")),
        "degree": to_text(pick(major, "授予学位", "degree", default="")),
        "detail_url": to_text(pick(major, "详情页", "detail_url", "url", default="")),
        "introduction": to_text(pick(major, "专业介绍", "introduction", "简介", default="")),
        "employment_direction_raw": extract_employment_direction(major)
    }


def main() -> None:
    ensure_output()
    data = load_json(INPUT_FILE)
    degree_levels = extract_degree_levels(data)

    rows: List[Dict[str, Any]] = []
    seen = set()

    for level_item in degree_levels:
        degree_level = to_text(pick(level_item, "名称", "培养层次", "name", default=""))
        discipline_list = pick(level_item, "门类列表", "items", default=[])

        if not isinstance(discipline_list, list):
            continue

        for discipline_item in discipline_list:
            if not isinstance(discipline_item, dict):
                continue

            discipline = to_text(pick(discipline_item, "门类", "名称", "name", default=""))
            major_category_list = pick(discipline_item, "专业类列表", "items", default=[])

            if not isinstance(major_category_list, list):
                continue

            for category_item in major_category_list:
                if not isinstance(category_item, dict):
                    continue

                major_category = to_text(pick(category_item, "专业类", "名称", "name", default=""))
                major_list = pick(category_item, "专业列表", "items", default=[])

                if not isinstance(major_list, list):
                    continue

                for major in major_list:
                    if not isinstance(major, dict):
                        continue

                    row = normalize_major(major, degree_level, discipline, major_category)

                    if not row["major_code"] or not row["major_name"]:
                        continue

                    key = (row["major_code"], row["major_name"])
                    if key in seen:
                        continue

                    seen.add(key)
                    rows.append(row)

    rows.sort(key=lambda x: (x["major_code"], x["major_name"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"majors normalized: {len(rows)}")


if __name__ == "__main__":
    main()