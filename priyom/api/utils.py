from datetime import datetime, timedelta

__all__ = ["parse_isodate_full",
           "parse_datetime"]

datetime_formats = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%MZ",
    "%Y-%m-%dT%H:%M",
]

def parse_isodate_full(s):
    if s.endswith("Z"):
        s = s[:-1]
    date, sep, milliseconds = s.rpartition(".")
    if sep is not None:
        fracseconds = float(sep+milliseconds)
    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    return date.replace(
        microsecond=int(fracseconds*1000000))

def parse_datetime(s):
    if isinstance(s, datetime):
        return s
    # format with milliseconds
    try:
        return parse_isodate_full(s)
    except ValueError:
        pass

    for fmt in datetime_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    else:
        raise ValueError("Not a valid UTC timestamp".format(s))
