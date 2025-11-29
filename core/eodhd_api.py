
import requests, pandas as pd

class EODHDClient:
    BASE="https://eodhd.com/api"
    API_KEY="demo"

    def get_ohlc(self, ticker):
        url=f"{self.BASE}/eod/{ticker}?api_token={self.API_KEY}&fmt=json"
        r=requests.get(url)
        if r.status_code!=200:
            return None
        data=r.json()
        df=pd.DataFrame(data)
        if "date" in df:
            df["date"]=pd.to_datetime(df["date"])
        return df
