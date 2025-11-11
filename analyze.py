def compute_stats(scores: List[float]) -> Dict[str, float]:
    """
    Computes statistical measures using NumPy for speed.
    """
    # Convert scores to a NumPy array, filtering out None values
    clean_scores = np.array([s for s in scores if s is not None], dtype=np.float64)
    n = len(clean_scores)
    
    if n == 0:
        return {"count": 0, "mean": 0, "median": 0, "min": 0, "max": 0, "std_dev": 0}
    
    # Use NumPy's highly optimized functions
    mean = np.mean(clean_scores)
    
    # NumPy's percentile(50) is the median
    median = np.percentile(clean_scores, 50) 
    
    # np.std defaults to the population standard deviation (divisor N), matching the original logic
    std_dev = np.std(clean_scores)
    
    return {
        "count": n,
        "mean": float(mean),
        "median": float(median),
        "min": float(np.min(clean_scores)),
        "max": float(np.max(clean_scores)),
        "std_dev": float(std_dev)
    }

def compute_percentile(scores: List[float], percentile: float) -> float:
    """
    Computes a percentile using NumPy's interpolation method.
    """
    clean_scores = [s for s in scores if s is not None]
    if not clean_scores:
        return 0
        
    # Use NumPy's built-in percentile function
    return float(np.percentile(clean_scores, percentile))

def detect_outliers(scores: List[float]) -> List[float]:
    """
    Detects outliers based on the 1.5 * IQR rule, utilizing NumPy for quartile calculation.
    """
    clean_scores = [s for s in scores if s is not None]
    if len(clean_scores) < 4:
        return []
    
    scores_array = np.array(clean_scores, dtype=np.float64)
    
    # Calculate quartiles using NumPy
    q1 = np.percentile(scores_array, 25)
    q3 = np.percentile(scores_array, 75)
    
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    
    return [s for s in clean_scores if s < lower or s > upper]

def analyze_section(students: List[Dict], section: str) -> Dict:
    """
    Analyzes a specific section, maintaining compatibility with the rest of the system.
    """
    # The final_score data types are typically floats, suitable for NumPy
    scores = [s.get("final_score") for s in students if s.get("section") == section]
    stats = compute_stats(scores)
    outliers = detect_outliers(scores)
    return {**stats, "section": section, "outliers": outliers}