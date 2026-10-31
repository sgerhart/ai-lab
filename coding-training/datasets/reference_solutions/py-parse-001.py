def parse_key_values(s: str) -> dict[str, str]:
    res = {}
    for pair in s.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            res[k.strip()] = v.strip()
    return res
