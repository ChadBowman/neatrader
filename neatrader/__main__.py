import os
from neatrader import neatrader


if __name__ == '__main__':
    config_path = os.path.join('neatrader', 'config.ini')
    neatrader.run(config_path)
