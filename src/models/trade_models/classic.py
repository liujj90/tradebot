import pandas as pd
from src.models.base import TradeDecision
from src.pipeline import get_pair_info, compute_bid_ask_ratio, compile_ticker_feature
from src.utils import pg_engine
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def moving_average_crossover_strategy(data, short_window = 50, long_window = 200):
    # Compute short-term moving average
    data['short_ma'] = data['last_trade_closed'].rolling(window=short_window).mean()
    
    # Compute long-term moving average
    data['long_ma'] = data['last_trade_closed'].rolling(window=long_window).mean()
    
    # Generate buy/sell signals
    data['ma_signal'] = 0
    data.loc[data['short_ma'] > data['long_ma'], 'ma_signal'] = 1
    data.loc[data['short_ma'] < data['long_ma'], 'ma_signal'] = -1
    
    return data

def bollinger_bands_strategy(data, window = 10, num_std = 2):
    # Compute rolling mean and standard deviation
    data['rolling_mean'] = data['last_trade_closed'].rolling(window=window).mean()
    data['rolling_std'] = data['last_trade_closed'].rolling(window=window).std()
    
    # Compute upper and lower bands
    data['upper_band'] = data['rolling_mean'] + (data['rolling_std'] * num_std)
    data['lower_band'] = data['rolling_mean'] - (data['rolling_std'] * num_std)
    
    # Generate buy/sell signals
    data['bo_signal'] = 0
    data.loc[data['last_trade_closed'] < data['lower_band'], 'bo_signal'] = 1
    data.loc[data['last_trade_closed'] > data['upper_band'], 'bo_signal'] = -1
    
    return data

def mean_reversion_strategy(data, window = 10, num_std = 1.6):

    # Compute rolling mean and standard deviation
    data['rolling_mean'] = data['last_trade_closed'].rolling(window=window).mean()
    data['rolling_std'] = data['last_trade_closed'].rolling(window=window).std()

    # Compute upper and lower bounds
    data['upper_bound'] = data['rolling_mean'] + (data['rolling_std'] * num_std)
    data['lower_bound'] = data['rolling_mean'] - (data['rolling_std'] * num_std)

    # Generate buy/sell signals
    data['mr_signal'] = 0
    data.loc[data['last_trade_closed'] > data['upper_bound'], 'mr_signal'] = -1  # Overbought condition
    data.loc[data['last_trade_closed'] < data['lower_bound'], 'mr_signal'] = 1  # Oversold condition

    return data

class ClassicDecision(TradeDecision):
    description = "Classic trading algorithms based om moving average crossover"\
        "Bollinger Bands Strategy, Mean Reversion Strategy, Breakout Strategy"\
        "https://kritjunsree.medium.com/building-a-trading-bot-in-python-a-step-by-step-guide-with-examples-6898244016cd"

    def __init__(self):
        pass

    def feature_engineering(self):
        self.data = moving_average_crossover_strategy(self.data)
        self.data = bollinger_bands_strategy(self.data)
        self.data = mean_reversion_strategy(self.data)
        self.data['classic_signal'] = self.data['mr_signal'] + self.data['bo_signal'] + self.data['ma_signal'] 

        

    
    def get_data(self, pair='XBTUSDC'):
        

        ts_from = (datetime.now(tz=ZoneInfo("Asia/Singapore"))-timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        q = f"select * from kraken_ticker where snapshot_ts>'{ts_from}'"
        self.data = pg_engine.query_data(q)

        current_data = compile_ticker_feature(pair = pair)

        self.data = pd.concat([self.data, current_data])


        

    def decide(self, threshold = 2):

        self.get_data()
        self.feature_engineering()

        current_signal = self.data.iloc[-1,:]['classic_signal']
        print(current_signal)

        if current_signal >= threshold:
            return True, False, False
        elif current_signal <= 0:
            return False, True, False
        
        else: 
            return False, False, True 