import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from neatrader.preprocess.normalizer import min_max
from pathlib import Path

raw = pd.read_csv('data/TSLA/chains/200207.csv')

plt.close('all')
raw = raw[raw['direction'] == 'put']
raw = raw[['expiration', 'theta']].replace(-9999999.0, np.nan)
raw = raw[raw['expiration'] < 205000]
raw.sort_values('expiration').plot.scatter(x='expiration', y='theta')
plt.show()
