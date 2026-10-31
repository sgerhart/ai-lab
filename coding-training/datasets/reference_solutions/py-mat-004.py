def count_islands(grid: list[list[int]]) -> int:
    if not grid or not grid[0]:
        return 0
    R, C = len(grid), len(grid[0])
    visited = set()
    islands = 0
    def dfs(r, c):
        visited.add((r, c))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1 and (nr, nc) not in visited:
                dfs(nr, nc)
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 1 and (r, c) not in visited:
                dfs(r, c)
                islands += 1
    return islands
