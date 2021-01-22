from datetime import datetime


def flatten_dict(d):
    for v in d.values():
        if isinstance(v, dict):
            yield from flatten_dict(v)
        else:
            yield v


def small_date(date):
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    return date.strftime('%y%m%d')


def from_small_date(string):
    return datetime.strptime(string, '%y%m%d')


def add_value(dic, key, val):
    if dic.get(key, None):
        dic[key].append(val)
    else:
        dic[key] = [val]


def days_between(start, end):
    """
    Returns the number of days between two dates. End date is exclusive.
    Example: will return 31 when start=2021-01-01 and end=20201-02-01
    """
    return divmod((end-start).total_seconds(), 86400)[0]
