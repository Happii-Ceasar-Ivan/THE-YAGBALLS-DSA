def compute_stats(scores: List[float]) -> Dict[str, float]:
    clean_scores = [s for s in scores if s is not None]
    n = len(clean_scores)
    if n == 0:
        return {"count": 0, "mean": 0, "median": 0, "min": 0, "max": 0, "std_dev": 0}
    sorted_scores = sorted(clean_scores)
    mean = sum(sorted_scores) / n
    median = sorted_scores[n // 2] if n % 2 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
    variance = sum((x - mean) ** 2 for x in sorted_scores) / n
    std_dev = math.sqrt(variance)
    return {
        "count": n,
        "mean": mean,
        "median": median,
        "min": min(sorted_scores),
        "max": max(sorted_scores),
        "std_dev": std_dev
    }

def compute_percentile(scores: List[float], percentile: float) -> float:
    clean_scores = sorted([s for s in scores if s is not None])
    if not clean_scores:
        return 0
    k = (len(clean_scores) - 1) * (percentile / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return clean_scores[int(k)]
    return clean_scores[f] + (clean_scores[c] - clean_scores[f]) * (k - f)

def detect_outliers(scores: List[float]) -> List[float]:
    if len(scores) < 4:
        return []
    q1 = compute_percentile(scores, 25)
    q3 = compute_percentile(scores, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [s for s in scores if s < lower or s > upper]

def analyze_section(students: List[Dict], section: str) -> Dict:
    scores = [s["final_score"] for s in students if s["section"] == section]
    stats = compute_stats(scores)
    outliers = detect_outliers(scores)
    return {**stats, "section": section, "outliers": outliers}