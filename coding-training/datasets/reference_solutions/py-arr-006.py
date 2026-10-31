def find_missing_number(nums: list[int]) -> int:
    n = len(nums)
    expected = n * (n + 1) // 2
    return expected - sum(nums)
