import datetime
import time
from ccxt import kucoinfutures as kcf
from pandas import DataFrame as dataframe 
from ta import volatility

LEVERAGE = 20

LOTS = 500

TIMEFRAMES = ['1m']

COINS = ["KLAY/USDT:USDT","LUNC/USDT:USDT","GALA/USDT:USDT"]

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
    osc = volatility.bollinger_pband(getData(coin,tf)['close'], window=window, window_dev=dev, fillna=False).iloc[-period]
    return osc
while True:
    for tf, coin in [(tf,coin) for tf in TIMEFRAMES for coin in COINS]:
            try:
                print(dataframe(getPositions()))               
                pnl = getPositions()[coin]['percentage']
                contracts = getPositions()[coin]['contracts']
                side = getPositions()[coin]['side']
                if bands(13,1,1) > 1:
                    if side != 'short': 
                        exchange.create_market_buy_order(coin, LOTS, {'leverage': LEVERAGE})           
                    elif side == 'short':
                        exchange.create_market_buy_order(coin, contracts, {'reduceOnly':True, 'closeOrder':True})
                elif bands(13,1,1) < 0:
                    if side != 'long': 
                        exchange.create_market_sell_order(coin, LOTS, {'leverage': LEVERAGE})           
                    elif side == 'long':
                        exchange.create_market_sell_order(coin, contracts, {'reduceOnly':True, 'closeOrder':True})                          
            except Exception as e:
                print(e)
                time.sleep(10)
