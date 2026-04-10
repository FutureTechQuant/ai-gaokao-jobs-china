import json
import os


INPUT_FILE = "data/all.json"
OUTPUT_FILE = "output/majors.normalized.json"


def ensure_output():
    os.makedirs("output", exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in (None, ""):
            return d[k]
    return default


def normalize_major(major, degree_level, discipline, major_category):
    major_code = str(pick(major, "专业代码", "code", "major_code", "zydm", default="")).strip()
    major_name = str(pick(major, "专业名称", "name", "major_name", "zymc", default="")).strip()
    duration = str(pick(major, "修业年限", "duration", default="")).strip()
    degree = str(pick(major, "授予学位", "degree", default="")).strip()
    detail_url = str(pick(major, "详情页", "detail_url", "url", default="")).strip()
    introduction = str(pick(major, "专业介绍", "introduction", "简介", default="")).strip()

    return {
        "major_code": major_code,
        "major_name": major_name,
        "degree_level": degree_level,
        "discipline": discipline,
        "major_category": major_category,
        "duration": duration,
        "degree": degree,
        "detail_url": detail_url,
        "introduction": introduction
    }


def main():
    ensure_output()
    data = load_json(INPUT_FILE)

    degree_levels = pick(data, "培养层次列表", "data", default=[])
    rows = []
    seen = set()

    for level_item in degree_levels:
        degree_level = str(pick(level_item, "培养层次", "name", default="")).strip()
        discipline_list = pick(level_item, "门类列表", "items", default=[])

        for discipline_item in discipline_list:
            discipline = str(pick(discipline_item, "门类", "name", default="")).strip()
            major_category_list = pick(discipline_item, "专业类列表", "items", default=[])

            for category_item in major_category_list:
                major_category = str(pick(category_item, "专业类", "name", default="")).strip()
                major_list = pick(category_item, "专业列表", "items", default=[])

                for major in major_list:
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


if __name__ == "__main__":
    main()
