def rotate_matrix_90(mat: list[list[int]]) -> list[list[int]]:
    return [list(x) for x in zip(*mat[::-1])]
