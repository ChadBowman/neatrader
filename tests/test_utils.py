import os


def fetch_resource(resource_name=None):
    local_dir = os.path.dirname(__file__)
    if not resource_name:
        return local_dir
    return os.path.join(local_dir, resource_name)
