import sys
import time
import base64
import hashlib
import hmac
import urllib.request
import json
import requests


def get_private(
    api_method: str = "Balance", 
    api_data: str = "", 
    rel_pth: str = "../"
    ) -> bytes:
    """ Performs API call to get private data from kraken api. 
    docs: https://docs.kraken.com/api/docs/rest-api/

    Args:
        api_method(str): method to use
        api_data(str): api data to include in body parameters. only applicable to certain api_methods. Use format &{param}={value}
        rel_path(str): relative path to config  
    Returns:
        bytes: bytedata of response 
    """
    api_domain = "https://api.kraken.com"
    api_path = "/0/private/"
    api_nonce = str(int(time.time()*1000))
    try:
        api_key = open(f"{rel_pth}API_Public_Key").read().strip()
        api_secret = base64.b64decode(open(f"{rel_pth}API_Private_Key").read().strip())
    except:
        print("API public key and API private (secret) key \
            must be in plain text files called API_Public_Key and API_Private_Key")
        sys.exit(1)
    api_postdata = api_data + "&nonce=" + api_nonce
    api_postdata = api_postdata.encode('utf-8')
    api_sha256 = hashlib.sha256(api_nonce.encode('utf-8') + api_postdata).digest()
    api_hmacsha512 = hmac.new(api_secret, api_path.encode('utf-8') + api_method.encode('utf-8') + api_sha256, hashlib.sha512)
    api_request = urllib.request.Request(api_domain + api_path + api_method, api_postdata)
    api_request.add_header("API-Key", api_key)
    api_request.add_header("API-Sign", base64.b64encode(api_hmacsha512.digest()))
    api_request.add_header("User-Agent", "Kraken REST API")

    api_reply = urllib.request.urlopen(api_request).read()

    return api_reply

def get_pair_info(pair, order_count=500, get_depth=True):
    """ Function to get snapshot of info for currency pair
    """
    base_url = "https://api.kraken.com/0/public"
    payload = {}
    headers = {'Accept': 'application/json'}

    # ticker_info 
    response = requests.get(url = f"{base_url}/Ticker?pair={pair}", headers=headers, data=payload)
    try:
        ticker_info = response.json()['result'][pair]
    except:
        print(response.json())
    # ticker depth: [price, volume, timestamp]
    if get_depth:
        response = requests.get(url = f"{base_url}/Depth?pair={pair}&count={order_count}", headers=headers, data=payload)
        try:
            ticker_depth = response.json()['result'][pair]
        except:
            print(response.json())
    else:
        ticker_depth = None

    return ticker_info, ticker_depth