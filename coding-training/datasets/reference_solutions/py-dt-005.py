def days_between(d1: str, d2: str) -> int:
    import datetime
    dt1 = datetime.date.fromisoformat(d1)
    dt2 = datetime.date.fromisoformat(d2)
    return abs((dt2 - dt1).days)
