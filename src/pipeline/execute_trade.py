import sys
sys.path.append('.')
import json
from src.pipeline import get_private, get_acc_snapshot

from uuid import uuid4
 


def execute_trade_with_buffer(
        trade_type,
        trade_amt,
        pair,
        price,
        order_type="limit",
        # validate=True, # does not submit trade
        rel_pth = "./",
        fees = 0.025/100,
        # buffer=0.01, # Buffer size 
        **kwargs
    ):
    buffer = kwargs.get("buffer", 0.01)
    validate = kwargs.get("validate", True)

    if trade_type == "buy":
        price = (1-buffer) * price
        
    elif trade_type == "sell":
        price = (1+buffer) * price

    api_data =  dict(
        ordertype = order_type,
        type = trade_type,
        volume = trade_amt,
        pair = pair,
        price = round(price, 2),
        validate=validate,
        cl_ord_id=str(uuid4())
        )

    revised_api_data = validate_order(api_data, fees=fees, **kwargs)

    if isinstance(revised_api_data, bool):
        return(revised_api_data, "order rejected")


    else:
        api_postdata = ""
        for k,v in revised_api_data.items():
            api_postdata += f"&{k}={v}"
        

        response = get_private(api_method="AddOrder", api_data = api_postdata, rel_pth=rel_pth)

        print(response.decode())

        try:
            final_response = json.loads(response.decode())
        except: 
            
            final_response = response


        return revised_api_data, final_response


def get_free_balance():
    bal_df, _, _ = get_acc_snapshot()
    bal_df['balance'] = bal_df['balance'].astype(float)
    bal_df['hold_trade'] = bal_df['hold_trade'].astype(float)

    bal_df['free_balance'] = bal_df['balance'] - bal_df['hold_trade']

    free_usdc_bal = bal_df.loc[bal_df['currency'] == "USDC", 'free_balance'].values[0]
    free_btc_bal = bal_df.loc[bal_df['currency'] == "XXBT", 'free_balance'].values[0]
    return free_usdc_bal, free_btc_bal


def validate_order(
        order, 
        fee = 0.025*100,
        **kwargs):

    min_btc_balance= kwargs.get("min_btc_balance", 0.0005)
    min_usdc_balance = kwargs.get("min_usdc_balance", 75)
    max_btc_buy = kwargs.get("max_btc_buy", 0.005)
    max_btc_sell = kwargs.get("max_btc_sell", 0.005)
    

    # This only looks at btc usdc
    assert order['pair'] == "XBTUSDC"

    # get free balance  
    free_usdc_bal, free_btc_bal = get_free_balance()
    
    # bal_df, _, _ = get_acc_snapshot()
    # bal_df['balance'] = bal_df['balance'].astype(float)
    # bal_df['hold_trade'] = bal_df['hold_trade'].astype(float)
    # bal_df['free_balance'] = bal_df['balance'] - bal_df['hold_trade']
    # free_usdc_bal = bal_df.loc[bal_df['currency'] == "USDC", 'free_balance'].values[0]
    # free_btc_bal = bal_df.loc[bal_df['currency'] == "XXBT", 'free_balance'].values[0]

    # check if it can accomodate this order
    # check if order meets min balance, else adjust order
    if order['type'] == "sell": # sell btc, gain usdc 
        if free_btc_bal <= min_btc_balance:
            print(f'free btc bal: {free_btc_bal} lower than minimum: {min_btc_balance}')
            return False 
        order_usdc = order['price'] * order['volume']
        after_order_usdc = free_usdc_bal + order_usdc - fee*order_usdc
        after_order_btc =  free_btc_bal - order['volume']

        if (after_order_btc <= min_btc_balance) or (order['volume'] > max_btc_sell):
            diff = free_btc_bal - min_btc_balance
            adjusted_volume = min(round(float(diff), 10), max_btc_sell)
            print(adjusted_volume)
            # change volume
            print(f"original sell order of {order['volume']} btc too high. Adjusting Sell order to: {adjusted_volume}")
            
            order['volume'] = adjusted_volume
            print(order)
        
        return order

    elif  order['type'] == "buy":
        if free_usdc_bal <= min_usdc_balance:
            print(f'free usdc bal: {free_usdc_bal} lower than minimum: {min_usdc_balance}')
            return False
        order_usdc = order['price'] * order['volume']
        after_order_usdc = free_usdc_bal - order_usdc - fee*order_usdc
        after_order_btc =  free_btc_bal + order['volume']

        if (after_order_usdc <= min_usdc_balance) or (order['volume'] > max_btc_buy):
            diff = free_usdc_bal - min_usdc_balance
            adjusted_volume = min(round(float(diff/order['price']), 10), max_btc_buy)
            print(adjusted_volume)
            # change volume
            print(f"original buy order of {order['volume']} btc too high. Adjusting Buy order to: {adjusted_volume}")
            
            order['volume'] = adjusted_volume
            print(order)
        
        return order

    else:
        print("unsupported order type")
        return False
    

    

if __name__=="__main__":

    options = dict(
        buffer= 0.005,
        validate = True,
        min_btc_balance= 0.0005,
        min_usdc_balance = 75,
        max_btc_buy = 0.005,
        max_btc_sell = 0.005,
    )
    
    order_details, response = execute_trade_with_buffer(
        trade_type = "buy",
        volume = 0.1,
        pair = "XBTUSDC",
        price = 110_000,
        order_type = "limit",
        # validate = True,
        rel_pth = './',
        **options
        # buffer= 0.005
    )
    print(response)
    print(order_details)