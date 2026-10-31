def std_dev(nums: list[float]) -> float:
    if len(nums) <= 1: return 0.0
    m = sum(nums) / len(nums)
    return (sum((x - m)**2 for x in nums) / len(nums)) ** 0.5
