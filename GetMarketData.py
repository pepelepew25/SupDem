<<<<<<< HEAD
import pprint, logging
import time
import csv
from datetime import datetime,timezone,timedelta
=======
#import polo_py3
import pprint, logging
import time
import csv
import krakenex
from datetime import datetime,timezone,timedelta
from pandas_datareader_gdax import get_data_gdax
>>>>>>> ae649f336a723413014a93f3f9e4252e35b695d1
import argparse
import pandas as pd
import numpy as np
import pytz
import ccxt
<<<<<<< HEAD

=======
bitmex = ccxt.bitmex({
    'enableRateLimit': True,
})
>>>>>>> ae649f336a723413014a93f3f9e4252e35b695d1

pp = pprint.PrettyPrinter(indent=4)


<<<<<<< HEAD
def GetCCXTMarketData(pair, days_history, period, offline):

    exchange = ccxt.bitmex({
        'enableRateLimit': True,
    })
=======
def get_latest_funding(symbol):

    inst = bitmex.publicGetInstrument({'symbol': symbol})
    logging.debug(pp.pformat(inst))
    funding={}
    funding['fundingRate'] = inst[0]['fundingRate']
    funding['timestamp'] = inst[0]['fundingTimestamp']
    funding['fundingInterval'] = inst[0]['fundingInterval']
    predicted = inst[0]['indicativeFundingRate']
    return(funding)


def __sync_funding(symbol, days_history, offline=False):

    filename = "./funding_" + symbol + "_" + str(days_history) + ".pkl"
    starttime = datetime.now(tz=timezone.utc) - timedelta(days=days_history)
    current_day = starttime.replace(hour=0, minute=0, second=0)
    try:
        logging.info("funding: trying to read existing data frame from disk")
        df = pd.read_pickle(filename)
        #df.set_index('timestamp', inplace=True)
        #df = df.drop(['fundingPredictedTime'], axis=1)
        #df.index = pd.to_datetime(df.index).tz_localize(pytz.utc)
        last_record = df.index[len(df.index) - 1]
        logging.debug('last record ' + str(last_record))
        current_day = last_record
    except FileNotFoundError:
        print("no existing dataframe on disk, creating a blank one")
        df = pd.DataFrame()


    print('today day ' + str(datetime.now(tz=timezone.utc)))
    if offline and len(df):
        return df

    logging.debug("request each new funding day one by one")
    while current_day < datetime.now(tz=timezone.utc):
        logging.debug('requesting day:' + str(current_day))
        next_date = current_day + timedelta(days=30)

        funding = bitmex.publicGetFunding({'symbol': symbol, 'startTime': current_day, 'endTime': next_date})
        logging.debug(pp.pformat(funding))
        if funding:
            df2 = pd.DataFrame(funding)
            # df_funding['fundingPredictedTime'] = pd.to_datetime(df_funding.timestamp).tz_localize(pytz.utc) - pd.to_timedelta(8, unit='h')
            df2.set_index('timestamp', inplace=True)
            df2.index = pd.to_datetime(df2.index).tz_localize(pytz.utc)
            df2 = df2.drop(['fundingInterval'], axis=1)
            print(df2.to_string())
            df = df.append(df2)

        current_day = next_date
        time.sleep(2)

    funding = []
    funding.append(get_latest_funding(symbol))
    logging.debug(pp.pformat(funding))
    if funding:
        df2 = pd.DataFrame(funding)
        # df_funding['fundingPredictedTime'] = pd.to_datetime(df_funding.timestamp).tz_localize(pytz.utc) - pd.to_timedelta(8, unit='h')
        df2.set_index('timestamp', inplace=True)
        df2.index = pd.to_datetime(df2.index).tz_localize(pytz.utc)
        df2 = df2.drop(['fundingInterval'], axis=1)
        print(df2.to_string())
        df = df.append(df2)
    #print('new dataframe concatenated %d:' % len(df.index))
    #print(df.to_string())
    #drop duplicates
    #df = df.drop_duplicates()
    df = df.groupby(level=0).first()
    #print('after drop duplicates %d:' % len(df.index))
    #print(df.to_string())
    df.to_pickle(filename)
    return df


def GetHistoricalMarketdata(symbol, period, tf='1h', offline='False'):
    df_funding = __sync_funding(symbol, period, offline)
    # exit()
    # df_funding = pd.read_pickle("./funding_" + str(days_history) + "days.pkl")
    #df_funding = pd.read_pickle("./funding_" + symbol + ".pkl")
    df_funding['fundingPredictedTime'] = pd.to_datetime(df_funding.index) - pd.to_timedelta(8, unit='h')
    # df['fundingPredictedTime'] = pd.to_datetime(df.timestamp) - pd.to_datetime(df.fundingInterval).hour
    df_funding.set_index('fundingPredictedTime', inplace=True)
    df_funding = df_funding.drop(['fundingRateDaily'], axis=1)
    df_funding = df_funding.drop(['symbol'], axis=1)
    logging.debug(df_funding)
    # exit()

    # period = "6h"

    #try:
    #    df = pd.read_pickle("./bitmex_" + symbol + "_" + str(period) + "days.pkl")
    #except FileNotFoundError:
    df = GetCCXTMarketData(bitmex, symbol, period, tf, offline)



    #symbol = 'BTC-USD'
    #try:
     #   df = pd.read_pickle("./gdax_" + symbol + "_" + str(period) + "days.pkl")
    #except FileNotFoundError:
     #   df = GetGdaxMarketData(symbol, period, "onehour")

    logging.debug(df)
    logging.debug("merging ohlc with funding")
    df = pd.merge(df, df_funding, left_index=True, right_index=True, how='left')
    df.fillna(method='ffill', inplace=True)

    logging.debug(df)
    return df


def GetCCXTMarketData(exchange, pair, days_history, period, offline=False):
>>>>>>> ae649f336a723413014a93f3f9e4252e35b695d1
    logging.info("GetCCXTMarketData: pair={} days={} period={}".format(pair,days_history,period))
    if pair == 'XBTUSD':
        pair ='BTC/USD'
    if pair == 'ETHUSD':
        pair = 'ETH/USD'
    filename = "./bitmex" + "_" + pair.replace('/','') + "_" + period + "_" + str(days_history) + "days.pkl"

<<<<<<< HEAD
    logging.info("trying to read existing data frame from disk from: {}".format(filename))
=======
    logging.info("reading existing data frame from disk")
>>>>>>> ae649f336a723413014a93f3f9e4252e35b695d1
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

