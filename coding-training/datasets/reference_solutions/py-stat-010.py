def harmonic_mean(nums: list[float]) -> float:
    if not nums or any(x <= 0 for x in nums): return 0.0
    return len(nums) / sum(1.0/x for x in nums)
