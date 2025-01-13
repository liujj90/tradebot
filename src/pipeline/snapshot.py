import json
import datetime
import time
import pandas as pd

from src.utils import load_yaml
from src.pipeline import get_private


def snapshot_data(
    rel_pth:str = "./", 
    days: int = 1
    ) -> tuple:
    """ get single snapshot of balance, trade balance and open orders
    """
    try:
        balance = json.loads(
            get_private(
            api_method = 'BalanceEx', 
            rel_pth=rel_pth).\
                decode())['result']
        trade_balance = json.loads(
            get_private(
            api_method = 'TradeBalance', 
            api_data="&asset=USDC", 
            rel_pth=rel_pth).\
                decode())['result']
        open_orders = json.loads(get_private(
            api_method="OpenOrders",
            rel_pth=rel_pth
        ).\
            decode())['result']['open']
        # Closed orders require a start date
        tstart = int(time.time() - (86400 * days * 10))
        closed_orders = json.loads(get_private(
            api_method="ClosedOrders", 
            api_data=f"&start={tstart}",
            rel_pth=rel_pth).\
                decode())['result']['closed']


    except Exception as e:
        print(e)
        balance, trade_balance, open_orders, closed_orders = None, None, None, None
   
    return balance, trade_balance, open_orders, closed_orders



def _format_order(
    order_data: dict, 
    schema: dict, 
    date: str, 
    timestamp: str, 
    dt_cols: list = ['period_id', 'snapshot_ts']
    ) -> pd.DataFrame:
    """ Format order data frame from schema and order data
    """
    
    all_oo_cols = list(schema['kraken_orders']['columns'].keys())
    df_dict = {k:[] for k in all_oo_cols if k not in dt_cols}
    desc_cols = ['pair', 'type', 'ordertype', 'price', 'price2', 'order_description', 'close']
    non_desc_cols = [c for c in df_dict.keys() if c not in desc_cols]
    
    for key, value in order_data.items():
        df_dict['order_id'].append(key)
        desc = value['descr']
        # rename order column due to db limitation
        desc['order_description'] = desc['order']
        for col in desc_cols: 
            df_dict[col].append(desc[col])
        for col in non_desc_cols:
            if col in value.keys():
                df_dict[col].append(value[col])
    oo_df = pd.DataFrame(df_dict)
    oo_df['period_id'] = date
    oo_df['snapshot_ts'] = timestamp
    oo_df = oo_df[all_oo_cols]

    return oo_df


def format_acc_snapshot(
    balance: dict, 
    trade_balance: dict, 
    open_orders: dict, 
    closed_orders: dict
    ) -> tuple:
    """ Format one account snapshot 
    """
    schema = load_yaml(filepath="/home/jj/workspace/src/schema/snapshot.yaml")
    ts = datetime.datetime.now()
    timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
    date = ts.strftime("%Y-%m-%d")
    dt_cols = ['period_id', 'snapshot_ts']
    # Balance
    balance_cols = [k for k,v in schema['kraken_acc_balance']['columns'].items()]
    bal_df = pd.DataFrame(balance).T.reset_index(names = "currency")
    bal_df['period_id'] = date
    bal_df['snapshot_ts'] = timestamp
    bal_df = bal_df[balance_cols]

    # Trade Balance
    tb_cols = [k for k,v in schema['kraken_trade_balance']['columns'].items()]
    tb_cols_nodate = [x for x in tb_cols if x not in dt_cols]
    tb_df = pd.DataFrame(trade_balance, index=[0])
    tb_df.columns = tb_cols_nodate
    tb_df['period_id'] = date
    tb_df['snapshot_ts'] = timestamp
    tb_df = tb_df[tb_cols]

    # open_orders
    oo_df = _format_order(open_orders, schema, date, timestamp)

    # closed_orders
    co_df = _format_order(closed_orders, schema, date, timestamp)
    
    # Combine orders
    orders_df = pd.concat([oo_df, co_df])
    
    return bal_df, tb_df, orders_df
    
def get_acc_snapshot(days=1):
    """ main function to get snapshot data
    """
    
    balance, trade_balance, open_orders, closed_orders = snapshot_data(days=days)

    assert all([
        balance is not None, 
        trade_balance is not None, 
        open_orders is not None, 
        closed_orders is not None])
    
    bal_df, trade_df, orders_df = format_acc_snapshot(balance, trade_balance, open_orders, closed_orders)

    return bal_df, trade_df, orders_df

