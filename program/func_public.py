from datetime import datetime, timedelta
from func_utils import get_ISO_times
from constants import RESOLUTION
import pandas as pd
import numpy as np
import time 
from pprint import pprint

ISO_TIMES = get_ISO_times()



def get_candles_recent(client, market):
    close_prices = []
    time.sleep(0.2)

    candles = client.public.get_candles(
        market=market,
        resolution=RESOLUTION,
        limit=100
    )

    for candle in candles.data['candles']:
        close_prices.append(candle['close'])

    close_prices.reverse()
    prices_result = np.array(close_prices).astype(np.float)
    return prices_result

# print(ISO_TIMES)
def get_candles_historical(client, market):
    close_prices = []

    for timeframe in ISO_TIMES.keys():
        tf_obj = ISO_TIMES[timeframe]
        from_iso = tf_obj['from_iso']
        to_iso = tf_obj['to_iso']

        time.sleep(0.3)

        candles = client.public.get_candles(
            market=market,
            resolution=RESOLUTION,
            from_iso=from_iso,
            to_iso=to_iso,
            limit=100
        )
        # print(candles.data)

        for candle in candles.data['candles']:
            close_prices.append({'datetime': candle['startedAt'], market: candle['close']})

        # print(close_prices)

    close_prices.reverse()
    return close_prices


def construct_market_prices(client):
    tradeable_markets = []
    markets = client.public.get_markets()

    for market in markets.data['markets'].keys():
        market_info = markets.data['markets'][market]
        if market_info['status'] == 'ONLINE' and market_info['type'] == 'PERPETUAL':
            tradeable_markets.append(market)
            # print(tradeable_markets)

    close_prices = get_candles_historical(client, tradeable_markets[0])

    # pprint(close_prices)
    df = pd.DataFrame(close_prices)
    df.set_index('datetime', inplace=True)
    # print(df.head())

    for market in tradeable_markets[1:]:
        close_prices_add = get_candles_historical(client, market)
        df_add = pd.DataFrame(close_prices_add)
        df_add.set_index('datetime', inplace=True)
        df = pd.merge(df, df_add, how='outer', on='datetime', copy=False)
        del df_add

    nans = df.columns[df.isna().any()].to_list()
    if len(nans) > 0:
        df.drop(columns=nans, inplace=True)
    # print(df['XTZ-USD'].spread(1))
    return df