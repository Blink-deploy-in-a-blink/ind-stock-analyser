#!/usr/bin/env python3
"""
Clean NSE Data Fetcher
Based on proven working NSE Option Chain Analyzer
Real implementation to fetch data from official NSE API sources
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class NSEDataFetcher:
    """Clean NSE data fetcher using proven API endpoints"""
    
    # Known NSE F&O index symbols
    INDEX_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50']
    
    def __init__(self):
        # Proven URLs from working analyzer
        self.url_oc = "https://www.nseindia.com/option-chain"
        self.url_index = "https://www.nseindia.com/api/option-chain-indices?symbol="
        self.url_stock = "https://www.nseindia.com/api/option-chain-equities?symbol="
        self.url_symbols = "https://www.nseindia.com/api/underlying-information"
        
        # Proven headers from working analyzer
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'
        }
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.cookies = {}
        self._session_initialized = False
        
        # Initialize session by getting cookies
        self._init_session()
    
    def _init_session(self):
        """Initialize session with NSE Option Chain page to get cookies"""
        try:
            print("📡 Initializing NSE session...")
            
            request = self.session.get(self.url_oc, headers=self.headers, timeout=10)
            self.cookies = dict(request.cookies)
            
            if request.status_code == 200 and self.cookies:
                print("✅ NSE session initialized with cookies")
                self._session_initialized = True
                return True
            elif request.status_code == 200:
                print("⚠️  NSE returned 200 but no cookies received")
                self._session_initialized = True
                return True
            else:
                print(f"⚠️  NSE session returned {request.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to NSE - check internet connection")
            self.cookies = {}
            return False
        except requests.exceptions.Timeout:
            print("⚠️  NSE session initialization timed out")
            self.cookies = {}
            return False
        except Exception as e:
            print(f"⚠️  NSE session initialization error: {str(e)}")
            self.cookies = {}
            return False
    
    def _refresh_session(self):
        """Refresh session cookies when needed"""
        try:
            print("🔄 Refreshing NSE session...")
            request = self.session.get(self.url_oc, headers=self.headers, timeout=10)
            self.cookies = dict(request.cookies)
            if self.cookies:
                print("✅ Session cookies refreshed")
                self._session_initialized = True
            else:
                print("⚠️  Session refresh returned no cookies")
        except Exception as e:
            print(f"⚠️  Failed to refresh session: {str(e)}")
            self.cookies = {}
    
    def _request_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and exponential backoff"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url, headers=self.headers, timeout=10, cookies=self.cookies
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    print(f"🔄 Session expired (attempt {attempt + 1}), refreshing...")
                    self._refresh_session()
                elif response.status_code == 403:
                    print(f"⚠️  Access forbidden (attempt {attempt + 1}) - may be rate limited")
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                    self._refresh_session()
                elif response.status_code == 429:
                    wait_time = 2 ** (attempt + 2)  # Longer wait for rate limits
                    print(f"⚠️  Rate limited (attempt {attempt + 1}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️  NSE API returned {response.status_code} (attempt {attempt + 1})")
                    
            except requests.exceptions.Timeout:
                wait_time = 2 ** attempt
                print(f"⚠️  Request timeout (attempt {attempt + 1}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            except requests.exceptions.ConnectionError:
                print(f"⚠️  Connection error (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"⚠️  Request error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def get_symbols(self) -> Dict[str, List[str]]:
        """
        Get list of available indices and stocks from NSE using proven API
        
        API: https://www.nseindia.com/api/underlying-information
        Returns: Dict with 'indices' and 'stocks' lists
        """
        try:
            response = self._request_with_retry(self.url_symbols)
            
            if response and response.status_code == 200:
                json_data = response.json()
                
                data = json_data.get('data', {})
                index_list = data.get('IndexList', [])
                underlying_list = data.get('UnderlyingList', [])
                
                indices = [item.get('symbol', '') for item in index_list if item.get('symbol')]
                stocks = [item.get('symbol', '') for item in underlying_list if item.get('symbol')]
                
                print(f"✅ Fetched {len(indices)} indices and {len(stocks)} stocks")
                return {
                    'indices': indices,
                    'stocks': stocks
                }
            else:
                print(f"⚠️  Failed to fetch symbols from NSE")
                return {'indices': [], 'stocks': []}
                
        except Exception as e:
            print(f"❌ Error fetching symbols: {str(e)}")
            return {'indices': [], 'stocks': []}
    
    def get_option_chain(self, symbol: str) -> Optional[Dict]:
        """
        Get option chain data using proven NSE API endpoints
        
        API: https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY (for indices)
             https://www.nseindia.com/api/option-chain-equities?symbol=RELIANCE (for stocks)
        Method: Direct JSON API call with session cookies
        Data: Complete option chain with CE/PE data, underlying price, volumes
        Cost: FREE - official NSE API
        """
        try:
            # Validate and normalize symbol
            if not symbol or not symbol.strip():
                print(f"❌ Invalid symbol: '{symbol}'")
                return None
            
            symbol = symbol.strip().upper()
            
            # Determine if symbol is index or stock
            is_index = symbol in self.INDEX_SYMBOLS
            
            # Use appropriate API endpoint
            if is_index:
                url = f"{self.url_index}{symbol}"
            else:
                url = f"{self.url_stock}{symbol}"
            
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            
            # Make API request with retry logic
            response = self._request_with_retry(url)
            
            if response and response.status_code == 200:
                json_data = response.json()
                
                # Validate response structure
                records = json_data.get('records', {})
                if records and 'data' in records:
                    num_strikes = len(records['data'])
                    print(f"✅ Fetched option chain for {symbol} with {num_strikes} strikes")
                    return json_data
                else:
                    print(f"⚠️  Invalid option chain response structure for {symbol}")
                    return None
            else:
                print(f"⚠️  Could not fetch option chain for {symbol}")
                return None
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in option chain response for {symbol}")
            return None
        except Exception as e:
            print(f"❌ Error fetching option chain for {symbol}: {str(e)}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time stock quote from NSE using option chain API
        
        Method: Extract underlying price from option chain data (proven method)
        Data: Last price, underlying value from option chain API
        Cost: FREE - official NSE API
        """
        try:
            # Get option chain data which contains underlying price (proven method)
            option_data = self.get_option_chain(symbol)
            
            if option_data and 'records' in option_data:
                records = option_data['records']
                
                # Method 1: Get underlying value directly from records (proven extraction)
                if 'underlyingValue' in records and records['underlyingValue'] > 0:
                    underlying_value = records['underlyingValue']
                    quote = {
                        'symbol': symbol,
                        'lastPrice': underlying_value,
                        'underlyingValue': underlying_value,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'NSE_API'
                    }
                    print(f"✅ Fetched quote for {symbol}: ₹{underlying_value}")
                    return quote
                
                # Method 2: Extract from first valid data record (proven fallback)
                if 'data' in records and records['data']:
                    for record in records['data']:
                        # Check PE side for underlying value
                        if 'PE' in record and 'underlyingValue' in record['PE']:
                            underlying_value = record['PE']['underlyingValue']
                            if underlying_value > 0:
                                quote = {
                                    'symbol': symbol,
                                    'lastPrice': underlying_value,
                                    'underlyingValue': underlying_value,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'NSE_API'
                                }
                                print(f"✅ Fetched quote for {symbol}: ₹{underlying_value}")
                                return quote
                        
                        # Check CE side for underlying value
                        if 'CE' in record and 'underlyingValue' in record['CE']:
                            underlying_value = record['CE']['underlyingValue']
                            if underlying_value > 0:
                                quote = {
                                    'symbol': symbol,
                                    'lastPrice': underlying_value,
                                    'underlyingValue': underlying_value,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'NSE_API'
                                }
                                print(f"✅ Fetched quote for {symbol}: ₹{underlying_value}")
                                return quote
                            
                print(f"⚠️  Could not extract underlying price for {symbol}")
                return None
            else:
                print(f"⚠️  No valid option chain data for {symbol}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching quote for {symbol}: {str(e)}")
            return None
    
    def get_option_data_for_analysis(self, symbol: str, expiry_date: str = None) -> Optional[Dict]:
        """
        Get formatted option data for market analysis
        
        Returns: Formatted data ready for strategy analysis
        """
        try:
            option_chain = self.get_option_chain(symbol)
            
            if not option_chain or 'records' not in option_chain:
                return None
            
            records = option_chain['records']
            
            # Get underlying price
            underlying_price = records.get('underlyingValue', 0)
            if underlying_price == 0:
                # Try to extract from data records
                for record in records.get('data', []):
                    if 'PE' in record and 'underlyingValue' in record['PE']:
                        underlying_price = record['PE']['underlyingValue']
                        if underlying_price > 0:
                            break
            
            # Get expiry dates
            expiry_dates = records.get('expiryDates', [])
            if not expiry_date and expiry_dates:
                expiry_date = expiry_dates[0]  # Use nearest expiry
            
            # Filter data for specific expiry
            filtered_data = []
            for record in records.get('data', []):
                ce_data = record.get('CE', {})
                pe_data = record.get('PE', {})
                
                # Check if this record matches our expiry
                ce_expiry = ce_data.get('expiryDate', '')
                pe_expiry = pe_data.get('expiryDate', '')
                
                if expiry_date and (ce_expiry == expiry_date or pe_expiry == expiry_date):
                    filtered_data.append(record)
                elif not expiry_date:  # Include all if no specific expiry requested
                    filtered_data.append(record)
            
            analysis_data = {
                'symbol': symbol,
                'underlying_price': underlying_price,
                'expiry_date': expiry_date,
                'expiry_dates': expiry_dates,
                'option_chain': filtered_data,
                'timestamp': datetime.now().isoformat(),
                'total_strikes': len(filtered_data),
                'source': 'NSE_API'
            }
            
            print(f"✅ Prepared option analysis data for {symbol}: {len(filtered_data)} strikes")
            return analysis_data
            
        except Exception as e:
            print(f"❌ Error preparing option analysis data for {symbol}: {str(e)}")
            return None