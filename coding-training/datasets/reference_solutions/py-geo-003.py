def is_point_on_segment(px: int, py: int, x1: int, y1: int, x2: int, y2: int) -> bool:
    c = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if c != 0: return False
    return min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2)
