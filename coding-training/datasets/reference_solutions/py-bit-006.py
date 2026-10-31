def bitwise_and_range(m: int, n: int) -> int:
    while n > m:
        n &= n - 1
    return m & n
