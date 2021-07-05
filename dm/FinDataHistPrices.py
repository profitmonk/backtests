import datetime  # For datetime objects
import os.path
import numpy as np
import pandas as pd
import requests
from time import sleep

api_key = "3d319882a7d958543097ee3985fafada"

def OHLCdf(tckr):
    data = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/{tckr}?apikey="+ api_key)
    data = data.json()
    
    df = pd.DataFrame(data['historical'])
    df = df.filter(['date', 'open', 'high', 'low', 'close', 'adjClose', 'volume'], axis=1)
    # Backtrader requires column names = Open, High, Low, Close, Adj Close, Volume
    df = df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                                    'adjClose': 'Adj Close', 'volume': 'Volume'})
    df = df.iloc[::-1]
    df.Date = pd.to_datetime(df.Date)
    df = df.set_index('Date')

    return df

    df = OHLCdf('HCHC')