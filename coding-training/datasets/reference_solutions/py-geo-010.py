def rectangles_overlap(r1: list[int], r2: list[int]) -> bool:
    return not (r1[2] <= r2[0] or r2[2] <= r1[0] or r1[3] <= r2[1] or r2[3] <= r1[1])
