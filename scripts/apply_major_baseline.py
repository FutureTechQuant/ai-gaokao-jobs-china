import json
import os

INPUT_FILE = "output/major_ai_rate.json"
BASELINE_FILE = "config/major_baseline_rules.json"
OUTPUT_FILE = "output/major_ai_rate.json"
SUMMARY_FILE = "output/major_ai_rate.baseline.summary.json"


def load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def to_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def match_rule(row, rule):
    cond = rule.get("when", {})

    major_name = row.get("major_name", "") or ""
    major_category = row.get("major_category", "") or row.get("category", "") or ""
    discipline = row.get("discipline", "") or ""

    name_contains = cond.get("major_name_contains", [])
    if name_contains and not any(x in major_name for x in name_contains):
        return False

    category_in = cond.get("major_category_in", [])
    if category_in and major_category not in category_in:
        return False

    discipline_in = cond.get("discipline_in", [])
    if discipline_in and discipline not in discipline_in:
        return False

    return True


def get_baseline(row, rules):
    best = 0.0
    hit = []
    for rule in rules:
        if match_rule(row, rule):
            val = to_float(rule.get("min_replace_rate", 0))
            if val > best:
                best = val
            hit.append(rule.get("name", ""))
    return best, hit


def main():
    rows = load_json(INPUT_FILE, [])
    baseline_rules = load_json(BASELINE_FILE, {}).get("baseline_rules", [])

    changed = 0
    raw_zero_lifted = 0

    for row in rows:
        old_rate = to_float(row.get("replace_rate", 0))
        baseline_rate, baseline_rules_hit = get_baseline(row, baseline_rules)

        row["raw_replace_rate"] = old_rate
        row["baseline_replace_rate"] = baseline_rate
        row["baseline_rules_hit"] = baseline_rules_hit

        new_rate = max(old_rate, baseline_rate)
        row["replace_rate"] = round(new_rate, 4)

        if new_rate > old_rate:
            changed += 1
        if old_rate == 0 and new_rate > 0:
            raw_zero_lifted += 1

    rows.sort(key=lambda x: (-to_float(x.get("replace_rate", 0)), x.get("major_code", "")))

    summary = {
        "input_file": INPUT_FILE,
        "total_rows": len(rows),
        "baseline_changed_rows": changed,
        "raw_zero_lifted_rows": raw_zero_lifted,
        "examples": [x for x in rows if to_float(x.get("baseline_replace_rate", 0)) > 0][:30]
    }

    save_json(OUTPUT_FILE, rows)
    save_json(SUMMARY_FILE, summary)

    print(f"baseline changed rows: {changed}")
    print(f"raw zero lifted rows: {raw_zero_lifted}")
    print(f"output: {OUTPUT_FILE}")
    print(f"summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()