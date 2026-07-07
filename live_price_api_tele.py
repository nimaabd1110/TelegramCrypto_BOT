
import requests
import datetime


from coin_dic import coins

class PriceManager :
    def __init__(self):
        pass




    def get_crypto_price(self,coin_name):

        self.coin_name = coin_name
        coin_name1 = coin_name.strip().lower()
        symbol = coins.get(coin_name1)
        binance_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

        try :
            get_data = requests.get(binance_url,  timeout=10)
            get_data.raise_for_status()
            data = get_data.json()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            crypto_price = float(data["price"])
            crypto_symbol = data["symbol"]
            return {"success" : True, "crypto_price" : crypto_price,"crypto_symbol" : crypto_symbol,"exact_time" : current_time}

        except Exception as e:
            return {"success" : False, "error" : str(e)}




















