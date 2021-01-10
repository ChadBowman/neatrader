import os
from neatrader import neatrader

config_path = os.path.join('neatrader', 'config.ini')
neatrader.run(config_path)
