def days_in_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]
