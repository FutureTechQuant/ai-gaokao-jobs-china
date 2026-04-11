import json
from statistics import mean

K = 10

CONFIDENCE_FACTOR = {
    "high": 1.00,
    "medium": 0.85,
    "low": 0.70
}

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def adjusted_rate(raw_rate, job_count, confidence, global_mean, k=K):
    raw_rate = float(raw_rate or 0)
    job_count = int(job_count or 0)
    conf_factor = CONFIDENCE_FACTOR.get((confidence or "low").lower(), 0.70)

    sample_weight = job_count / (job_count + k) if job_count >= 0 else 0
    w = clamp(sample_weight * conf_factor)

    adj = raw_rate * w + global_mean * (1 - w)
    return round(clamp(adj), 4), round(w, 4)

with open("output/major_ai_rate.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

global_mean = mean(float(r.get("replace_rate", 0) or 0) for r in rows) if rows else 0.0

for r in rows:
    raw = float(r.get("replace_rate", 0) or 0)
    job_count = int(r.get("job_count", 0) or 0)
    confidence = (r.get("confidence") or "low").lower()

    adj, weight = adjusted_rate(
        raw_rate=raw,
        job_count=job_count,
        confidence=confidence,
        global_mean=global_mean,
        k=K
    )

    r["raw_replace_rate"] = round(raw, 4)
    r["adjusted_replace_rate"] = adj
    r["confidence_weight"] = weight
    r["global_mean_replace_rate"] = round(global_mean, 4)

rows.sort(
    key=lambda x: (
        float(x.get("adjusted_replace_rate", 0) or 0),
        int(x.get("job_count", 0) or 0)
    ),
    reverse=True
)

with open("output/major_ai_rate.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
