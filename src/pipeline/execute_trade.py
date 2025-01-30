import sys
sys.path.append('.')
from src.pipeline import get_private, get_acc_snapshot

from uuid import uuid4
 


def execute_trade_with_buffer(
        trade_type,
        volume,
        pair,
        price,
        order_type="limit",
        validate=True, # does not submit trade
        rel_pth = "./",
        buffer=0.01
    ):

    if trade_type == "buy":
        price = (1-buffer) * price
        
    elif trade_type == "sell":
        price = (1+buffer) * price

    api_data =  dict(
        ordertype = order_type,
        type = trade_type,
        volume = volume,
        pair = pair,
        price = price,
        validate=validate,
        cl_ord_id=str(uuid4())
        )

    revised_api_data = validate_order(api_data)

    if isinstance(revised_api_data, bool):
        return("order rejected")


    else:
        api_postdata = ""
        for k,v in revised_api_data.items():
            api_postdata += f"&{k}={v}"
        

        response = get_private(api_method="AddOrder", api_data = api_postdata, rel_pth=rel_pth)

        return response.decode()


def validate_order(
        order, 
        min_btc_balance=0.0005, 
        min_usdc_balance = 75,
        max_btc_buy = 0.005,
        max_btc_sell = 0.005, 
        fee = 0.25/100):

    # This only looks at btc usdc
    assert order['pair'] == "XBTUSDC"

    # get free balance  
    bal_df, _, _ = get_acc_snapshot()

    bal_df['balance'] = bal_df['balance'].astype(float)
    bal_df['hold_trade'] = bal_df['hold_trade'].astype(float)

    bal_df['free_balance'] = bal_df['balance'] - bal_df['hold_trade']

    free_usdc_bal = bal_df.loc[bal_df['currency'] == "USDC", 'free_balance'].values[0]
    free_btc_bal = bal_df.loc[bal_df['currency'] == "XXBT", 'free_balance'].values[0]

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
    

    

if __name__=="__main__":
    
    response = execute_trade_with_buffer(
        trade_type = "sell",
        volume = 0.1,
        pair = "XBTUSDC",
        price = 110_000,
        order_type = "limit",
        validate = True,
        rel_pth = './',
        buffer= 0.005
    )
    print(response)