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
        
        # Initialize session by getting cookies
        self._init_session()
    
    def _init_session(self):
        """Initialize session with NSE Option Chain page to get cookies (proven method)"""
        try:
            print("📡 Initializing NSE session...")
            
            # Visit option-chain page to get cookies (proven working method)
            request = self.session.get(self.url_oc, headers=self.headers, timeout=5)
            self.cookies = dict(request.cookies)
            
            if request.status_code == 200:
                print("✅ NSE session initialized with cookies")
                return True
            else:
                print(f"⚠️  NSE session returned {request.status_code}")
                return True  # Continue anyway
                
        except Exception as e:
            print(f"⚠️  NSE session initialization error: {str(e)}")
            self.cookies = {}
            return True
    
    def _refresh_session(self):
        """Refresh session cookies when needed"""
        try:
            print("🔄 Refreshing NSE session...")
            request = self.session.get(self.url_oc, headers=self.headers, timeout=5)
            self.cookies = dict(request.cookies)
            print("✅ Session cookies refreshed")
        except Exception as e:
            print(f"⚠️  Failed to refresh session: {str(e)}")
            self.cookies = {}
    
    def get_symbols(self) -> Dict[str, List[str]]:
        """
        Get list of available indices and stocks from NSE using proven API
        
        API: https://www.nseindia.com/api/underlying-information
        Returns: Dict with 'indices' and 'stocks' lists
        """
        try:
            response = self.session.get(self.url_symbols, headers=self.headers, timeout=5, cookies=self.cookies)
            
            if response.status_code == 200:
                json_data = response.json()
                
                indices = [item['symbol'] for item in json_data['data']['IndexList']]
                stocks = [item['symbol'] for item in json_data['data']['UnderlyingList']]
                
                print(f"✅ Fetched {len(indices)} indices and {len(stocks)} stocks")
                return {
                    'indices': indices,
                    'stocks': stocks
                }
            else:
                print(f"⚠️  Failed to fetch symbols: {response.status_code}")
                return {'indices': [], 'stocks': []}
                
        except Exception as e:
            print(f"❌ Error fetching symbols: {str(e)}")
            return {'indices': [], 'stocks': []}
    
    def get_option_chain(self, symbol: str) -> Optional[Dict]:
        """
        Get option chain data using proven NSE API endpoints
        
        API: https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY (for indices)
             https://www.nseindia.com/api/option-chain-equities?symbol=RELIANCE (for stocks)
        Method: Direct JSON API call with session cookies (proven working method)
        Data: Complete option chain with CE/PE data, underlying price, volumes
        Cost: FREE - official NSE API
        """
        try:
            # Determine if symbol is index or stock (proven detection method)
            indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50']
            is_index = symbol.upper() in indices
            
            # Use appropriate API endpoint (proven URLs)
            if is_index:
                url = f"{self.url_index}{symbol}"
            else:
                url = f"{self.url_stock}{symbol}"
            
            # Add delay to avoid rate limiting (proven timing)
            time.sleep(0.5)
            
            # Make API request with cookies (proven method)
            response = self.session.get(url, headers=self.headers, timeout=10, cookies=self.cookies)
            
            # Handle 401 (unauthorized) by refreshing session (proven error handling)
            if response.status_code == 401:
                print("🔄 Session expired, refreshing cookies...")
                self._refresh_session()
                response = self.session.get(url, headers=self.headers, timeout=10, cookies=self.cookies)
            
            if response.status_code == 200:
                json_data = response.json()
                
                # Validate response structure (proven validation)
                if 'records' in json_data and 'data' in json_data['records']:
                    num_strikes = len(json_data['records']['data'])
                    print(f"✅ Fetched option chain for {symbol} with {num_strikes} strikes")
                    return json_data
                else:
                    print(f"⚠️  Invalid option chain response structure for {symbol}")
                    return None
            else:
                print(f"⚠️  NSE API returned {response.status_code} for {symbol}")
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