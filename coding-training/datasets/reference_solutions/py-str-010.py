def rot13(s: str) -> str:
    import codecs
    return codecs.encode(s, 'rot_13')
