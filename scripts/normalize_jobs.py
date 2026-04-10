import json
import os
import re


INPUT_FILE = "data/data.json"
OUTPUT_FILE = "output/jobs.normalized.json"


def ensure_output():
    os.makedirs("output", exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_salary_mid(s):
    if not s:
        return None

    text = str(s).strip().replace("＋", "+").replace("—", "-").replace("–", "-")
    text = text.replace("万+", "万")

    m = re.findall(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return None

    nums = [float(x) for x in m]
    if len(nums) == 1:
        return nums[0]

    return round((nums[0] + nums[1]) / 2, 2)


def normalize_one(item, idx):
    title = str(item.get("title", "")).strip()
    category = str(item.get("category", "")).strip()
    employment_workers = int(item.get("employment_workers", 0) or 0)
    exposure = int(item.get("exposure", 0) or 0)
    highlighted = bool(item.get("highlighted", False))
    avg_salary = str(item.get("avgSalary", "")).strip()
    detail = str(item.get("detail", "")).strip()
    source_url = str(item.get("source_url", "")).strip()

    salary_mid = parse_salary_mid(avg_salary)

    full_text = " ".join([
        title,
        category,
        detail,
        avg_salary
    ]).strip()

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


def main():
    ensure_output()
    data = load_json(INPUT_FILE)

    if not isinstance(data, list):
        raise ValueError("data.json 顶层应为 list")

    rows = []
    for idx, item in enumerate(data, start=1):
        row = normalize_one(item, idx)
        if not row["job_title"]:
            continue
        rows.append(row)

    rows.sort(key=lambda x: (x["category"], x["job_title"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
