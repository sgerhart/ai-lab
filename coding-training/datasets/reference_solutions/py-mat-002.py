def diagonal_sum(mat: list[list[int]]) -> int:
    n = len(mat)
    total = 0
    for i in range(n):
        total += mat[i][i]
        if i != n - 1 - i:
            total += mat[i][n - 1 - i]
    return total
