def triangle_perimeter(a: float, b: float, c: float) -> float:
    return a + b + c if (a+b>c and a+c>b and b+c>a) else 0.0
