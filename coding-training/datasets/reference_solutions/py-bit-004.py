def single_number(nums: list[int]) -> int:
    res = 0
    for x in nums:
        res ^= x
    return res
