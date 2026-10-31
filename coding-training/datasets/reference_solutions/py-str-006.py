def truncate_words(s: str, n: int) -> str:
    words = s.split()
    if len(words) <= n:
        return ' '.join(words)
    return ' '.join(words[:n]) + '...'
