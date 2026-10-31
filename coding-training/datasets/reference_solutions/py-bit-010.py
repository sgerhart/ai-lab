def is_bitwise_subset(sub: int, mask: int) -> bool:
    return (sub & mask) == sub
