def swap_odd_even_bits(n: int) -> int:
    return ((n & 0xAAAAAAAA) >> 1) | ((n & 0x55555555) << 1)
