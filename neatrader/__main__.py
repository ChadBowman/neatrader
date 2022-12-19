import os
import sys
import math
from neatrader import neatrader


if __name__ == '__main__':
    config_path = os.path.join('neatrader', 'config.ini')
    generations_per_iteration = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    iterations = int(sys.argv[2]) if len(sys.argv) > 2 else math.inf
    neatrader.run(config_path, generations_per_iteration, iterations)
