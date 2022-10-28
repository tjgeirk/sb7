
import datetime
import logging
import time
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
STOP_LOSS = -0.1
TAKE_PROFIT = 0.05
LEVERAGE = 5
TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h']

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

def macd(fast=13, slow=21, signal=8, period=1):
    macd = ema(c, fast) - ema(c, slow)
    signal = ema(macd, signal)
    return {'macd': macd.iloc[-period], 'signal': signal.iloc[-period]}

def bands(window=20, devs=2, period=1):
    return {
        'upper': volatility.bollinger_hband(c, window, devs).iloc[-period], 
        'lower': volatility.bollinger_lband(c, window, devs).iloc[-period], 
        'middle': volatility.bollinger_mavg(c, window, devs).iloc[-period]}

def donch(window=20, period=1):
    return {
        'upper': volatility.donchian_channel_hband(h,l,c,window).iloc[-period],
        'lower': volatility.donchian_channel_lband(h,l,c,window).iloc[-period],
        'middle': volatility.donchian_channel_mband(h,l,c,window).iloc[-period]
    }

while True:
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
        for tf in TIMEFRAMES:

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
            
            upperBand = bands()['upper']
            lowerBand =  bands()['lower']
            
            upperDonch = donch()['upper']
            lowerDonch = donch()['lower']
            upperStop = donch(5)['upper']
            lowerStop = donch(5)['lower']
            
            try:
                if pnl < STOP_LOSS or pnl > TAKE_PROFIT:
                    exchange.create_limit_order(coin, 'buy', contracts, bid, params=exit)
                    
                if ((Open > upperBand) and (Open > Close) and 
                    (macd()['macd'] < macd()['signal'])):
                        while True:
                            order.sell()
                            if ((h.iloc[-1] == upperStop) or
                                (macd()['macd'] > macd()['signal'])):
                                    order.buy()
                                    break
                                
                if ((Open < lowerBand) and (Open < Close) and 
                    (macd()['macd'] > macd()['signal'])):
                        while Open < Close:
                            order.buy()
                            if ((l.iloc[-1] == lowerStop) or 
                                (macd()['signal'] > macd()['macd'])):
                                    order.sell()
                                    break
                
                if ((l.iloc[-1] == lowerDonch) and (Open > Close)
                    and (macd()['macd'] < 0)):
                        while True:
                            order.sell()
                            if ((h.iloc[-1] == upperStop) or 
                                (macd()['macd'] > macd()['signal'])):
                                    order.buy()
                                    break
                    
                if ((h.iloc[-1] == upperDonch) and (Open < Close)
                    and (macd()['macd'] > 0)):
                        while True:
                            order.buy()
                            if ((l.iloc[-1] == lowerStop) or
                                 (macd()['macd'] < macd()['signal'])):
                                    order.sell()
                                    break
                        


            except Exception as e:
                print(e)
                logging.exception(e)
