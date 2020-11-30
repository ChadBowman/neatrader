import os


def fetch_resource(resource_name):
    local_dir = os.path.dirname(__file__)
    return os.path.join(local_dir, resource_name)
