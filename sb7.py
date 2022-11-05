import datetime
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import volatility, momentum, trend

LEVERAGE = 10
LOTS = 10
TIMEFRAMES = ['1m']
COINS = ['LRC', 'BAND', 'YGG', 'OP', 'OCEAN', 'MATIC']
exchange = kcf({
    'apiKey': '',
    'secret': '',
    'password': '',
    'adjustForTimeDifference': True})

coins = []
if 'all' in COINS:
    for v in exchange.load_markets():
        if '/USDT:USDT' in v:
            coins.append(v)
else:
    for item in COINS:
        coins.append(str(f"{item}/USDT:USDT"))
COINS = coins


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
        for _, col in enumerate(['contracts', 'side', 'percentage']):
            df[coin][col] = 0
            for (_, v) in enumerate(positions):
                if v['symbol'] == coin:
                    df[coin][col] = v[col]
        DF = dataframe(df)
    return DF


def buy():
    if getPositions()[coin]['side'] != 'short':
        try:
            return exchange.create_limit_order(
                coin, 'buy', LOTS,
                exchange.fetch_order_book(coin)['bids'][0][0],
                {'leverage': LEVERAGE})
        except Exception as e:
            print(e)
    elif getPositions()[coin]['side'] == 'short':
        try:
            return exchange.create_limit_order(
                coin, 'buy', getPositions()[coin]['contracts'],
                exchange.fetch_order_book(coin)['bids'][0][0],
                {'closeOrder': True, 'reduceOnly': True})
        except Exception as e:
            print(e)


def sell():
    if getPositions()[coin]['side'] != 'long':
        try:
            return exchange.create_limit_order(
                coin, 'sell', LOTS,
                exchange.fetch_order_book(coin)['asks'][0][0],
                {'leverage': LEVERAGE})
        except Exception as e:
            print(e)
    elif getPositions()[coin]['side'] == 'long':
        try:
            return exchange.create_limit_order(
                coin, 'sell', getPositions()[coin]['contracts'],
                exchange.fetch_order_book(coin)['asks'][0][0],
                {'closeOrder': True, 'reduceOnly': True})
        except Exception as e:
            print(e)


def ema(ohlc='close', window=8, period=1):
    return trend.ema_indicator(getData(coin, tf)[ohlc], window).iloc[-period]


def bands(window=20, dev=1, period=1):
    return {
        'pb': volatility.bollinger_pband(
            getData(coin, tf)['close'], window, dev).iloc[-period],
        'dn': volatility.bollinger_lband(
            getData(coin, tf)['close'], window, dev).iloc[-period],
        'up': volatility.bollinger_hband(
            getData(coin, tf)['close'], window, dev).iloc[-period]
    }


def rsi(window=2, period=1):
    return momentum.rsi(getData(coin, tf)['close'], window).iloc[-period]


while True:
    for coin in COINS:
        exchange.cancel_all_orders()
        print(dataframe(getPositions()))
        for tf in TIMEFRAMES:
            print(dataframe(getPositions()[coin]))
            # LONG
            if bands()['pb'] > 1 and rsi() > 70:
                while ema('close', 1) > ema() > ema('close', 200):
                    buy()
            while (getPositions()[coin]['side'] == 'long'):
                sell()

            # SHORT
            while bands()['pb'] < 0 and rsi() < 30:
                while ema('close', 1) < ema() < ema('close', 200):
                    sell()
            while getPositions()[coin]['side'] == 'short':
                buy()
