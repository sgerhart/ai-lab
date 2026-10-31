def count_parentheses_depth(s: str) -> int:
    max_d = curr = 0
    for c in s:
        if c == '(': curr += 1; max_d = max(max_d, curr)
        elif c == ')': curr = max(0, curr - 1)
    return max_d
