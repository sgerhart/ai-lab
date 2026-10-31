def percentile_rank(nums: list[float], val: float) -> float:
    if not nums: return 0.0
    return (sum(1 for x in nums if x <= val) / len(nums)) * 100.0
