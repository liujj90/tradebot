import time
from datetime import datetime, timezone
import pandas as pd
from src.pipeline import get_pair_info
from src.utils import load_yaml

def compute_bid_ask_ratio(ticker_depth, n_records):

    bids = ticker_depth['bids'][:n_records]
    asks = ticker_depth['asks'][:n_records]
    bid_vol = [float(x[0])* float(x[1]) for x in bids]
    ask_vol = [float(x[0])* float(x[1]) for x in asks]

    # Bid Ask ratio 
    ## If bid > ask, you have more people looking to buy at this point 
    bid_ask_ratio = sum(bid_vol)/sum(ask_vol)

    return bid_ask_ratio
    


def compile_ticker_feature(pair="XBTUSDC"):
    
    schema_path = "/home/jj/workspace/src/schema/ticker.yaml"
    schema = load_yaml(schema_path)['kraken_ticker']
    
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    utc_now = datetime.now(timezone.utc) 
    time_since_open = int((utc_now - utc_now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())
    
    ticker_info, ticker_depth = get_pair_info(pair)

    final_data = {
        'snapshot_ts': ts,
        'time_since_open': time_since_open,
        'pair': pair
    }
    
    for column, column_info in schema['columns'].items():
        col_meta = column_info['meta']
        col_data_source = col_meta['api']

        if col_data_source == "Ticker":
            if 'position' not in col_meta.keys(): # open price
                final_data[column] = [float(ticker_info[col_meta['param']])]
            else:
                final_data[column] = [float(ticker_info[col_meta['param']][col_meta['position']])]

        elif col_data_source == "Depth":
            n_records = col_meta['n_records']
            bid_ask_ratio = compute_bid_ask_ratio(ticker_depth, n_records)
            final_data[column] = bid_ask_ratio

        else: 
            pass            
    return pd.DataFrame(final_data)
