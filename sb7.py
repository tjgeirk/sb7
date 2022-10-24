import datetime
import logging

logging.basicConfig(filename='shlongbot7.log', 
                    encoding='utf-8', level=logging.INFO)
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe 
from matplotlib import pyplot as plt
from ta import trend, volatility, momentum


exchange = kcf({
    'apiKey': '', 
    'secret': '', 
    'password': '', 
    'adjustForTimeDifference': True, 
})

COINS = ['SUSHI/USDT:USDT', 'KLAY/USDT:USDT', 'RNDR/USDT:USDT', 'OP/USDT:USDT']

LOTS_PER_TRADE = 10
STOP_LOSS = -0.2
TAKE_PROFIT = 0.1
LEVERAGE = 20
TIMEFRAME = '5m'
cycle = 0
def getData(coin, TIMEFRAME):
    data = exchange.fetch_ohlcv(coin, TIMEFRAME, limit=500)
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

def rsi(window, smooth, period):
    return trend.ema_indicator(momentum.rsi(c, window), smooth).iloc[-period]

def bands(window, devs, period):
    return {'upper': volatility.bollinger_hband(c, window, devs).iloc[-period], 'lower': volatility.bollinger_lband(c, window, devs).iloc[-period], 'middle': volatility.bollinger_mavg(c, window, devs).iloc[-period]}

#chart = {}
#for coin in COINS:
#    chart[coin] = []

while True:
    cycle += 1
    if cycle % 10 == 0:
        exchange.cancel_all_orders()
    for coin in COINS:
        if coin in getPositions():
            contracts = getPositions()[coin]['contracts']
            side = getPositions()[coin]['side']
            pnl = getPositions()[coin]['percentage']
            print(getPositions())
            #chart[coin].append(pnl)
        else:
            contracts = 0
            side = 0
            pnl = 0

        o = getData(coin, TIMEFRAME)['open']
        h = getData(coin, TIMEFRAME)['high']
        l = getData(coin, TIMEFRAME)['low']
        c = getData(coin, TIMEFRAME)['close']
        
        Open = (c.iloc[-2]+o.iloc[-2])/2
        lastOpen = (c.iloc[-3]+o.iloc[-3])/2
        Close = (c.iloc[-1]+h.iloc[-1]+l.iloc[-1])/3
        lastClose = (c.iloc[-2]+h.iloc[-2]+l.iloc[-2])/3

        ask = exchange.fetch_order_book(coin)['asks'][0][0]
        bid = exchange.fetch_order_book(coin)['bids'][0][0]

        exit = {'reduceOnly': True, 'closeOrder': True}
        enter = {'leverage': LEVERAGE}
                
        hema = ema(h, 8, 1)
        lema = ema(l, 8, 1)
        clema = ema(c, 8, 1)
        opema = ema(o, 8, 1)
        signal = ema(o,3,1)+ema(c,3,1)+ema(h,3,1)+ema(l,3,1)/4
        upperBand = bands(20, 2, 1)['upper']
        lowerBand =  bands(20, 2, 1)['lower']
        
        try:
            if pnl < -abs(STOP_LOSS) or pnl > abs(TAKE_PROFIT):
                print(0)
                if side == 'long':
                    order.sell()
                elif side == 'short':
                    order.buy()
            
            if side == 'long' and signal > Close and Open > Close: 
                print(5)
                order.sell()
            
            elif side == 'short' and signal < Close and Open < Close:
                print(6)
                order.buy()
            
            else:
                if hema < upperBand and lema > bands(20,2,1)['middle'] and rsi(13,8,1) < 80 and opema < clema and (ema(c,13,1) - ema(c,21,1)) < ema(c,8,1):
                    print(1)
                    order.buy()

                if lema > lowerBand and hema < bands(20,2,1)['middle'] and rsi(13,8,1) > 20 and opema > clema and (ema(c,13,1) - ema(c,21,1)) > ema(c,8,1):
                    print(2)
                    order.sell()
                
                if Open > Close and opema > clema and rsi(8,3,1) > 30 and (ema(c,100,1) - ema(c,200,1)) < ema(c,50,1) and (ema(c,13,1) - ema(c,21,1)) < ema(c,8,1):
                    print(3)
                    order.buy()
            
                if Open < Close and opema < clema and rsi(8,3,1) < 70 and (ema(c,100,1) - ema(c,200,1)) > ema(c,50,1) and (ema(c,13,1) - ema(c,21,1)) >  ema(c,8,1):
                    print(4)
                    order.sell()
                
        except Exception as e:
            print(e)
            logging.exception(e)

