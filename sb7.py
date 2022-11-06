import datetime
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import momentum, trend, volatility

STOP = 0.05
TRIGGER = 0.03
INIT_STOP = 0.1
LEVERAGE = 20
LOTS = 50
TIMEFRAMES = ['1m']
COINS = ["RNDR"]

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
        for _, col in enumerate(['contracts', 'side', 'percentage'
                                 ]):
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


def stoploss():
    stop = STOP if getPositions()[coin]['percentage'] > TRIGGER else INIT_STOP

    if getPositions()[coin]['percentage'] > trail[coin]:
        trail[coin] = getPositions()[coin]['percentage']
    if getPositions()[coin]['percentage'] < (trail[coin]-stop):
        sell() if getPositions()[coin]['side'] == 'long' else buy()
    return print('stop: ', stop, 'trail:', trail[coin])


def kelts(window=21, period=1):
    return volatility.keltner_channel_pband(getData(coin, tf)['high'], getData(coin, tf)['low'], getData(coin, tf)['close'], window).iloc[-period]


def bands(window=20, devs=2, period=1):
    return volatility.bollinger_pband(getData(coin, tf)['close'], window, devs).iloc[-period]


def kama(ohlc='close', period=1):
    return momentum.kama(getData(coin, tf)[ohlc]).iloc[-period]


def rsi(window=2, period=1):
    return momentum.kama(momentum.rsi(getData(coin, tf)['close'], window)).iloc[-period]


trail = {}
for coin in COINS:
    trail[coin] = 0

while True:
    for coin in COINS:
        exchange.cancel_all_orders()
        print(dataframe(getPositions()))
        for tf in TIMEFRAMES:

            print(dataframe(getPositions()[coin]))
            print('KARSI:', rsi())

            while kelts() > 1 and rsi() > 50 and getData(coin, tf)['close'].iloc[-1] > kama():
                buy()
            while kelts() < 0 and rsi() < 50 and getData(coin, tf)['close'].iloc[-1] < kama():
                sell()

            while getPositions()[coin]['contracts'] != 0:
                if getPositions()[coin]['side'] == 'long':
                    sell() if rsi() < 50 else buy()
                elif getPositions()[coin]['side'] == 'short':
                    buy() if rsi() > 50 else sell()
