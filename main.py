from plot import *
import pandas as pd
import numpy as np
from supply_demand_zones import *

df = pd.read_pickle("gdax_onehour_30days.pkl")
df = df.dropna()

df.index.name = 'Date'
#df = df.resample('24H').agg({'Open': 'first',
#                                 'High': 'max',
#                                 'Low': 'min',
#                                 'Close': 'last'})
#df.insert(0, 'rownum', range(0,len(df)))

#print(df)

ax = plot_candlestick(df)

SupDem(df, ax)


plt.tight_layout()
# plt.savefig("candle.png")
plt.show()

