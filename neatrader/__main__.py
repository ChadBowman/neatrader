import os
import sys
from neatrader import neatrader


if __name__ == '__main__':
    config_path = os.path.join('neatrader', 'config.ini')
    generations_per_iteration = int(sys.argv[1]) if len(sys.argv) == 2 else 3
    neatrader.run(config_path, generations_per_iteration)
