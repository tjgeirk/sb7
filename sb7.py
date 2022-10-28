import datetime
import logging

logging.basicConfig(filename='shlongbot7.log', 
                    encoding='utf-8', level=logging.INFO)

from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe 
from ta import trend, volatility, momentum

exchange = kcf({
    'apiKey': '',
    'secret': '',
    'password': '',
    'adjustForTimeDifference': True, 
})

COINS = ["KLAY/USDT:USDT", "OP/USDT:USDT", "SHIB/USDT:USDT", "DOGE/USDT:USDT"]

LOTS_PER_TRADE = 10
LEVERAGE = 5
TIMEFRAMES = ['1m','5m','15m','1h']

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

class order:
    def __init__(self, contracts, side, bid, ask, enter, exit):
        self.contracts = contracts
        self.side = side
        self.bid = bid
        self.ask = ask
        self.enter = enter
        self.exit = exit

    def buy():
        if side == 'short':
            return exchange.create_limit_order(coin, 'buy', contracts, bid, params=exit)
        
        elif side != 'short':
            return exchange.create_limit_order(coin, 'buy', LOTS_PER_TRADE, bid, params=enter)

    def sell():
        if side == 'long':
            return exchange.create_limit_order(coin, 'sell', contracts, ask, params=exit)
        
        if side != 'long':
            return exchange.create_limit_order(coin, 'sell', LOTS_PER_TRADE, ask, params=enter)

def ema(ohlc, window, period):
    return trend.ema_indicator(ohlc, window).iloc[-period]

def bands(window, devs, period):
    return {'upper': volatility.bollinger_hband(c, window, devs).iloc[-period], 'lower': volatility.bollinger_lband(c, window, devs).iloc[-period], 'middle': volatility.bollinger_mavg(c, window, devs).iloc[-period]}

while True:
    for tf in TIMEFRAMES:
        print(getPositions())
        for coin in COINS:
            if coin in getPositions():
                contracts = getPositions()[coin]['contracts']
                side = getPositions()[coin]['side']
                pnl = getPositions()[coin]['percentage']
            else:
                contracts = None
                side = None
                pnl = None

            o = getData(coin, tf)['open']
            h = getData(coin, tf)['high']
            l = getData(coin, tf)['low']
            c = getData(coin, tf)['close']
            
            Open = (c.iloc[-2]+o.iloc[-2])/2
            lastOpen = (c.iloc[-3]+o.iloc[-3])/2
            Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3
            lastClose = (c.iloc[-2]+h.iloc[-2]+l.iloc[-2])/3

            ask = exchange.fetch_order_book(coin)['asks'][0][0]
            bid = exchange.fetch_order_book(coin)['bids'][0][0]

            exit = {'reduceOnly': True, 'closeOrder': True}
            enter = {'leverage': LEVERAGE}
            
            hema =  ema(h, 8, 1)
            lema = ema(l, 8, 1)
            clema = ema(c, 8, 1)
            opema = ema(o, 8, 1)

            upperBand = bands(20, 2, 1)['upper']
            lowerBand =  bands(20, 2, 1)['lower']
            
            try:
                if Close < lema and opema > clema:
                    order.sell()

                if Close > lema and opema < clema:
                    order.buy()
            
                if (Close or lastClose) > upperBand and h.iloc[-2] > h.iloc[-1]:
                    order.sell()
                        
                if (Close or lastClose) < lowerBand and l.iloc[-2] < l.iloc[-1]:
                    order.buy()

                if Open > upperBand > Close:
                    order.sell()
                        
                if Open < lowerBand < Close:
                    order.buy()

            except Exception as e:
                print(e)
                logging.exception(e)
