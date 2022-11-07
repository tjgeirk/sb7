import time
import datetime
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe
from ta import momentum, trend, volatility

LEVERAGE = 20
TIMEFRAMES = ['1m']
COINS = ["OP"]
DCA_INTERVAL_DELAY_TIME: 0
DCA_LOTS_PER_INTERVAL = 1

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
        for _, col in enumerate(['contracts', 'side', 'percentage', 'unrealizedPnl']):
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
                coin, 'buy', DCA_LOTS_PER_INTERVAL,
                exchange.fetch_order_book(coin)['bids'][0][0],
                {'leverage': LEVERAGE})
        except Exception:
            pass
    elif getPositions()[coin]['side'] == 'short':
        try:
            return exchange.create_limit_order(
                coin, 'buy', getPositions()[coin]['contracts'],
                exchange.fetch_order_book(coin)['bids'][0][0],
                {'closeOrder': True, 'reduceOnly': True})
        except Exception:
            pass


def sell():
    if getPositions()[coin]['side'] != 'long':
        try:
            return exchange.create_limit_order(
                coin, 'sell', DCA_LOTS_PER_INTERVAL,
                exchange.fetch_order_book(coin)['asks'][0][0],
                {'leverage': LEVERAGE})
        except Exception:
            pass
    elif getPositions()[coin]['side'] == 'long':
        try:
            return exchange.create_limit_order(
                coin, 'sell', getPositions()[coin]['contracts'],
                exchange.fetch_order_book(coin)['asks'][0][0],
                {'closeOrder': True, 'reduceOnly': True})
        except Exception:
            pass
        
def bands(window=20, devs=2, period=1):
    return volatility.bollinger_pband(getData(coin, tf)['close'], window, devs).iloc[-period]


def kama(ohlc='close', window=8, period=1):
    return momentum.kama(getData(coin, tf)[ohlc], window).iloc[-period]


def rsi(rsi_window=8, kama_window=2, period=1):
    return momentum.kama(momentum.rsi(getData(coin, tf)['close'], rsi_window), kama_window).iloc[-period]


while True:
    for coin in COINS:
        exchange.cancel_all_orders()
        for tf in TIMEFRAMES:

            buysignal1 = (bands(20, 2) < 0)
            buysignal2 = (getData(coin, tf)['high'].iloc[-1] >
                          getData(coin, tf)['high'].iloc[-2] and
                          getData(coin, tf)['low'].iloc[-1] >
                          getData(coin, tf)['low'].iloc[-2])
            buysignal3 = (getData(coin, tf)['close'].iloc[-1] > kama())

            sellsignal1 = (bands(20, 2) > 1)
            sellsignal2 = (getData(coin, tf)['high'].iloc[-1] <
                           getData(coin, tf)['high'].iloc[-2] and
                           getData(coin, tf)['low'].iloc[-1] <
                           getData(coin, tf)['low'].iloc[-2])
            sellsignal3 = (getData(coin, tf)['close'].iloc[-1] < kama())

            while rsi() >= 50 and buysignal3 and buysignal2:
                print(getPositions())
                print('ADAPT.RSI:', round(rsi(), 2))
                buy()
                if sellsignal1 or sellsignal2 or sellsignal3:
                    sell()
                    break
                else:
                    time.sleep(DCA_INTERVAL_DELAY_TIME)
            
            while rsi() <= 50 and sellsignal3:
                print(getPositions())
                print('ADAPT.RSI:', round(rsi(), 1))
                sell()
                if buysignal1 or buysignal2 or buysignal3:
                    buy()
                    break
                else:
                    time.sleep(DCA_INTERVAL_DELAY_TIME)
