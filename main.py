from plot import *
import pandas as pd
import numpy as np
from supply_demand_zones import *
import sys
#sys.path.append('../backtesting_bot/')
import GetMarketData
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s',
                    #filename='backtesting.log',
                    filemode='w')

days_history = 300
    #days_history = 100

symbol = 'XBTUSD'
#symbol = 'ETHUSD'

df = GetMarketData.GetHistoricalMarketdata(symbol, days_history, 'False')
if not len(df):
    print("empty dataframe")
    exit()

df = df.dropna()

df.index.name = 'Date'

ax = plot_candlestick(df)
#df = df.resample('4H').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})
#SupDem(df, ax)
df = df.resample('24H').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})
SupDem(df, ax)
df = df.resample('W').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})
SupDem(df, ax)
plt.tight_layout()
# plt.savefig("candle.png")
plt.show()

