def mask_credit_card(card: str) -> str:
    digits = [c for c in card if c.isdigit()]
    if len(digits) < 4: return ''
    return '*' * (len(digits) - 4) + ''.join(digits[-4:])
