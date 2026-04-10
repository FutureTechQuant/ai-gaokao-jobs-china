import json
import os
import re
from collections import defaultdict, Counter

ALL_JSON = "data/all.json"
JOBS_JSON = "data/data.json"

OUT_JOB_TITLES = "output/all_job_titles.json"
OUT_MAJOR_DIRECTIONS = "output/major_employment_directions.json"
OUT_RULES = "output/major_job_rules.auto.json"
OUT_SUMMARY = "output/major_job_rules.auto.summary.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pick(d, *keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def normalize_text(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s


def walk_majors(all_data):
    degree_levels = pick(all_data, "培养层次列表", default=[])
    for level_item in degree_levels:
        degree_level = str(pick(level_item, "培养层次", "name", default="")).strip()
        discipline_list = pick(level_item, "门类列表", default=[])

        for discipline_item in discipline_list:
            discipline = str(pick(discipline_item, "门类", "name", default="")).strip()
            category_list = pick(discipline_item, "专业类列表", default=[])

            for category_item in category_list:
                major_category = str(pick(category_item, "专业类", "name", default="")).strip()
                major_list = pick(category_item, "专业列表", default=[])

                for major in major_list:
                    yield {
                        "major_code": str(pick(major, "专业代码", "code", "major_code", "zydm", default="")).strip(),
                        "major_name": str(pick(major, "专业名称", "name", "major_name", "zymc", default="")).strip(),
                        "degree_level": degree_level,
                        "discipline": discipline,
                        "major_category": major_category,
                        "employment_direction_raw": extract_employment_text(major)
                    }


def extract_employment_text(major):
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
                return str(raw)
            if isinstance(arr, list) and arr:
                return "".join([str(x) for x in arr if x])
        elif isinstance(c, str) and c.strip():
            return c
    return ""


def build_job_catalog(job_data):
    alias_map = {
        "内容创作者/编辑": ["编辑", "内容编辑", "文案", "新媒体编辑", "内容创作者"],
        "新闻记者": ["记者", "新闻记者", "采编"],
        "平面设计师": ["平面设计", "视觉设计", "美工", "设计师"],
        "数据分析师": ["数据分析", "分析师", "商业分析"],
        "测试工程师": ["测试工程师", "软件测试", "测试"],
        "软件工程师": ["软件工程师", "开发工程师", "程序员", "后端", "前端"],
        "会计与出纳": ["会计", "出纳", "财务"],
        "银行柜员": ["柜员", "银行柜员"],
        "证券分析师": ["证券分析师", "投研", "研究员"],
        "高中教师": ["高中教师", "高中老师", "中学教师"],
        "初中教师": ["初中教师", "初中老师"],
        "大学教师": ["大学教师", "高校教师", "讲师", "教授"],
        "行政专员/助理": ["行政", "行政专员", "行政助理", "助理"],
        "公务员": ["公务员", "选调生", "事业单位人员", "事业单位"],
        "私营企业主": ["企业主", "创业", "创业者", "老板", "私营企业主"]
    }

    all_titles = []
    title_to_category = {}
    title_aliases = {}

    for item in job_data:
        title = str(item.get("title", "")).strip()
        category = str(item.get("category", "")).strip()
        if not title:
            continue
        all_titles.append({
            "title": title,
            "category": category
        })
        title_to_category[title] = category
        title_aliases[title] = list(set([title] + alias_map.get(title, [])))

    return all_titles, title_to_category, title_aliases


def extract_direction_tokens(raw_text, title_aliases):
    text = normalize_text(raw_text)
    if not text:
        return []

    matched = []
    used_spans = []

    alias_items = []
    for title, aliases in title_aliases.items():
        for alias in aliases:
            alias_norm = normalize_text(alias)
            if alias_norm:
                alias_items.append((title, alias, alias_norm))

    alias_items.sort(key=lambda x: len(x[2]), reverse=True)

    for std_title, alias, alias_norm in alias_items:
        start = 0
        while True:
            idx = text.find(alias_norm, start)
            if idx == -1:
                break
            end = idx + len(alias_norm)
            overlap = False
            for s, e in used_spans:
                if not (end <= s or idx >= e):
                    overlap = True
                    break
            if not overlap:
                matched.append({
                    "standard_title": std_title,
                    "matched_alias": alias
                })
                used_spans.append((idx, end))
            start = idx + 1

    uniq = []
    seen = set()
    for x in matched:
        key = (x["standard_title"], x["matched_alias"])
        if key not in seen:
            seen.add(key)
            uniq.append(x)
    return uniq


def build_major_code_rules(major_rows, title_to_category, title_aliases):
    rules = {}
    extracted_rows = []
    unmapped = []

    for row in major_rows:
        code = row["major_code"]
        name = row["major_name"]
        raw = row["employment_direction_raw"]

        tokens = extract_direction_tokens(raw, title_aliases)
        titles = sorted(list({x["standard_title"] for x in tokens}))
        categories = sorted(list({title_to_category.get(t, "") for t in titles if title_to_category.get(t, "")}))

        extracted_rows.append({
            "major_code": code,
            "major_name": name,
            "degree_level": row["degree_level"],
            "discipline": row["discipline"],
            "major_category": row["major_category"],
            "employment_direction_raw": raw,
            "matched_titles": titles,
            "matched_details": tokens
        })

        if titles or categories:
            rules[code] = {
                "include_categories": categories,
                "include_titles": titles,
                "exclude_titles": []
            }
        else:
            unmapped.append({
                "major_code": code,
                "major_name": name,
                "major_category": row["major_category"],
                "discipline": row["discipline"],
                "employment_direction_raw": raw
            })

    return rules, extracted_rows, unmapped


def build_major_category_rules(major_rows, major_code_rules):
    bucket = defaultdict(lambda: {
        "categories": Counter(),
        "titles": Counter(),
        "major_codes": [],
        "examples": []
    })

    code_to_major = {x["major_code"]: x for x in major_rows}

    for code, rule in major_code_rules.items():
        major = code_to_major.get(code)
        if not major:
            continue
        cat = major["major_category"]
        b = bucket[cat]

        for c in rule.get("include_categories", []):
            b["categories"][c] += 1
        for t in rule.get("include_titles", []):
            b["titles"][t] += 1

        b["major_codes"].append(code)
        if len(b["examples"]) < 8:
            b["examples"].append({
                "major_code": code,
                "major_name": major["major_name"]
            })

    out = {}
    for major_category, b in bucket.items():
        include_categories = [k for k, v in b["categories"].most_common(8) if v >= 2]
        include_titles = [k for k, v in b["titles"].most_common(12) if v >= 2]

        out[major_category] = {
            "_meta": {
                "derived_from_major_count": len(b["major_codes"]),
                "examples": b["examples"]
            },
            "include_categories": include_categories,
            "include_titles": include_titles,
            "exclude_titles": []
        }

    return out


def build_discipline_rules(major_rows, major_category_rules):
    category_to_discipline = defaultdict(Counter)
    for row in major_rows:
        if row["major_category"] and row["discipline"]:
            category_to_discipline[row["discipline"]][row["major_category"]] += 1

    out = {}
    for discipline, counter in category_to_discipline.items():
        agg_categories = Counter()
        agg_titles = Counter()

        top_major_categories = [k for k, _ in counter.most_common(10)]
        for mc in top_major_categories:
            rule = major_category_rules.get(mc)
            if not rule:
                continue
            for c in rule.get("include_categories", []):
                agg_categories[c] += 1
            for t in rule.get("include_titles", []):
                agg_titles[t] += 1

        out[discipline] = {
            "_meta": {
                "derived_from_major_categories": top_major_categories
            },
            "include_categories": [k for k, v in agg_categories.most_common(8) if v >= 1],
            "include_titles": [k for k, v in agg_titles.most_common(12) if v >= 1],
            "exclude_titles": []
        }

    return out


def main():
    all_data = load_json(ALL_JSON)
    job_data = load_json(JOBS_JSON)

    major_rows = [x for x in walk_majors(all_data) if x["major_code"] and x["major_name"]]
    all_titles, title_to_category, title_aliases = build_job_catalog(job_data)

    major_code_rules, extracted_rows, unmapped = build_major_code_rules(
        major_rows, title_to_category, title_aliases
    )
    major_category_rules = build_major_category_rules(major_rows, major_code_rules)
    discipline_rules = build_discipline_rules(major_rows, major_category_rules)

    rules = {
        "_meta": {
            "description": "由已毕业人员从业方向自动生成",
            "note": "建议人工复核 exclude_titles 与少量误匹配"
        },
        "major_code_rules": major_code_rules,
        "major_category_rules": major_category_rules,
        "discipline_rules": discipline_rules
    }

    summary = {
        "major_total": len(major_rows),
        "job_title_total": len(all_titles),
        "major_code_rules_generated": len(major_code_rules),
        "major_category_rules_generated": len(major_category_rules),
        "discipline_rules_generated": len(discipline_rules),
        "unmapped_major_count": len(unmapped),
        "unmapped_examples": unmapped[:50]
    }

    save_json(OUT_JOB_TITLES, {
        "job_titles": all_titles,
        "title_aliases": title_aliases
    })
    save_json(OUT_MAJOR_DIRECTIONS, extracted_rows)
    save_json(OUT_RULES, rules)
    save_json(OUT_SUMMARY, summary)

    print("已生成:")
    print("-", OUT_JOB_TITLES)
    print("-", OUT_MAJOR_DIRECTIONS)
    print("-", OUT_RULES)
    print("-", OUT_SUMMARY)


if __name__ == "__main__":
    main()
