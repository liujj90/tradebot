import sys 
sys.path.append('.')

import pandas as pd
import datetime

from src.models import DepthDecision, PercentileDecision
from src.pipeline import get_pair_info

depth_model = DepthDecision()
percentile_model = PercentileDecision()

class TradeModel:
    fees = 0.25/100 # 0.25% Fees
    def __init__(
        self, 
        btc_bal = 0.0, 
        usdc_bal = 1000, 
        trade_limit = 0.5, 
        # limit_target = 0.002, # 0.2% difference with current market
        savefilepath = "/home/jj/workspace/experiment.csv"
        ):
        self.btc_bal = btc_bal
        self.usdc_bal= usdc_bal
        self.trade_limit = trade_limit
        self.savefilepath = savefilepath 

        

    def one_decision(self, override_threshold=None):

        # default decision
        buy, sell, hold = False, False, True
        # Get trade decision based on percentile
        to_trade = percentile_model.decide(override_threshold=override_threshold)
        if to_trade: 
            print("Threshold met for trading decision") 
            buy, sell, hold = depth_model.decide()
        
        if hold:
            action = 'hold'
        elif buy:
            action = 'buy'
        else:
            action = 'sell'

        return to_trade, action

    def get_current_market(self):

        ticker_info, _ = get_pair_info(pair="XBTUSDC", get_depth=False)
        res = dict(
            price = ticker_info['c'][0], # last trade closed
            bid = ticker_info['b'][0],
            ask = ticker_info['a'][0],
            low_24h = ticker_info['l'][1],
            high_24h = ticker_info['h'][1], 
            vol_24h = ticker_info['v'][1],
            volume_wt_price_24h = ticker_info['p'][1]
            )
        
        return res


    def update_balance(self, data):

        # format data
        df = pd.DataFrame({
            k: [v] for k,v in data.items()
        })
        # save to sheet
        try:
            saved_df = pd.read_csv(self.savefilepath)
            final_df = pd.concat([saved_df, df])
        except: # file does not exist
            final_df = df

        final_df.to_csv(self.savefilepath, index=None)

    def execute_trade(self, current_market, trade_decision):
        
        executed = False 
        trade_amt = None
        trade_price = None

        if trade_decision == 'sell': # sell at bid price? 
            trade_amt = self.trade_limit * self.btc_bal
            trade_price = current_market['bid']
            if self.btc_bal > 0:
                self.btc_bal -= trade_amt
                usdc_amt = trade_amt * trade_price 
                self.usdc_bal += usdc_amt - usdc_amt * self.fees
                executed = True
        
        
        elif trade_decision == 'buy': # buy at ask price?
            trade_amt = self.trade_limit * self.usdc_bal
            trade_price = current_market['ask']
            if self.usdc_bal > 0:
                self.usdc_bal -= (trade_amt + trade_amt*self.fees)  
                self.btc_bal += trade_amt/trade_price
                executed = True

        return trade_amt, trade_price, executed

    def run(self, override_threshold=None): # only XBTUSDC support right now
        
        to_trade, action = self.one_decision(override_threshold=override_threshold)
        current_market = self.get_current_market()
        if to_trade:
            print(f"Trading. Action: {action}")
            trade_amt, trade_price, executed = self.execute_trade(current_market, action)
            current_market['time_now'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_market['trade_executed'] = executed
            current_market['trade_amt'] = trade_amt
            current_market['trade_price'] = trade_price
            self.update_balance(current_market)
            print(f"balance updated with data {current_market}") 
        else:
            print(f"No trade due to threshold decision not being met. pchange < {override_threshold or 1.5}")

if __name__ == '__main__':
    import time
    model = TradeModel()

    # run simulation
    while True:
        model.run(override_threshold=0.8)
        time.sleep(60)
            


        
                

        
    
    