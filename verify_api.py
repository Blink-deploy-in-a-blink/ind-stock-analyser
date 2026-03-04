#!/usr/bin/env python3
"""
Live API Verification Script
Run this to test if all API connections are working properly.
Usage: python verify_api.py [SYMBOL]
"""

import sys
import time
import json
import requests
from datetime import datetime


def test_nse_session():
    """Test NSE session initialization and cookie retrieval"""
    print("=" * 60)
    print("TEST 1: NSE Session Initialization")
    print("=" * 60)
    
    session = requests.Session()
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'accept-language': 'en,gu;q=0.9,hi;q=0.8',
        'accept-encoding': 'gzip, deflate, br'
    }
    session.headers.update(headers)
    
    try:
        r = session.get('https://www.nseindia.com/option-chain', headers=headers, timeout=10)
        cookies = dict(r.cookies)
        print(f"  Status: {r.status_code}")
        print(f"  Cookies obtained: {len(cookies)}")
        if cookies:
            print(f"  Cookie names: {list(cookies.keys())}")
            print("  ✅ PASS: NSE session initialized successfully")
            return session, cookies, True
        else:
            print("  ⚠️  WARN: No cookies received (may still work)")
            return session, cookies, True
    except requests.exceptions.ConnectionError:
        print("  ❌ FAIL: Cannot connect to NSE - check internet connection")
        return None, {}, False
    except requests.exceptions.Timeout:
        print("  ❌ FAIL: Connection timed out")
        return None, {}, False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return None, {}, False


def test_nse_option_chain(session, cookies, symbol='RELIANCE', is_index=False):
    """Test NSE option chain API"""
    print(f"\n{'=' * 60}")
    print(f"TEST 2: NSE Option Chain - {symbol} ({'index' if is_index else 'stock'})")
    print(f"{'=' * 60}")
    
    if not session:
        print("  ⚠️  SKIP: No session available")
        return False
    
    time.sleep(1)
    
    try:
        if is_index:
            url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
        else:
            url = f'https://www.nseindia.com/api/option-chain-equities?symbol={symbol}'
        
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'accept-language': 'en,gu;q=0.9,hi;q=0.8',
            'accept-encoding': 'gzip, deflate, br'
        }
        
        r = session.get(url, headers=headers, timeout=10, cookies=cookies)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            records = data.get('records', {})
            underlying = records.get('underlyingValue', 'N/A')
            expiry_dates = records.get('expiryDates', [])
            strikes = records.get('data', [])
            
            print(f"  Underlying Price: ₹{underlying}")
            print(f"  Expiry Dates: {expiry_dates[:3]}{'...' if len(expiry_dates) > 3 else ''}")
            print(f"  Total Strikes: {len(strikes)}")
            
            if strikes:
                first = strikes[0]
                print(f"  First Strike: {first.get('strikePrice', 'N/A')}")
                print(f"  Has CE data: {'CE' in first}")
                print(f"  Has PE data: {'PE' in first}")
                
                # Check data quality
                ce_with_data = sum(1 for s in strikes if s.get('CE', {}).get('lastPrice', 0) > 0)
                pe_with_data = sum(1 for s in strikes if s.get('PE', {}).get('lastPrice', 0) > 0)
                print(f"  Strikes with CE prices: {ce_with_data}/{len(strikes)}")
                print(f"  Strikes with PE prices: {pe_with_data}/{len(strikes)}")
            
            print(f"  ✅ PASS: Option chain data retrieved successfully")
            return True
        elif r.status_code == 401:
            print("  ❌ FAIL: Unauthorized - session cookies expired")
            return False
        elif r.status_code == 403:
            print("  ❌ FAIL: Forbidden - may be rate limited or blocked")
            return False
        else:
            print(f"  ❌ FAIL: Unexpected status code {r.status_code}")
            return False
            
    except json.JSONDecodeError:
        print("  ❌ FAIL: Invalid JSON response")
        return False
    except requests.exceptions.ConnectionError:
        print("  ❌ FAIL: Cannot connect to NSE")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False


def test_yahoo_finance(symbol='RELIANCE'):
    """Test Yahoo Finance chart API"""
    print(f"\n{'=' * 60}")
    print(f"TEST 3: Yahoo Finance - {symbol}.NS")
    print(f"{'=' * 60}")
    
    try:
        end_date = int(time.time())
        start_date = end_date - (30 * 24 * 60 * 60)
        
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS'
        params = {'period1': start_date, 'period2': end_date, 'interval': '1d'}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        r = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            result = data.get('chart', {}).get('result', [])
            
            if result:
                meta = result[0].get('meta', {})
                print(f"  Symbol: {meta.get('symbol', 'N/A')}")
                print(f"  Currency: {meta.get('currency', 'N/A')}")
                print(f"  Regular Market Price: ₹{meta.get('regularMarketPrice', 'N/A')}")
                print(f"  Exchange: {meta.get('exchangeName', 'N/A')}")
                
                timestamps = result[0].get('timestamp', [])
                print(f"  Data Points: {len(timestamps)}")
                
                indicators = result[0].get('indicators', {})
                quote = indicators.get('quote', [{}])[0]
                closes = [c for c in quote.get('close', []) if c is not None]
                if closes:
                    print(f"  Latest Close: ₹{closes[-1]:.2f}")
                    print(f"  30d Range: ₹{min(closes):.2f} - ₹{max(closes):.2f}")
                
                print(f"  ✅ PASS: Yahoo Finance data retrieved successfully")
                return True
            else:
                print("  ❌ FAIL: No result data in response")
                return False
        else:
            print(f"  ❌ FAIL: HTTP {r.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ❌ FAIL: Cannot connect to Yahoo Finance")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False


def test_google_news(symbol='RELIANCE'):
    """Test Google News search"""
    print(f"\n{'=' * 60}")
    print(f"TEST 4: Google News - {symbol}")
    print(f"{'=' * 60}")
    
    try:
        from bs4 import BeautifulSoup
        
        url = f'https://www.google.com/search?q={symbol}+stock+news+india&tbm=nws&hl=en'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        r = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Try multiple strategies
            strategies_tried = []
            articles = []
            
            # Strategy 1
            h1 = soup.find_all('div', class_='SoaBEf')
            strategies_tried.append(f"SoaBEf class: {len(h1)} results")
            for h in h1[:3]:
                title_elem = h.find('div', class_='MBeuO')
                if title_elem:
                    articles.append(title_elem.get_text())
            
            # Strategy 2
            h2 = soup.find_all('div', {'role': 'heading'})
            strategies_tried.append(f"role=heading: {len(h2)} results")
            if not articles:
                for h in h2[:5]:
                    text = h.get_text().strip()
                    if len(text) > 20:
                        articles.append(text)
            
            # Strategy 3
            h3 = soup.find_all('h3')
            strategies_tried.append(f"h3 tags: {len(h3)} results")
            if not articles:
                for h in h3[:5]:
                    text = h.get_text().strip()
                    if len(text) > 20:
                        articles.append(text)
            
            print(f"  Strategies tried: {strategies_tried}")
            print(f"  Headlines found: {len(articles)}")
            for i, article in enumerate(articles[:3]):
                print(f"    {i+1}. {article[:80]}...")
            
            if articles:
                print(f"  ✅ PASS: Google News data retrieved")
            else:
                print(f"  ⚠️  WARN: No headlines found (Google may have changed HTML structure)")
            return len(articles) > 0
        elif r.status_code == 429:
            print("  ⚠️  WARN: Rate limited by Google")
            return False
        else:
            print(f"  ❌ FAIL: HTTP {r.status_code}")
            return False
            
    except ImportError:
        print("  ❌ FAIL: beautifulsoup4 not installed (pip install beautifulsoup4)")
        return False
    except requests.exceptions.ConnectionError:
        print("  ❌ FAIL: Cannot connect to Google")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False


def test_full_analysis(symbol='RELIANCE'):
    """Test the full analysis pipeline"""
    print(f"\n{'=' * 60}")
    print(f"TEST 5: Full Analysis Pipeline - {symbol}")
    print(f"{'=' * 60}")
    
    try:
        import unittest.mock as mock
        
        # Import with NSE mock to avoid double initialization
        from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
        
        analyzer = IntegratedMarketAnalyzer()
        
        print(f"  Analyzing {symbol}...")
        result = analyzer.analyze_single_stock(symbol)
        
        if result:
            price = result.get('price_data', {})
            strategy = result.get('best_strategy', {})
            confidence = result.get('confidence', 0)
            
            print(f"  Current Price: ₹{price.get('current_price', 'N/A')}")
            print(f"  Strategy: {strategy.get('name', 'N/A')}")
            print(f"  Confidence: {confidence}%")
            print(f"  ✅ PASS: Full analysis completed successfully")
            return True
        else:
            print(f"  ❌ FAIL: Analysis returned no results")
            print(f"  This may be due to:")
            print(f"    - NSE API not reachable (market hours required)")
            print(f"    - Yahoo Finance data unavailable")
            print(f"    - No F&O data available for {symbol}")
            return False
            
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API verification tests"""
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'RELIANCE'
    is_index = symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50']
    
    print("=" * 60)
    print(f"🔍 API VERIFICATION - Testing with: {symbol}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: NSE Session
    session, cookies, nse_ok = test_nse_session()
    results['NSE Session'] = nse_ok
    
    # Test 2: NSE Option Chain
    if nse_ok:
        results['NSE Option Chain'] = test_nse_option_chain(session, cookies, symbol, is_index)
    else:
        results['NSE Option Chain'] = False
        print(f"\n  ⚠️  SKIP: NSE Option Chain (no session)")
    
    # Test 3: Yahoo Finance
    results['Yahoo Finance'] = test_yahoo_finance(symbol if not is_index else 'RELIANCE')
    
    # Test 4: Google News
    results['Google News'] = test_google_news(symbol)
    
    # Test 5: Full Analysis (only if at least Yahoo works)
    if results.get('Yahoo Finance') or results.get('NSE Option Chain'):
        results['Full Analysis'] = test_full_analysis(symbol)
    else:
        results['Full Analysis'] = False
        print(f"\n  ⚠️  SKIP: Full Analysis (no data sources available)")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("  🎉 All APIs working correctly!")
    elif passed > 0:
        print("  ⚠️  Some APIs have issues - analyzer may still work with fallbacks")
    else:
        print("  ❌ No APIs working - check internet connection and try again")
    
    print(f"{'=' * 60}")
    return 0 if passed > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
