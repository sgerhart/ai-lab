def slope(p1: list[float], p2: list[float]) -> float | None:
    if p1[0] == p2[0]: return None
    return (p2[1] - p1[1]) / (p2[0] - p1[0])
