def is_valid_ipv4(ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4: return False
    for p in parts:
        if not p.isdigit() or (len(p) > 1 and p[0] == '0') or not (0 <= int(p) <= 255): return False
    return True
