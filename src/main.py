import sys
sys.path.append('.')
import pandas as pd
from src.utils import conf, pg_engine, load_yaml
from src.pipeline import get_acc_snapshot, compile_ticker_feature


def daily_snapshot():
    """ get and upload function
    """

    try:
        bal_df, trade_df, orders_df = get_acc_snapshot(days=1)
    except AssertionError:
        raise Exception("Error getting and formatting data from API. please check again")

    nrows = pg_engine.write_data(df = bal_df, table = "kraken_acc_balance")
    print(f"uploaded {nrows} rows to kraken_acc_balance")
    nrows = pg_engine.write_data(df = trade_df, table = "kraken_trade_balance")
    print(f"uploaded {nrows} rows to kraken_trade_balance")
    nrows = pg_engine.write_data(df = orders_df, table = "kraken_orders")
    print(f"uploaded {nrows} rows to kraken_orders")

    return True

def ticker_snapshot():
    
    try: 
        snapshot = compile_ticker_feature()
    except Exception as e:
        print(e)
    
    nrows = pg_engine.write_data(df = snapshot, table = 'kraken_ticker', if_exists='append')
    print(f"uploaded {nrows} rows to kraken_ticker")

    return True

if __name__ == "__main__":
    import time
    while True:
        try:
            ticker_snapshot()
        except: 
            pass
        time.sleep(600) # 10 min interval
        