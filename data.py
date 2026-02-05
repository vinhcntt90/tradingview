import pandas as pd
import requests
from binance.client import Client
from .config import Config

class DataFetcher:
    def __init__(self):
        self.use_binance_lib = False
        self.client = None
        
        try:
            self.client = Client()
            self.use_binance_lib = True
            print("[*] Binance Client initialized successfully")
        except Exception as e:
            print(f"[!] Failed to init Binance Client: {e}")
            self.use_binance_lib = False

    def fetch_btc_data(self, timeframe='15m', limit=1000):
        """
        Fetch BTC/USDT data from Binance
        Returns DataFrame with index as Datetime
        """
        symbol = 'BTCUSDT'
        print(f"[*] Fetching {symbol} {timeframe} data (limit={limit})...")
        
        try:
            if self.use_binance_lib and self.client:
                # Use official library
                klines = self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'trades', 
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Convert to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                # Add typical price if needed
                df['hl2'] = (df['high'] + df['low']) / 2
                df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
                
                return df
                
            else:
                # Fallback to direct REST API
                base_url = "https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': symbol,
                    'interval': timeframe,
                    'limit': limit
                }
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_asset_volume', 'trades', 
                        'taker_buy_base', 'taker_buy_quote', 'ignore'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                    return df
                else:
                    print(f"[!] API Error: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"[!] Error fetching data: {e}")
            return None

    def fetch_derivatives_data(self):
        """
        Fetch Funding Rate, Open Interest, Long/Short Ratio from Binance Futures
        No API key required - Public endpoints
        """
        data = {
            'funding_rate': None,
            'funding_rate_pct': None,
            'open_interest': None,
            'open_interest_usd': None,
            'long_ratio': None,
            'short_ratio': None,
            'ls_ratio': None,
            'top_trader_ls_ratio': None,
        }
        
        try:
            # 1. Funding Rate
            r = requests.get(
                'https://fapi.binance.com/fapi/v1/fundingRate',
                params={'symbol': 'BTCUSDT', 'limit': 1},
                timeout=10
            )
            if r.status_code == 200:
                fr_data = r.json()[0]
                data['funding_rate'] = float(fr_data['fundingRate'])
                data['funding_rate_pct'] = data['funding_rate'] * 100  # Convert to percentage
                data['mark_price'] = float(fr_data.get('markPrice', 0))
            
            # 2. Open Interest
            r = requests.get(
                'https://fapi.binance.com/fapi/v1/openInterest',
                params={'symbol': 'BTCUSDT'},
                timeout=10
            )
            if r.status_code == 200:
                oi_data = r.json()
                data['open_interest'] = float(oi_data['openInterest'])
                # Estimate USD value
                if data.get('mark_price'):
                    data['open_interest_usd'] = data['open_interest'] * data['mark_price']
            
            # 3. Global Long/Short Ratio (Retail traders)
            r = requests.get(
                'https://fapi.binance.com/futures/data/globalLongShortAccountRatio',
                params={'symbol': 'BTCUSDT', 'period': '1h', 'limit': 1},
                timeout=10
            )
            if r.status_code == 200:
                ls_data = r.json()[0]
                data['long_ratio'] = float(ls_data['longAccount'])
                data['short_ratio'] = float(ls_data['shortAccount'])
                data['ls_ratio'] = float(ls_data['longShortRatio'])
            
            # 4. Top Trader Long/Short Ratio (Whales)
            r = requests.get(
                'https://fapi.binance.com/futures/data/topLongShortAccountRatio',
                params={'symbol': 'BTCUSDT', 'period': '1h', 'limit': 1},
                timeout=10
            )
            if r.status_code == 200:
                top_data = r.json()[0]
                data['top_trader_ls_ratio'] = float(top_data['longShortRatio'])
                data['top_long_ratio'] = float(top_data['longAccount'])
                data['top_short_ratio'] = float(top_data['shortAccount'])
                
        except Exception as e:
            print(f"  [!] Error fetching derivatives data: {e}")
        
        return data

# Global instance
fetcher = DataFetcher()

def get_btc_data(timeframe='15m', limit=1000):
    return fetcher.fetch_btc_data(timeframe, limit)

def get_derivatives_data():
    return fetcher.fetch_derivatives_data()
