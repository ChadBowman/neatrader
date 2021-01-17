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
