import re
from datetime import date


def iso_date(value):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value): raise ValueError("Invalid ISO date")
    return date.fromisoformat(value)


def utc_timestamp(value):
    m = re.fullmatch(r"([0-9]{4}-[0-9]{2}-[0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]+)?Z", value)
    if not m: raise ValueError("Invalid UTC timestamp")
    iso_date(m[1]); hour, minute, second = map(int, m.group(2, 3, 4))
    if not (hour <= 23 and minute <= 59 and second <= 60 and (second != 60 or (hour == 23 and minute == 59))):
        raise ValueError("Invalid UTC clock components")
    # Leap-second syntax accepted; this offline parser does not establish IERS announcement history.


def date_or_timestamp(value):
    if len(value) == 10: iso_date(value)
    else: utc_timestamp(value)
