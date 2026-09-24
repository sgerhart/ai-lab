"""Minimal 5-field cron matcher (minute hour dom month dow).

Supports ``*``, ``N``, ``A-B``, ``*/N``, and comma lists. Host local time.
Not a full cron implementation — enough for personal-lab schedules (FEAT-009).
"""

from __future__ import annotations

from datetime import datetime


class CronError(ValueError):
    """Invalid cron expression."""


def _parse_field(field: str, minimum: int, maximum: int) -> set[int]:
    field = field.strip()
    if not field:
        raise CronError("empty cron field")
    values: set[int] = set()
    for part in field.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(minimum, maximum + 1))
            continue
        if part.startswith("*/"):
            step = int(part[2:])
            if step < 1:
                raise CronError(f"invalid step: {part}")
            values.update(range(minimum, maximum + 1, step))
            continue
        if "-" in part:
            a_s, b_s = part.split("-", 1)
            a, b = int(a_s), int(b_s)
            if a > b or a < minimum or b > maximum:
                raise CronError(f"invalid range: {part}")
            values.update(range(a, b + 1))
            continue
        n = int(part)
        if n < minimum or n > maximum:
            raise CronError(f"out of range: {part}")
        values.add(n)
    return values


def parse_cron(expr: str) -> tuple[set[int], set[int], set[int], set[int], set[int]]:
    parts = expr.strip().split()
    if len(parts) != 5:
        raise CronError("expected 5 fields: minute hour dom month dow")
    minute, hour, dom, month, dow = parts
    return (
        _parse_field(minute, 0, 59),
        _parse_field(hour, 0, 23),
        _parse_field(dom, 1, 31),
        _parse_field(month, 1, 12),
        _parse_field(dow, 0, 6),  # 0 = Sunday
    )


def cron_matches(expr: str, when: datetime | None = None) -> bool:
    """Return True if ``expr`` matches ``when`` (local time; default now)."""
    when = when or datetime.now().astimezone()
    minutes, hours, doms, months, dows = parse_cron(expr)
    # Python: Monday=0 … Sunday=6; cron: Sunday=0 … Saturday=6
    cron_dow = (when.weekday() + 1) % 7
    return (
        when.minute in minutes
        and when.hour in hours
        and when.day in doms
        and when.month in months
        and cron_dow in dows
    )


__all__ = ["CronError", "cron_matches", "parse_cron"]
