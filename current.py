import time
import datetime
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import momentum, trend, volatility

lever = 10
tf = '1m'
coin = 'RSR/USDT:USDT'
lots = 100

exchange = kcf({
    'apiKey': '',
    'secret': '',
    'password': '',
    'adjustForTimeDifference': True})

markets = exchange.load_markets()


def getData(coin, tf):
    time.sleep(exchange.rateLimit / 1000)
    data = exchange.fetch_ohlcv(coin, tf, limit=500)
    df = {}
    for i, col in enumerate(['date', 'open', 'high', 'low', 'close',
                             'volume']):
        df[col] = []
        for row in data:
            if col == 'date':
                df[col].append(datetime.datetime.fromtimestamp(row[i] / 1000))
            else:
                df[col].append(row[i])
        DF = dataframe(df)
    return DF


def getPositions():
    positions = exchange.fetch_positions()
    df = {}
    df[coin] = {}
    for _, col in enumerate(['contracts', 'side', 'percentage', 'unrealizedPnl']):
        df[coin][col] = 0
        for (_, v) in enumerate(positions):
            if v['symbol'] == coin:
                df[coin][col] = v[col]
        DF = dataframe(df)
    return DF


class order:
    def buy():
        bid = exchange.fetch_order_book(coin)['bids'][0][0]
        if getPositions()[coin]['side'] != 'short':
            exchange.create_limit_order(
                coin, 'buy', lots,
                bid, {'leverage': lever})
        elif getPositions()[coin]['side'] == 'short':
            exchange.create_limit_order(coin, 'buy', getPositions()[coin]['contracts'], bid, {
                                        'closeOrder': True, 'reduceOnly': True})

    def sell():
        ask = exchange.fetch_order_book(coin)['asks'][0][0]
        if getPositions()[coin]['side'] != 'long':
            exchange.create_limit_order(
                coin, 'sell', lots, ask, {'leverage': lever})
        elif getPositions()[coin]['side'] == 'long':
            exchange.create_limit_order(coin, 'sell', getPositions()[coin]['contracts'], ask, {
                                        'closeOrder': True, 'reduceOnly': True})


def open(period=-1):
    return (getData(coin, tf)['close'].iloc[period-1] +
            getData(coin, tf)['open'].iloc[period-1])/2


def close(period=-1):
    return (getData(coin, tf)['close'].iloc[period] +
            getData(coin, tf)['high'].iloc[period] +
            getData(coin, tf)['low'].iloc[period] +
            getData(coin, tf)['open'].iloc[period])/4


def low(period=-1):
    return getData(coin, tf)['low'].iloc[period]


def high(period=-1):
    return getData(coin, tf)['high'].iloc[period]


def stc(fast=13, slow=34, cycle=8, smooth1=3, smooth2=3, period=-1):
    return trend.stc(getData(coin, tf)['close'], slow, fast, cycle, smooth1, smooth2).iloc[period]


def rsi(rsi_window=8, kama_window=2, period=-1):
    return momentum.kama(momentum.rsi(getData(coin, tf)['close'], rsi_window), kama_window).iloc[period]


def bands(window=21, devs=1, period=-1):
    return volatility.bollinger_pband(getData(coin, tf)['close'], window, devs).iloc[period]


def kama(window=8, period=-1):
    return momentum.kama(getData(coin, tf)['close'], window).iloc[period]


while True:
    try:
        while stc() >= stc(period=-2) and stc() > 25 and rsi() > 50 and close() > kama():
            print(getPositions())
            order.buy()
            if (open() < open(-2) and close() < close(-2)) or stc() < stc(period=-2) or close() < kama():
                order.sell()
                break

        while stc() <= stc(period=-2) and stc() < 75 and rsi() < 50 and close() < kama():
            print(getPositions())
            order.sell()
            if (open() > open(-2) and close() > close(-2)) or stc() > stc(period=-2) or close() > kama():
                order.buy()
                break

    except Exception as e:
        print(e)
