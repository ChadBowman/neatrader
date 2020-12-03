def flatten_dict(d):
    for v in d.values():
        if isinstance(v, dict):
            yield from flatten_dict(v)
        else:
            yield v
