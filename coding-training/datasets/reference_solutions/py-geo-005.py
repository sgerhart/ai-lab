def is_square_coords(p1: list[int], p2: list[int], p3: list[int], p4: list[int]) -> bool:
    pts = [p1, p2, p3, p4]
    dists = sorted((pts[i][0]-pts[j][0])**2 + (pts[i][1]-pts[j][1])**2 for i in range(4) for j in range(i+1, 4))
    return len(set(dists[:4])) == 1 and dists[0] > 0 and len(set(dists[4:])) == 1 and dists[4] == 2 * dists[0]
