import pandas as pd
from ta.utils import dropna
import matplotlib.pyplot as plt
from ta.trend import MACD

df = pd.read_csv('TSLA.csv', sep=',')

# clean NaN
df = dropna(df)

macd = MACD(close=df["Close"])

df["macd"] = macd.macd()
df["macd_signal"] = macd.macd_signal()
df["macd_diff"] = macd.macd_diff()

#plt.plot(df.Close, label="price")
plt.plot(df.macd, label="MACD")
plt.plot(df.macd_signal, label="MACD signal")
plt.plot(df.macd_diff, label="MACD diff")
plt.title("TSLA MACD")
plt.show()

with open("TSLA_ta.csv", "w") as f:
    f.write(df.to_csv())
