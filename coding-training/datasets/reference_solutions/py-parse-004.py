def parse_query_params(query: str) -> dict[str, str]:
    from urllib.parse import parse_qs
    parsed = parse_qs(query.lstrip('?'))
    return {k: v[0] for k, v in parsed.items()}
