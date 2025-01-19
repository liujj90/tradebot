from src.models.base import TradeDecision
from src.pipeline import get_pair_info, compute_bid_ask_ratio


class DepthDecision(TradeDecision):

    description = ""

    def __init__(self): 
        pass 

    def get_data(self):
        
        ticker_info, ticker_depth = get_pair_info('XBTUSDC')

        # ask_price_50, bid_price_50 = 
        bid_ask_ratio_50 = compute_bid_ask_ratio(ticker_depth, 50)
        bid_ask_ratio_100 = compute_bid_ask_ratio(ticker_depth, 100)
        bid_ask_ratio_500 = compute_bid_ask_ratio(ticker_depth, 500)

        return bid_ask_ratio_50, bid_ask_ratio_100, bid_ask_ratio_500


    def decide(self): # buy, sell, hold

        bar_50, bar_100, bar_500 = self.get_data()

        s =  bar_50 - bar_100 # short term difference 
        l = bar_50 - bar_500 # long term difference
        m = bar_100 - bar_500 # medium term difference

        if s > 0: 
            # buy or sell early
            if l > 0: 
                # sell. a lot of buys lower
                return False, True, False
            elif l < 0: # buy now. 
                return True, False, False
        elif s <= 0: 
            if m < 0: # hold. Price might go up long term
                return False, False, True
            elif m > 0: # sell. Turning point upcoming 
                return False, True, False
            
        