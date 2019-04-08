import pprint, logging
import time
import csv
from datetime import datetime,timezone,timedelta
import argparse
import pandas as pd
import numpy as np
import pytz
import ccxt


pp = pprint.PrettyPrinter(indent=4)


def GetCCXTMarketData(pair, days_history, period, offline):

    exchange = ccxt.bitmex({
        'enableRateLimit': True,
    })
    logging.info("GetCCXTMarketData: pair={} days={} period={}".format(pair,days_history,period))
    if pair == 'XBTUSD':
        pair ='BTC/USD'
    if pair == 'ETHUSD':
        pair = 'ETH/USD'
    filename = "./bitmex" + "_" + pair.replace('/','') + "_" + period + "_" + str(days_history) + "days.pkl"

    logging.info("trying to read existing data frame from disk from: {}".format(filename))
    try:
        df = pd.read_pickle(filename)
        # df.set_index('timestamp', inplace=True)
        # df = df.drop(['fundingPredictedTime'], axis=1)
        # df.index = pd.to_datetime(df.index).tz_localize(pytz.utc)
        last_record = df.index[len(df.index) - 1]
        logging.debug('last record ' + str(last_record))
        since = datetime.timestamp(last_record) * 1000
        logging.info("dataframe loaded from disk")
    # or create it
    except (FileNotFoundError, IndexError):
        logging.info("no existing dataframe on disk, creating a blank one")
        df = pd.DataFrame()

    if offline and len(df):
        return df

    if exchange.has['fetchOHLCV']:

        exchange.loadMarkets()
        #pp.pprint(exchange.markets.keys())

        if pair not in exchange.markets:
            exit()

        if df.empty:
            since = exchange.milliseconds() - (86400000 * days_history)
        # recover new records
        all_records = []
        #since = exchange.milliseconds() - 86400000
        while since < exchange.milliseconds():
            logging.debug("getting records for {} {}".format(since,datetime.fromtimestamp(since / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')))
            time.sleep(exchange.rateLimit / 1000)  # time.sleep wants seconds
            #ohlcv = exchange.fetch_ohlcv(pair, '1h', since=datetime.timestamp(datetime.now() - timedelta(days=days_history)))
            records = exchange.fetch_ohlcv(pair, '1h', since=int(since))
            if len(records):
                since = records[len(records) - 1][0]
                logging.debug("new since {} {}".format(since, datetime.fromtimestamp(since / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')))
                all_records += records
            else:
                break
        if len(all_records) > 0:
            all_records = np.array(all_records)

            df2 = pd.DataFrame(all_records[:, 1:], index=all_records[:, 0], columns=['Open', 'High', 'Low', 'Close', 'Volume'])

            df2.index = pd.to_datetime(pd.to_numeric(df2.index), utc=True, unit='ms')

            df = df.append(df2)
        # unique records
        df = df.groupby(level=0).first()
        logging.debug(df)
        df = df.sort_index(ascending=True)

    logging.debug(df)
    # saving dataframe
    df.to_pickle(filename)

    return df

