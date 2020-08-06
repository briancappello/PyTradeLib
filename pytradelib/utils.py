from datetime import datetime, timezone


def utcnow():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def chunk(string, size):
    for i in range(0, len(string), size):
        yield string[i:i+size]


def percent_change(from_val, to_val):
    # coerce to float to ensure non-integer division
    return (float(to_val - from_val) / from_val) * 100


def within_percent_of_value(price, value, percent=1):
    diff = percent * 0.01 * 0.5 * value
    return (value - diff) < price < (value + diff)
