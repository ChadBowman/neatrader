
def min_max(x, mn, mx):
    """
    recales x such that it fits in the range: [-1, 1]
    """
    return 2 * ((x - mn) / (mx - mn)) - 1


def un_min_max(x, mn, mx):
    return (((mx - mn) * (x + 1)) / 2) + mn
