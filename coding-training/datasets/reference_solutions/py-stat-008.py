def interquartile_range(nums: list[float]) -> float:
    if len(nums) < 4: return 0.0
    s = sorted(nums)
    mid = len(s) // 2
    q1 = s[mid//2] if (mid%2==1) else (s[mid//2-1]+s[mid//2])/2.0
    upper = s[mid:] if len(s)%2==0 else s[mid+1:]
    q3 = upper[len(upper)//2] if (len(upper)%2==1) else (upper[len(upper)//2-1]+upper[len(upper)//2])/2.0
    return q3 - q1
