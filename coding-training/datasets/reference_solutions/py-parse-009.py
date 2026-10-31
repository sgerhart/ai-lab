def csv_line_split(line: str) -> list[str]:
    import csv, io
    return next(csv.reader(io.StringIO(line))) if line else []
