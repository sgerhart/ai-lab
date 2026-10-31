def run_length_encode(s: str) -> str:
    if not s:
        return ''
    res = []
    curr = s[0]
    count = 1
    for c in s[1:]:
        if c == curr:
            count += 1
        else:
            res.append(f'{curr}{count}')
            curr = c
            count = 1
    res.append(f'{curr}{count}')
    return ''.join(res)
