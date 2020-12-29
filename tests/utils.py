import os
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
