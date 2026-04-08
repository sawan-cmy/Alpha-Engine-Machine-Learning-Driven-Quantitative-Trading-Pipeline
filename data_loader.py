import yfinance as yf
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataLoader:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date

    def fetch_data(self):
        logging.info(f"Fetching data for {len(self.tickers)} tickers from {self.start_date} to {self.end_date}")
        data = yf.download(self.tickers, start=self.start_date, end=self.end_date, progress=False)
        
        # We need 'Close', 'Volume', 'High', and 'Low' for advanced factors
        adj_close = data['Close']
        volume = data['Volume']
        high = data['High']
        low = data['Low']
        
        # Forward fill to prevent look-ahead bias
        adj_close = adj_close.ffill()
        high = high.ffill()
        low = low.ffill()
        volume = volume.ffill().fillna(0)
        
        # Melt to long format
        adj_close_long = adj_close.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Close')
        volume_long = volume.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Volume')
        high_long = high.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='High')
        low_long = low.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Low')
        
        df = pd.merge(adj_close_long, volume_long, on=['Date', 'Ticker'])
        df = pd.merge(df, high_long, on=['Date', 'Ticker'])
        df = pd.merge(df, low_long, on=['Date', 'Ticker'])
        df = df.dropna()  # Drop rows where Close is still NaN (before asset existed)
        df.set_index(['Date', 'Ticker'], inplace=True)
        df.sort_index(inplace=True)
        
        logging.info(f"Data loading complete. Shape: {df.shape}")
        return df
