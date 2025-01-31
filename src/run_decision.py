import sys 
sys.path.append('.')

import pandas as pd
import datetime

from src.models import DepthDecision, PercentileDecision, ClassicDecision
from src.pipeline import get_pair_info, execute_trade_with_buffer, get_free_balance

depth_model = DepthDecision()
percentile_model = PercentileDecision()
classic_model = ClassicDecision()

class TradeModel:
    fees = 0.25/100 # 0.25% Fees
    min_usdc_balance = 50
    min_btc_balance = 0.00001
    
    def __init__(
        self, 
        simulated_btc_bal = 0.0, 
        simulated_usdc_bal = 1000, 
        trade_limit = 0.5, 
        savefilepath = "/home/jj/workspace/experiment.csv",
        trade_time_threshold = 60 * 60, # 1h
        simulation = True
        ):
        
        self.trade_limit = trade_limit
        self.savefilepath = savefilepath 
        self.trade_time_threshold = trade_time_threshold
        self.simulation = simulation
        self.last_buy_ts = datetime.datetime.now() - datetime.timedelta(days = 1) # initialize 
        self.last_sell_ts = datetime.datetime.now() - datetime.timedelta(days = 1) 
    

        if not self.simulation:
            print("""ALERT: SIMULATION IS OFF. REAL TRADES MAY BE SUBMITTED """)
            self.usdc_bal, self.btc_bal = get_free_balance()
        else: 
            print("""SIMULATION IS ON""")
            self.btc_bal = simulated_btc_bal
            self.usdc_bal= simulated_usdc_bal
        

    def one_decision(self, override_threshold=None):

        # default decision
        buy, sell, hold = False, False, True
        # Get trade decision based on percentile
        to_trade = percentile_model.decide(override_threshold=override_threshold)
        if to_trade: 
            print("Threshold met for trading decision") 
            depth_buy, depth_sell, depth_hold = depth_model.decide()
            classic_buy, classic_sell, classic_hold = classic_model.decide()
            print(f"Depth algorithm results: {depth_buy}, {depth_sell}, {depth_hold}")
            print(f"Classic algorithm results: {classic_buy}, {classic_sell}, {classic_hold}")

            buy = depth_buy or classic_buy
            sell = depth_sell or classic_sell
            hold = depth_hold or classic_hold
        
        if hold: #any hold -> hold
            action = 'hold'
        elif sell or buy: # split decision -> hold
            action = 'hold'
        elif sell:
            action = 'sell'
        else:
            action = 'buy'

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

    def execute_simulted_trade(self, current_market, trade_decision):
        
        executed = False 
        trade_amt = None
        trade_price = None
        description = "Not Executed"
        ts = datetime.datetime.now()
        
        if trade_decision == 'sell': # sell at bid price? 
            trade_amt = self.trade_limit * self.btc_bal
            trade_price = float(current_market['bid'])
            if self.btc_bal > self.min_btc_balance:
                if (ts - self.last_sell_ts).total_seconds() > self.trade_time_threshold:
                    self.btc_bal -= trade_amt
                    usdc_amt = trade_amt * trade_price 
                    self.usdc_bal += usdc_amt - usdc_amt * self.fees
                    executed = True
                    self.last_sell_ts = ts
                    description = f"{ts}: sold {trade_amt} btc @ {trade_price} for {usdc_amt} USDC"
                else:
                    description = "sell not executed because current time is too close to last sell timestamp"

            else: 
                description = "sell not executed because min btc balance not reached"
        
        elif trade_decision == 'buy': # buy at ask price?
            trade_amt = self.trade_limit * self.usdc_bal
            trade_price = float(current_market['ask'])
            if self.usdc_bal > self.min_usdc_balance:
                if (ts - self.last_buy_ts).total_seconds() > self.trade_time_threshold:
                    self.usdc_bal -= (trade_amt + trade_amt*self.fees)  
                    btc_amt = trade_amt/trade_price
                    self.btc_bal += btc_amt
                    executed = True
                    self.last_buy_ts = ts
                    description = f"{ts}: buy {btc_amt} @ {trade_price} USDC * {trade_amt}"
                else:
                    description = "buy not executed because current time is too close to last buy timestamp"
            else: 
                description = "buy not executed because min usdc balance not reached"

        else: 
            description = "decided to hold"

        return trade_amt, trade_price, executed, description

    def execute_real_trade(self, current_market, trade_decision, **kwargs):
        ts = datetime.datetime.now()
        # prep kwargs
        buffer = kwargs.get("buffer", 0.01)
        validate = kwargs.get("validate", True)

        if validate == False:
            print("""ALERT: VALIDATION IS OFF, TRADES WILL BE SUBMITTED """)

        # default
        executed = False 
        trade_amt = kwargs.get("volume", 0.005)
        trade_price = float(current_market['price'])
        description = "Not Executed"
        ts = datetime.datetime.now()

        if trade_decision == "hold":
            description = "decided to hold"
            return trade_amt, trade_price, executed, description

        elif trade_decision == 'sell' and (ts - self.last_sell_ts).total_seconds() <= self.trade_time_threshold:
            description = "sell not executed because current time is too close to last sell timestamp"
            return trade_amt, trade_price, executed, description
        
        elif trade_decision == 'buy' and (ts - self.last_buy_ts).total_seconds() <= self.trade_time_threshold:
            description = "buy not executed because current time is too close to last buy timestamp"
            return trade_amt, trade_price, executed, description


        order_details, response = execute_trade_with_buffer(
                trade_decision,
                trade_amt, 
                "XBTUSDC",
                trade_price, # this will be adjusted
                order_type="limit",
                rel_pth = "./",
                **kwargs
            )

        if isinstance(order_details, str):
            description = f"{trade_decision} not executed because min balance not reached"

        else: # trade executed
            description = response['result']['descr']['order']
            trade_amt = order_details['volume']
            trade_price = order_details['price']
            executed = True

            self.usdc_bal, self.btc_bal = get_free_balance()
        
            if trade_decision == 'sell':
                self.last_sell_ts = ts

            elif trade_decision == 'buy':
                self.last_buy_ts = ts

        return trade_amt, trade_price, executed, description


    def run(self, **kwargs): # only XBTUSDC support right now

        override_threshold=kwargs.get("override_threshold", 0.8)
        print(override_threshold)
        to_trade, action = self.one_decision(override_threshold=override_threshold)
        current_market = self.get_current_market()
        if to_trade and self.simulation:
            print(f"Trading. Action: {action}")
            trade_amt, trade_price, executed, description = self.execute_simulted_trade(current_market, action)
            
        elif to_trade and not self.simulation:
            print(f"Trading. Action: {action}")
            trade_amt, trade_price, executed, description = self.execute_real_trade(current_market, action, **kwargs) 
        else:
            print(f"No trade due to threshold decision not being met. pchange < {override_threshold or 1.5}")
            return None
        self.usdc_bal, self.btc_bal = get_free_balance() # update balances 
        current_market['time_now'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_market['trade_executed'] = executed
        current_market['trade_amt'] = trade_amt
        current_market['trade_price'] = trade_price
        current_market['usdc_bal'] = self.usdc_bal
        current_market['btc_bal'] = self.btc_bal
        current_market['description'] = description
        self.update_balance(current_market)
        print(f"balance updated with data {current_market}") 


if __name__ == '__main__':
    import time
    model = TradeModel(simulation=False) # use live data

    options = dict(
        override_threshold = 0.6,
        buffer= 0.005,
        validate = True, # False to submit trades
        min_btc_balance= 0.0005,
        min_usdc_balance = 75,
        max_btc_buy = 0.005,
        max_btc_sell = 0.005,
        volume = 0.0005
    )

    # run simulation
    while True:
        model.run(**options)
        time.sleep(60)
            