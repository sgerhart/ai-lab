def mode_single(nums: list[int]) -> int:
    from collections import Counter
    return Counter(nums).most_common(1)[0][0] if nums else 0
