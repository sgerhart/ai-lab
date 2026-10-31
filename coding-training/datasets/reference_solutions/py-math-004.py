def lcm(a: int, b: int) -> int:
    import math
    return (a * b) // math.gcd(a, b) if a and b else 0
