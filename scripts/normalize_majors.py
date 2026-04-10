import json
import os
import re


INPUT_FILE = "data/all.json"
OUTPUT_FILE = "output/majors.normalized.json"


def ensure_output():
    os.makedirs("output", exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick(d, *keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def to_text(v):
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v).strip()


def extract_employment_direction(major):
    candidates = [
        pick(major, "已毕业人员从业方向"),
        pick(major, "就业方向"),
        pick(major, "从业方向"),
        pick(major, "毕业去向")
    ]

    for c in candidates:
        if isinstance(c, dict):
            raw = pick(c, "原始文本", default="")
            arr = pick(c, "列表", default=[])
            if raw:
                return str(raw).strip()
            if isinstance(arr, list) and arr:
                return "".join([str(x).strip() for x in arr if x]).strip()
        elif isinstance(c, list):
            text = "".join([str(x).strip() for x in c if x]).strip()
            if text:
                return text
        elif isinstance(c, str) and c.strip():
            return c.strip()

    return ""


def normalize_major(major, degree_level, discipline, major_category):
    major_code = to_text(pick(major, "专业代码", "code", "major_code", "zydm", default=""))
    major_name = to_text(pick(major, "专业名称", "name", "major_name", "zymc", default=""))
    duration = to_text(pick(major, "修业年限", "duration", default=""))
    degree = to_text(pick(major, "授予学位", "degree", default=""))
    detail_url = to_text(pick(major, "详情页", "detail_url", "url", default=""))
    introduction = to_text(pick(major, "专业介绍", "introduction", "简介", default=""))
    employment_direction_raw = extract_employment_direction(major)

    return {
        "major_code": major_code,
        "major_name": major_name,
        "degree_level": degree_level,
        "discipline": discipline,
        "major_category": major_category,
        "duration": duration,
        "degree": degree,
        "detail_url": detail_url,
        "introduction": introduction,
        "employment_direction_raw": employment_direction_raw
    }


def main():
    ensure_output()
    data = load_json(INPUT_FILE)

    degree_levels = pick(data, "培养层次列表", "data", default=[])
    if not isinstance(degree_levels, list):
        raise ValueError("all.json 中未找到培养层次列表")

    rows = []
    seen = set()

    for level_item in degree_levels:
        degree_level = to_text(pick(level_item, "培养层次", "name", default=""))
        discipline_list = pick(level_item, "门类列表", "items", default=[])

        if not isinstance(discipline_list, list):
            continue

        for discipline_item in discipline_list:
            discipline = to_text(pick(discipline_item, "门类", "name", default=""))
            major_category_list = pick(discipline_item, "专业类列表", "items", default=[])

            if not isinstance(major_category_list, list):
                continue

            for category_item in major_category_list:
                major_category = to_text(pick(category_item, "专业类", "name", default=""))
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

    rows.sort(key=lambda x: x["major_code"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"majors normalized: {len(rows)}")


if __name__ == "__main__":
    main()