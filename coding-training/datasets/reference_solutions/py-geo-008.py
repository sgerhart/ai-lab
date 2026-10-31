def point_in_circle(px: float, py: float, cx: float, cy: float, r: float) -> bool:
    return (px - cx)**2 + (py - cy)**2 <= r**2
