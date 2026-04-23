"""
Binance Data Fetcher Module
Handles fetching OHLCV data from Binance for all trading pairs
"""

import ccxt
import pandas as pd
from typing import List, Dict, Optional
import time


class BinanceDataFetcher:
    """
    Professional Binance data fetcher with rate limiting and error handling
    """

    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        self.markets = None
        self.last_fetch_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests

    def load_markets(self) -> Dict:
        """Load all available markets from Binance"""
        try:
            self.markets = self.exchange.load_markets()
            return self.markets
        except Exception as e:
            print(f"Error loading markets: {e}")
            return {}

    def get_all_symbols(self, quote_currency: str = 'USDT', volume_threshold: float = 1000000) -> List[str]:
        """
        Get all symbols with specified quote currency and minimum volume
        
        Args:
            quote_currency: Quote currency (e.g., 'USDT', 'BTC', 'ETH')
            volume_threshold: Minimum 24h volume in quote currency
            
        Returns:
            List of symbol strings (e.g., ['BTC/USDT', 'ETH/USDT'])
        """
        if not self.markets:
            self.load_markets()

        symbols = []
        for symbol, market in self.markets.items():
            if (market.get('quote') == quote_currency and 
                market.get('active', False) and
                not market.get('future', False) and
                not market.get('margin', False)):
                
                # Check volume threshold
                ticker = self.exchange.fetch_ticker(symbol)
                if ticker.get('quoteVolume', 0) >= volume_threshold:
                    symbols.append(symbol)
        
        return sorted(symbols)

    def get_top_symbols_by_volume(self, quote_currency: str = 'USDT', top_n: int = 50) -> List[str]:
        """
        Get top N symbols by 24h trading volume
        
        Args:
            quote_currency: Quote currency
            top_n: Number of top symbols to return
            
        Returns:
            List of symbol strings sorted by volume
        """
        if not self.markets:
            self.load_markets()

        symbol_volumes = []
        for symbol, market in self.markets.items():
            if (market.get('quote') == quote_currency and 
                market.get('active', False) and
                not market.get('future', False)):
                
                try:
                    self._respect_rate_limit()
                    ticker = self.exchange.fetch_ticker(symbol)
                    volume = ticker.get('quoteVolume', 0)
                    if volume > 0:
                        symbol_volumes.append((symbol, volume))
                except Exception:
                    continue

        # Sort by volume descending
        symbol_volumes.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in symbol_volumes[:top_n]]

    def _respect_rate_limit(self):
        """Ensure we respect API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_fetch_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_fetch_time = time.time()

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 200,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (max 1000 for Binance)
            since: Timestamp in milliseconds to start from
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        try:
            self._respect_rate_limit()
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since)
            
            if not ohlcv:
                return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_multiple_timeframes(
        self,
        symbol: str,
        timeframes: List[str] = ['15m', '1h', '4h'],
        limit: int = 200
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple timeframes
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes to fetch
            limit: Number of candles per timeframe
            
        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        data = {}
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            if not df.empty:
                data[tf] = df
        
        return data

    def get_market_tickers(self, quote_currency: str = 'USDT') -> pd.DataFrame:
        """
        Get current tickers for all markets with specified quote currency
        
        Returns:
            DataFrame with ticker information
        """
        if not self.markets:
            self.load_markets()

        tickers_data = []
        
        for symbol, market in self.markets.items():
            if market.get('quote') == quote_currency and market.get('active', False):
                try:
                    self._respect_rate_limit()
                    ticker = self.exchange.fetch_ticker(symbol)
                    
                    tickers_data.append({
                        'symbol': symbol,
                        'price': ticker.get('last'),
                        'change_24h': ticker.get('percentage'),
                        'volume_24h': ticker.get('quoteVolume'),
                        'high_24h': ticker.get('high'),
                        'low_24h': ticker.get('low'),
                        'bid': ticker.get('bid'),
                        'ask': ticker.get('ask')
                    })
                except Exception:
                    continue

        return pd.DataFrame(tickers_data)

    def search_symbols(self, search_term: str) -> List[str]:
        """
        Search for symbols containing a specific term
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching symbols
        """
        if not self.markets:
            self.load_markets()

        matches = []
        search_term = search_term.upper()
        
        for symbol in self.markets.keys():
            if search_term in symbol.upper():
                matches.append(symbol)
        
        return sorted(matches)[:50]  # Limit to 50 results
