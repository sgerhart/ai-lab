def count_vowels(s: str) -> int:
    vowels = set('aeiouAEIOU')
    return sum(1 for c in s if c in vowels)
