def flatten_list(nested: list) -> list:
    res = []
    for item in nested:
        if isinstance(item, list):
            res.extend(flatten_list(item))
        else:
            res.append(item)
    return res
