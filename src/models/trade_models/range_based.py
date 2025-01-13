from datetime import datetime, timedelta

from src.utils import pg_engine
from src.models.base import TradeDecision

class PercentileDecision(TradeDecision):

    description = "Sets trade decision if interquartile price variation "\
        "above threshold based on percentile "\
        "over last 24h. Default 1.5%"

    def __init__(self, threshold=1.5):
        self.threshold=threshold

    def get_data(self): 
        ## get 24h of data and calculate interquantile range
        
        t = (datetime.now() - timedelta(hours = 24)).strftime("%Y-%m-%d %H:%M:%S")
        query = f"""
        select last_trade_closed
        from kraken_ticker
        where snapshot_ts > '{t}'
        """

        res = pg_engine.query_data(query)

        median = res.last_trade_closed.quantile(q = 0.5)
        q25 = res.last_trade_closed.quantile(q = .25)
        q75 = res.last_trade_closed.quantile(q = .75)
        qrange = q75 - q25
        
        ans = qrange/median * 100 # TODO: decide if denom should be median or current price 
        print(f"Median: {median}, q25: {q25}, q75: {q75}, qrange: {qrange}, pchange: {ans}")
        return ans 
    
    def decide(self, override_threshold=None):

        if override_threshold:
            self.threshold = override_threshold

        variance = self.get_data()

        if variance > self.threshold: 
            print(f"variance {variance} above threshold {self.threshold}. Trade decision: True")
            return True 
        
        else:
            return False


    