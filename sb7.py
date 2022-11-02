import datetime
import time
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import volatility, trend

LEVERAGE = 20

LOTS = 10

TIMEFRAMES = ['1m', '5m', '15m']

COINS = ["DOGE/USDT:USDT"]

exchange = kcf({
    'apiKey': '',
    'secret': '',
    'password': '',
    'adjustForTimeDifference': True,
})


def getData(coin, tf):
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
    for coin in COINS:
        df[coin] = {}
        for i, col in enumerate(['contracts', 'side', 'percentage']):
            df[coin][col] = 0
            for _, v in enumerate(positions):
                if v['symbol'] == coin:
                    df[coin][col] = v[col]
        DF = dataframe(df)
    return DF


def bands(window=13, dev=1, period=1):
    osc = volatility.bollinger_pband(getData(
        coin, tf)['close'], window=window, window_dev=dev, fillna=False).iloc[-period]
    return osc


def upper(window=13, dev=1, period=1):
    band = volatility.bollinger_hband(getData(
        coin, tf)['close'], window=window, window_dev=dev, fillna=False).iloc[-period]
    return band


def lower(window=13, dev=1, period=1):
    band = volatility.bollinger_lband(getData(
        coin, tf)['close'], window=window, window_dev=dev, fillna=False).iloc[-period]
    return band

def width(window=21, smooth=13, dev=1, period=1):
    absolute = volatility.bollinger_wband(getData(coin,tf)['close'], window, dev)
    avg = trend.sma_indicator(absolute, smooth)
    return {'width':absolute.iloc[-period], 'avg':avg.iloc[-period]}

while True:
    for tf, coin in [(tf, coin) for tf in TIMEFRAMES for coin in COINS]:
        try:
            print(dataframe(getPositions()))
            pnl = getPositions()[coin]['percentage']
            contracts = getPositions()[coin]['contracts']
            side = getPositions()[coin]['side']

            if bands() > 1 and width() ['width'] > width()['avg']:
                if side == 'short':
                    exchange.create_market_order(
                        coin, 'buy', contracts, None, {'closeOrder': True})
                exchange.create_market_order(
                    coin, 'buy', LOTS, None, {'leverage': LEVERAGE})

            elif bands() < 0 and width()['width'] > width()['avg']:
                if side == 'long':
                    exchange.create_market_order(
                        coin, 'sell', contracts, None, {'closeOrder': True})
                exchange.create_market_order(
                    coin, 'sell', LOTS, None, {'leverage': LEVERAGE})

        except Exception as e:
            print(e)
            time.sleep(10)
