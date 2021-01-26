import os
from random import random
from pathlib import Path
from neatrader.model import Security

TSLA = Security('TSLA')


def fetch_resource(resource_name=None):
    local_dir = os.path.dirname(__file__)
    if not resource_name:
        return local_dir
    return os.path.join(local_dir, resource_name)


def test_path(resource_name=None):
    return Path(fetch_resource(resource_name))


class BuyAndHoldNet:
    def activate(self, params):
        return (0, 0, 1, 0, 0)


class AlwaysSellNet:
    def activate(self, params):
        return (0, 1, 0, self.delta, self.theta)


class SellOnceNet:
    def __init__(self):
        self.sold = False

    def activate(self, params):
        if self.sold:
            return (0, 0, 1, 0, 0)  # hold
        else:
            self.sold = True
            return (0, 1, 0, self.delta, self.theta)


class RandomNet:
    def __init__(self, outputs):
        self.outputs = outputs

    def r(self):
        return (2 * random()) - 1

    def activate(self, params):
        result = []
        for _ in range(self.outputs):
            result.append((2 * random()) - 1)
        return tuple(result)
