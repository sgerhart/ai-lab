def day_of_week(year: int, month: int, day: int) -> str:
    import datetime
    d = datetime.date(year, month, day)
    return d.strftime('%A')
