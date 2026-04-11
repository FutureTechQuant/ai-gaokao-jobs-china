import json
import os
from statistics import mean


INPUT_FILE = "output/major_ai_rate.json"
OUTPUT_FILE = "output/major_ai_rate.json"

K = 10

CONFIDENCE_FACTOR = {
    "high": 1.00,
    "medium": 0.85,
    "low": 0.70
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def get_raw_rate(row):
    if row.get("raw_replace_rate") is not None:
        return float(row.get("raw_replace_rate") or 0)
    return float(row.get("replace_rate") or 0)


def get_confidence(row):
    return str(row.get("confidence") or "low").lower()


def get_job_count(row):
    return int(row.get("job_count") or 0)


def compute_adjusted_rate(raw_rate, job_count, confidence, global_mean, k=K):
    raw_rate = float(raw_rate or 0)
    job_count = int(job_count or 0)
    confidence = (confidence or "low").lower()

    conf_factor = CONFIDENCE_FACTOR.get(confidence, 0.70)
    sample_weight = job_count / (job_count + k) if job_count >= 0 else 0.0
    shrink_weight = clamp(sample_weight * conf_factor)

    adjusted = raw_rate * shrink_weight + global_mean * (1 - shrink_weight)
    return round(clamp(adjusted), 4), round(shrink_weight, 4)


def main():
    rows = load_json(INPUT_FILE)

    if not rows:
        save_json(OUTPUT_FILE, rows)
        print(f"recomputed: {OUTPUT_FILE} (empty)")
        return

    for row in rows:
        row["raw_replace_rate"] = round(get_raw_rate(row), 4)

    global_mean = mean(row["raw_replace_rate"] for row in rows)

    for row in rows:
        adjusted_rate, confidence_weight = compute_adjusted_rate(
            raw_rate=row["raw_replace_rate"],
            job_count=get_job_count(row),
            confidence=get_confidence(row),
            global_mean=global_mean,
            k=K
        )

        row["adjusted_replace_rate"] = adjusted_rate
        row["confidence_weight"] = confidence_weight
        row["global_mean_replace_rate"] = round(global_mean, 4)

    rows.sort(
        key=lambda x: (
            -float(x.get("adjusted_replace_rate", 0) or 0),
            -int(x.get("job_count", 0) or 0),
            x.get("major_code", "")
        )
    )

    save_json(OUTPUT_FILE, rows)
    print(f"recomputed: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()