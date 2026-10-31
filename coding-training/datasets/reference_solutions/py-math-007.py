def sum_of_digits(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))
