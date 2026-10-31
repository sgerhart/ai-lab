def z_score(val: float, m: float, s: float) -> float:
    return (val - m) / s if s != 0 else 0.0
