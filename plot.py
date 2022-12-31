import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from neatrader.model import Security
from neatrader.preprocess import CsvImporter
from neatrader.utils import daterange
from pathlib import Path

importer = CsvImporter()
path_str = "resources/data/TSLA/chains/200207.csv"
tsla = Security("TSLA")

raw = pd.read_csv(path_str)

chain = importer.parse_chain(datetime(2020, 2, 4), tsla, Path(path_str))

# 372.72
exp = {date: chain.iv(date, 372.72) for date in daterange(datetime(2021, 1, 1), datetime(2022, 3, 18))}

e = []
t = []
for expiration, theta in exp.items():
    if theta:
        e.append(expiration)
        t.append(theta)

df = pd.DataFrame.from_dict({"expiration": e, "theta": t})

plt.close("all")
df.plot(x="expiration", y="theta")
plt.show()
