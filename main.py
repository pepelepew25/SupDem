from plot import *
import pandas as pd
import numpy as np
from supply_demand_zones import SupDem
import sys
#sys.path.append('../backtesting_bot/')
import GetMarketData
import logging
logging.basicConfig(level=logging.DEBUG, format='[%(funcName)10s] %(message)s',
                    #filename='backtesting.log',
                    filemode='w')

#days_history = 30
days_history = 300

symbol = 'XBTUSD'
#symbol = 'ETHUSD'

df = GetMarketData.GetCCXTMarketData(symbol, days_history, "1h", True)

if not len(df):
    print("empty dataframe")
    exit()

df = df.dropna()
df.index.name = 'Date'

#ax = plot_candlestick(df)
plot_candlestick(df)

#df = df.resample('4H').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})


s = SupDem(df[-300:])
s.plot_fractals()
s.drawzones()

df = df.resample('24H').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})
s = SupDem()
s.plot_fractals()
s.drawzones()

df = df.resample('W').agg({'Open': 'first', 'High': 'max','Low': 'min','Close': 'last'})
s = SupDem()
s.plot_fractals()
s.drawzones()
ax = plt.gca()
ax.set_xmargin(0.2)
ax.autoscale_view()
plt.tight_layout()
# plt.savefig("candle.png")
plt.show()

