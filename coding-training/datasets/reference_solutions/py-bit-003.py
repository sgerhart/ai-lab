def reverse_bits_16(n: int) -> int:
    b = f'{n:016b}'
    return int(b[::-1], 2)
