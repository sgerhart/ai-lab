def remove_duplicates(items: list) -> list:
    seen = set()
    res = []
    for x in items:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res
