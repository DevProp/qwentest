"""
Binance Data Fetcher Module
Handles fetching OHLCV data from Binance for all trading pairs
Optimized for speed with parallel processing and intelligent caching
"""

import ccxt
import pandas as pd
from typing import List, Dict, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class BinanceDataFetcher:
    """
    Professional Binance data fetcher with rate limiting, error handling, and parallel processing
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
        self.rate_limit_delay = 0.05  # 50ms between requests for faster scanning
        self._lock = threading.Lock()
        self._ticker_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 60  # Cache tickers for 60 seconds
        
        # Pre-load markets on initialization
        try:
            self.load_markets()
        except Exception:
            pass

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
        Get top N symbols by 24h trading volume using cached data for speed
        
        Args:
            quote_currency: Quote currency
            top_n: Number of top symbols to return
            
        Returns:
            List of symbol strings sorted by volume
        """
        if not self.markets:
            self.load_markets()

        # Check cache first
        current_time = time.time()
        cache_key = f"{quote_currency}_volume"
        
        with self._lock:
            if (cache_key in self._ticker_cache and 
                current_time - self._cache_timestamp < self._cache_ttl):
                cached_data = self._ticker_cache[cache_key]
                cached_data.sort(key=lambda x: x[1], reverse=True)
                return [s[0] for s in cached_data[:top_n]]
        
        symbol_volumes = []
        
        # Use ThreadPoolExecutor for parallel fetching
        def fetch_ticker(symbol):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                volume = ticker.get('quoteVolume', 0)
                return (symbol, volume) if volume > 0 else None
            except Exception:
                return None
        
        # Filter valid symbols first
        valid_symbols = [
            symbol for symbol, market in self.markets.items()
            if (market.get('quote') == quote_currency and 
                market.get('active', False) and
                not market.get('future', False))
        ]
        
        # Fetch tickers in parallel batches
        batch_size = 20
        all_results = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i in range(0, len(valid_symbols), batch_size):
                batch = valid_symbols[i:i+batch_size]
                futures = {executor.submit(fetch_ticker, sym): sym for sym in batch}
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            all_results.append(result)
                    except Exception:
                        continue
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(valid_symbols):
                    time.sleep(0.1)
        
        # Cache results
        with self._lock:
            self._ticker_cache[cache_key] = all_results
            self._cache_timestamp = current_time
        
        # Sort by volume descending
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in all_results[:top_n]]

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
