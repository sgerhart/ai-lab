def rotate_array(nums: list[int], k: int) -> list[int]:
    if not nums:
        return []
    k = k % len(nums)
    if k == 0:
        return list(nums)
    return nums[-k:] + nums[:-k]
