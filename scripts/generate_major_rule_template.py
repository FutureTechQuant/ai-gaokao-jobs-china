import json
import os
from collections import defaultdict


INPUT_FILE = "output/majors.normalized.json"
OUTPUT_FILE = "config/major_job_rules.template.json"
SUMMARY_FILE = "output/major_rule_template_summary.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def group_majors(majors):
    category_map = defaultdict(list)
    discipline_map = defaultdict(list)
    degree_map = defaultdict(list)

    for row in majors:
        category = row.get("major_category", "").strip()
        discipline = row.get("discipline", "").strip()
        degree_level = row.get("degree_level", "").strip()

        if category:
            category_map[category].append(row)
        if discipline:
            discipline_map[discipline].append(row)
        if degree_level:
            degree_map[degree_level].append(row)

    return category_map, discipline_map, degree_map


def build_category_template(category_map):
    result = {}

    for category, rows in sorted(category_map.items(), key=lambda x: (-len(x[1]), x[0])):
        example_majors = []
        for row in rows[:8]:
            example_majors.append({
                "major_code": row.get("major_code", ""),
                "major_name": row.get("major_name", ""),
                "discipline": row.get("discipline", ""),
                "degree_level": row.get("degree_level", "")
            })

        result[category] = {
            "_meta": {
                "major_count": len(rows),
                "example_majors": example_majors,
                "note": "请填写该专业类对应的职业类别与标题关键词"
            },
            "include_categories": [],
            "include_titles": [],
            "exclude_titles": []
        }

    return result


def build_discipline_template(discipline_map):
    result = {}

    for discipline, rows in sorted(discipline_map.items(), key=lambda x: (-len(x[1]), x[0])):
        categories = sorted(list({x.get("major_category", "") for x in rows if x.get("major_category", "")}))
        example_majors = []
        for row in rows[:8]:
            example_majors.append({
                "major_code": row.get("major_code", ""),
                "major_name": row.get("major_name", ""),
                "major_category": row.get("major_category", ""),
                "degree_level": row.get("degree_level", "")
            })

        result[discipline] = {
            "_meta": {
                "major_count": len(rows),
                "major_categories": categories,
                "example_majors": example_majors,
                "note": "门类兜底规则；仅在该门类下没有专业类规则时使用"
            },
            "include_categories": [],
            "include_titles": [],
            "exclude_titles": []
        }

    return result


def build_summary(majors, category_map, discipline_map, degree_map):
    top_categories = []
    for category, rows in sorted(category_map.items(), key=lambda x: (-len(x[1]), x[0])):
        top_categories.append({
            "major_category": category,
            "major_count": len(rows),
            "sample_major_names": [x.get("major_name", "") for x in rows[:5]]
        })

    top_disciplines = []
    for discipline, rows in sorted(discipline_map.items(), key=lambda x: (-len(x[1]), x[0])):
        top_disciplines.append({
            "discipline": discipline,
            "major_count": len(rows),
            "major_categories": sorted(list({x.get("major_category", "") for x in rows if x.get("major_category", "")}))[:10]
        })

    degree_levels = []
    for degree_level, rows in sorted(degree_map.items(), key=lambda x: (-len(x[1]), x[0])):
        degree_levels.append({
            "degree_level": degree_level,
            "major_count": len(rows)
        })

    return {
        "total_majors": len(majors),
        "major_category_count": len(category_map),
        "discipline_count": len(discipline_map),
        "degree_level_count": len(degree_map),
        "top_major_categories": top_categories,
        "top_disciplines": top_disciplines,
        "degree_levels": degree_levels
    }


def main():
    os.makedirs("config", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    majors = load_json(INPUT_FILE)
    category_map, discipline_map, degree_map = group_majors(majors)

    template = {
        "_meta": {
            "description": "专业规则模板：优先 major_code_rules，其次 major_category_rules，最后 discipline_rules",
            "how_to_use": [
                "1. 先优先填写 major_category_rules，可覆盖大多数专业",
                "2. 对少量特殊专业再填写 major_code_rules",
                "3. discipline_rules 只做门类兜底"
            ]
        },
        "major_code_rules": {},
        "major_category_rules": build_category_template(category_map),
        "discipline_rules": build_discipline_template(discipline_map)
    }

    summary = build_summary(majors, category_map, discipline_map, degree_map)

    save_json(OUTPUT_FILE, template)
    save_json(SUMMARY_FILE, summary)

    print(f"已生成模板: {OUTPUT_FILE}")
    print(f"已生成摘要: {SUMMARY_FILE}")
    print(f"专业总数: {summary['total_majors']}")
    print(f"专业类数量: {summary['major_category_count']}")
    print(f"门类数量: {summary['discipline_count']}")
    print(f"培养层次数量: {summary['degree_level_count']}")


if __name__ == "__main__":
    main()
