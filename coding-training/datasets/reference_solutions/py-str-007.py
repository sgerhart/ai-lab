def are_anagrams(s1: str, s2: str) -> bool:
    from collections import Counter
    c1 = Counter(c.lower() for c in s1 if c.isalnum())
    c2 = Counter(c.lower() for c in s2 if c.isalnum())
    return c1 == c2
