import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from neatrader.preprocess import CsvImporter
from neatrader.model import Security
from datetime import datetime

raw = pd.read_csv('data/TSLA/chains/200207.csv')

importer = CsvImporter()
tsla = Security('TSLA')
chain = importer.parse_chain(datetime(2020, 9, 11), tsla, Path('normalized/TSLA/chains/200911.csv'))

# 372.72
exp = chain._expirations_by_price_weighted_theta('call', 372.72)
e = []
t = []
for expiration, theta in exp.items():
    e.append(expiration)
    t.append(theta)
df = pd.DataFrame.from_dict({'expiration': e, 'theta': t})

plt.close('all')
df.plot(x='expiration', y='theta')
plt.show()
