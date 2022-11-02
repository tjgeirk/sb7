import datetime
import time
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import volatility, trend

LEVERAGE = 20

LOTS = 10

TIMEFRAMES = ['1m']

COINS = ["LIT/USDT:USDT", "DOGE/USDT:USDT", "SHIB/USDT:USDT", "LUNC/USDT:USDT", "LUNA/USDT:USDT"]

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


def width(window=13, dev=1, period=1):
    absolute = volatility.bollinger_wband(
        getData(coin, tf)['close'], window, dev)
    w = trend.sma_indicator(absolute, window).iloc[-period]
    return w


while True:
    for coin in COINS:
        for tf in TIMEFRAMES:
            try:
                print(dataframe(getPositions()))
                pnl = getPositions()[coin]['percentage']
                contracts = getPositions()[coin]['contracts']
                side = getPositions()[coin]['side']
                
                if bands() > 1 and width(13) > width(21):
                    exchange.create_market_order(
                        coin, 'buy', LOTS, None, {'leverage': LEVERAGE})
                
                if bands() < 0 and width(13) > width(21):
                    exchange.create_market_order(
                        coin, 'sell', LOTS, None, {'leverage': LEVERAGE})
            
            except Exception as e:
                print(e)
                time.sleep(10)
