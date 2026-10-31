def chunk_list(items: list, size: int) -> list[list]:
    if size <= 0:
        return []
    return [items[i:i + size] for i in range(0, len(items), size)]
