def word_frequency(text: str) -> dict[str, int]:
    import re
    from collections import Counter
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    return dict(Counter(words))
