def tokenize_simple(expr: str) -> list[str]:
    import re
    return re.findall(r'\d+|[+*/()-]', expr)
