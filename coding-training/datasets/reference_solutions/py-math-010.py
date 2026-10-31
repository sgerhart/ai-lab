def is_perfect_square(n: int) -> bool:
    if n < 0:
        return False
    r = int(n ** 0.5)
    return r * r == n
