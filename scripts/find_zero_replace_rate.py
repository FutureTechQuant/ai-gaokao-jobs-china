import json
import csv
import os

INPUT_FILE = "output/major_ai_rate.json"

OUTPUT_ALL_JSON = "output/major_ai_rate.zero.all.json"
OUTPUT_ALL_CSV = "output/major_ai_rate.zero.all.csv"

OUTPUT_NO_JOB_JSON = "output/major_ai_rate.zero.no_job_match.json"
OUTPUT_NO_JOB_CSV = "output/major_ai_rate.zero.no_job_match.csv"

OUTPUT_ZERO_WITH_JOB_JSON = "output/major_ai_rate.zero.with_job_but_zero.json"
OUTPUT_ZERO_WITH_JOB_CSV = "output/major_ai_rate.zero.with_job_but_zero.csv"

OUTPUT_SUMMARY_JSON = "output/major_ai_rate.zero.summary.json"


def ensure_output():
    os.makedirs("output", exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(path, rows):
    fieldnames = [
        "major_code",
        "major_name",
        "degree_level",
        "discipline",
        "major_category",
        "replace_rate",
        "job_count",
        "confidence",
        "zero_reason",
        "matched_job_titles_sample"
    ]

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            row = dict(row)
            row["matched_job_titles_sample"] = " | ".join(row.get("matched_job_titles_sample", []))
            writer.writerow(row)


def to_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def normalize_row(row):
    replace_rate = to_float(row.get("replace_rate", 0))
    job_count = to_int(row.get("job_count", 0))

    if replace_rate != 0:
        return None

    if job_count == 0:
        zero_reason = "no_job_match"
    else:
        zero_reason = "with_job_but_zero"

    return {
        "major_code": row.get("major_code", ""),
        "major_name": row.get("major_name", ""),
        "degree_level": row.get("degree_level", ""),
        "discipline": row.get("discipline", ""),
        "major_category": row.get("major_category", ""),
        "replace_rate": replace_rate,
        "job_count": job_count,
        "confidence": row.get("confidence", ""),
        "zero_reason": zero_reason,
        "matched_job_titles_sample": row.get("matched_job_titles_sample", [])
    }


def main():
    ensure_output()
    data = load_json(INPUT_FILE)

    zero_all = []
    zero_no_job = []
    zero_with_job = []

    for row in data:
        item = normalize_row(row)
        if not item:
            continue

        zero_all.append(item)

        if item["zero_reason"] == "no_job_match":
            zero_no_job.append(item)
        else:
            zero_with_job.append(item)

    zero_all.sort(key=lambda x: (x["job_count"], x["major_code"]))
    zero_no_job.sort(key=lambda x: (x["major_code"]))
    zero_with_job.sort(key=lambda x: (x["job_count"], x["major_code"]))

    save_json(OUTPUT_ALL_JSON, zero_all)
    save_csv(OUTPUT_ALL_CSV, zero_all)

    save_json(OUTPUT_NO_JOB_JSON, zero_no_job)
    save_csv(OUTPUT_NO_JOB_CSV, zero_no_job)

    save_json(OUTPUT_ZERO_WITH_JOB_JSON, zero_with_job)
    save_csv(OUTPUT_ZERO_WITH_JOB_CSV, zero_with_job)

    summary = {
        "input_file": INPUT_FILE,
        "zero_replace_rate_total": len(zero_all),
        "zero_replace_rate_no_job_match": len(zero_no_job),
        "zero_replace_rate_with_job_but_zero": len(zero_with_job),
        "examples_no_job_match": zero_no_job[:20],
        "examples_with_job_but_zero": zero_with_job[:20]
    }

    save_json(OUTPUT_SUMMARY_JSON, summary)

    print(f"zero total: {len(zero_all)}")
    print(f"no_job_match: {len(zero_no_job)}")
    print(f"with_job_but_zero: {len(zero_with_job)}")
    print(f"summary: {OUTPUT_SUMMARY_JSON}")


if __name__ == "__main__":
    main()