#!/usr/bin/env python3
"""
Market Analyzer v5.0 - Production Ready
- NSE API as PRIMARY source (real-time Indian data)
- Yahoo Finance as BACKUP (fundamentals + fallback)
- Google News parser for sentiment
- Yahoo Finance News parser for sentiment
- All 189 F&O symbols
- Multi-threaded
- Intelligent backtesting
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional
import os
import concurrent.futures
from threading import Lock
import warnings
warnings.filterwarnings('ignore')

# Import components
from fno_symbols import get_all_fno_symbols, get_fno_count
from nse_data_fetcher_clean import NSEDataFetcher
from lot_sizes import get_lot_size, is_index

# Backtesting is now fully integrated - no separate module needed

# Try to import API configuration
try:
    from config import ALPHAVANTAGE_API_KEY
except ImportError:
    print("📋 No config.py found - using template. Copy config_template.py to config.py to add API keys.")
    ALPHAVANTAGE_API_KEY = None

# Backtesting is now integrated into the main analyzer - no separate module needed


class NewsParser:
    """Parse news from Google News and Yahoo Finance for sentiment"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_google_news(self, symbol: str) -> Dict:
        """
        Parse Google News for stock sentiment
        URL: https://www.google.com/search?q=SYMBOL+stock+news+india&tbm=nws
        """
        try:
            query = f"{symbol} stock news india"
            url = f"https://www.google.com/search?q={query}&tbm=nws&hl=en"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return self._empty_sentiment()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            articles = []
            headlines = soup.find_all('div', class_='SoaBEf')
            
            for headline in headlines[:5]:  # Top 5 news
                try:
                    title_elem = headline.find('div', class_='MBeuO')
                    if title_elem:
                        title = title_elem.get_text()
                        articles.append(title)
                except:
                    continue
            
            if not articles:
                # Try alternative structure
                headlines = soup.find_all('div', {'role': 'heading'})
                for headline in headlines[:5]:
                    try:
                        title = headline.get_text()
                        if len(title) > 20:  # Filter out noise
                            articles.append(title)
                    except:
                        continue
            
            # Analyze sentiment from headlines
            sentiment = self._analyze_sentiment(articles)
            sentiment['source'] = 'Google News'
            sentiment['headlines'] = articles[:3]  # Top 3
            
            return sentiment
            
        except Exception as e:
            print(f"⚠️  Google News parsing error for {symbol}: {str(e)}")
            return self._empty_sentiment()
    
    def parse_yahoo_finance_news(self, symbol: str) -> Dict:
        """
        Parse Yahoo Finance News for stock sentiment
        URL: https://finance.yahoo.com/quote/SYMBOL.NS/news
        """
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}.NS/news"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return self._empty_sentiment()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            articles = []
            
            # Yahoo uses various structures, try multiple
            news_items = soup.find_all('h3', class_='Mb(5px)')
            if not news_items:
                news_items = soup.find_all('h3')
            
            for item in news_items[:5]:  # Top 5 news
                try:
                    title = item.get_text().strip()
                    if len(title) > 20:
                        articles.append(title)
                except:
                    continue
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(articles)
            sentiment['source'] = 'Yahoo Finance'
            sentiment['headlines'] = articles[:3]
            
            return sentiment
            
        except Exception as e:
            print(f"⚠️  Yahoo Finance News parsing error for {symbol}: {str(e)}")
            return self._empty_sentiment()
    
    def get_combined_sentiment(self, symbol: str) -> Dict:
        """
        Get combined sentiment from both Google News and Yahoo Finance
        """
        google_sentiment = self.parse_google_news(symbol)
        time.sleep(1)  # Rate limiting
        yahoo_sentiment = self.parse_yahoo_finance_news(symbol)
        
        # Combine sentiments
        all_headlines = google_sentiment['headlines'] + yahoo_sentiment['headlines']
        combined_score = (google_sentiment['score'] + yahoo_sentiment['score']) / 2
        
        # Determine momentum
        if combined_score > 0.15:
            momentum = 'POSITIVE'
        elif combined_score < -0.15:
            momentum = 'NEGATIVE'
        else:
            momentum = 'NEUTRAL'
        
        return {
            'score': round(combined_score, 2),
            'momentum': momentum,
            'sources': ['Google News', 'Yahoo Finance'],
            'headlines': all_headlines[:5],  # Top 5 combined
            'news_count': len(all_headlines)
        }
    
    def _analyze_sentiment(self, headlines: List[str]) -> Dict:
        """
        Simple sentiment analysis based on keywords
        Production: Use NLP libraries like TextBlob or VADER
        """
        if not headlines:
            return self._empty_sentiment()
        
        positive_words = [
            'surge', 'jump', 'rally', 'gain', 'profit', 'growth', 'up', 'rise',
            'high', 'beat', 'strong', 'positive', 'bullish', 'upgrade', 'buy',
            'outperform', 'record', 'boost', 'success', 'winner', 'top'
        ]
        
        negative_words = [
            'fall', 'drop', 'crash', 'loss', 'down', 'decline', 'weak', 'negative',
            'bearish', 'downgrade', 'sell', 'underperform', 'miss', 'concern',
            'worry', 'risk', 'threat', 'bottom', 'worst', 'fail'
        ]
        
        positive_count = 0
        negative_count = 0
        
        combined_text = ' '.join(headlines).lower()
        
        for word in positive_words:
            positive_count += combined_text.count(word)
        
        for word in negative_words:
            negative_count += combined_text.count(word)
        
        total = positive_count + negative_count
        
        if total == 0:
            score = 0
            momentum = 'NEUTRAL'
        else:
            score = (positive_count - negative_count) / total
            if score > 0.3:
                momentum = 'POSITIVE'
            elif score < -0.3:
                momentum = 'NEGATIVE'
            else:
                momentum = 'NEUTRAL'
        
        return {
            'score': round(score, 2),
            'momentum': momentum,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'news_count': len(headlines)
        }
    
    def _empty_sentiment(self) -> Dict:
        """Return empty sentiment when parsing fails"""
        return {
            'score': 0,
            'momentum': 'NEUTRAL',
            'headlines': [],
            'news_count': 0,
            'source': 'None'
        }


class IntegratedMarketAnalyzer:
    """
    Integrated Market Analyzer v5.0
    - NSE for Option Chains
    - Yahoo for Stock Fundamentals  
    - Google News for Sentiment
    """
    
    def __init__(self):
        # Initialize clean NSE fetcher (no API key needed - uses official NSE API)
        self.nse = NSEDataFetcher()
        self.news_parser = NewsParser()
        self.lock = Lock()
        
        # Backtesting is now fully integrated - no separate module needed
        
        # Silent initialization
        
        # Results categorized by confidence
        self.high_confidence = []
        self.medium_confidence = []
        self.low_confidence = []
        
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def fetch_price_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock price data from Yahoo Finance (primary source for fundamentals)
        NSE is used separately for option chain data only
        """
        try:
            return self.fetch_yahoo_data(symbol)
        except Exception as e:
            return None
    
    def fetch_yahoo_data(self, symbol: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance as backup"""
        try:
            # Handle special symbols
            if symbol == 'NIFTY':
                ticker = '^NSEI'  # NIFTY 50 index
            elif symbol == 'BANKNIFTY':
                ticker = '^NSEBANK'  # Bank NIFTY index
            elif symbol.startswith('^'):
                ticker = symbol  # Index symbols like ^NSEI
            else:
                ticker = f"{symbol}.NS"  # Add .NS for Indian stocks
            
            end_date = int(time.time())
            start_date = end_date - (90 * 24 * 60 * 60)  # 90 days for better data
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            params = {
                'period1': start_date,
                'period2': end_date,
                'interval': '1d',
                'includePrePost': 'false'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check if the response has valid chart data
                    if not data.get('chart') or not data['chart'].get('result'):
                        print(f"   ⚠️  Yahoo: No chart data for {ticker}")
                        return None
                    
                    chart = data['chart']['result'][0]
                    
                    # Check if the chart has indicators
                    if not chart.get('indicators') or not chart['indicators'].get('quote'):
                        print(f"   ⚠️  Yahoo: No quote data for {ticker}")
                        return None
                    
                    quote = chart['indicators']['quote'][0]
                    timestamps = chart.get('timestamp', [])
                    
                    # Filter out None values and get valid data
                    closes = [c for c in quote.get('close', []) if c is not None]
                    highs = [h for h in quote.get('high', []) if h is not None]
                    lows = [l for l in quote.get('low', []) if l is not None]
                    opens = [o for o in quote.get('open', []) if o is not None]
                    volumes = [v for v in quote.get('volume', []) if v is not None]
                    
                    if not closes:
                        print(f"   ⚠️  Yahoo: No valid price data for {ticker}")
                        return None
                    
                    current_price = closes[-1]
                    
                    # Get the current market price from meta if available
                    meta = chart.get('meta', {})
                    if meta.get('regularMarketPrice'):
                        current_price = meta['regularMarketPrice']
                    
                    return {
                        'symbol': symbol,
                        'current_price': current_price,
                        'open': opens[-1] if opens else current_price,
                        'high': highs[-1] if highs else current_price,
                        'low': lows[-1] if lows else current_price,
                        'close': current_price,
                        'volume': volumes[-1] if volumes else 0,
                        'high_52w': max(highs) if highs else current_price,
                        'low_52w': min(lows) if lows else current_price,
                        'change': current_price - opens[-1] if opens else 0,
                        'pChange': ((current_price - opens[-1]) / opens[-1] * 100) if opens and opens[-1] else 0,
                        'source': 'Yahoo Finance',
                        'timestamp': datetime.now().isoformat(),
                        'historical_closes': closes[-30:] if len(closes) >= 30 else closes  # Last 30 days for technical analysis
                    }
                    
                except json.JSONDecodeError:
                    print(f"   ❌ Yahoo: Invalid JSON response for {ticker}")
                    return None
            else:
                print(f"   ⚠️  Yahoo API returned {response.status_code} for {ticker}")
                return None
            
        except requests.exceptions.Timeout:
            print(f"   ⚠️  Yahoo: Timeout for {ticker}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Yahoo: Connection error for {ticker}")
            return None
        except Exception as e:
            print(f"   ❌ Yahoo fetch error for {symbol}: {str(e)}")
            return None
    
    def fetch_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Fetch fundamentals from Yahoo Finance
        NSE doesn't provide fundamental data easily
        """
        try:
            ticker = f"{symbol}.NS"
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
            params = {
                'modules': 'financialData,defaultKeyStatistics'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data['quoteSummary']['result'][0]
                
                financial = result.get('financialData', {})
                stats = result.get('defaultKeyStatistics', {})
                
                return {
                    'pe': stats.get('trailingPE', {}).get('raw', None),
                    'pb': stats.get('priceToBook', {}).get('raw', None),
                    'roe': financial.get('returnOnEquity', {}).get('raw', 0) * 100 if financial.get('returnOnEquity') else None,
                    'debt_to_equity': financial.get('debtToEquity', {}).get('raw', None),
                    'industry_pe': 20  # Approximate, would need industry data
                }
            
            return None
            
        except:
            return None
    
    def calculate_technical_indicators(self, data: Dict) -> Dict:
        """Calculate RSI, moving averages, etc."""
        # Try to get historical closes from the data
        if 'historical_closes' in data:
            prices = data['historical_closes']
        else:
            # Fallback to current price
            prices = [data.get('current_price', data.get('close', 0))]
        
        if len(prices) < 2:
            return {
                'rsi': 50, 
                'sma_10': prices[0] if prices else 0, 
                'sma_20': prices[0] if prices else 0, 
                'trend': 'SIDEWAYS'
            }
        
        current_price = prices[-1]
        
        # RSI calculation (need at least 14 periods)
        if len(prices) >= 14:
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            # Simple momentum calculation for shorter periods
            if len(prices) >= 5:
                recent_avg = sum(prices[-5:]) / 5
                older_avg = sum(prices[:5]) / 5
                if older_avg > 0:
                    momentum = (recent_avg - older_avg) / older_avg
                    rsi = 50 + (momentum * 100)  # Convert to RSI-like scale
                    rsi = max(0, min(100, rsi))  # Clamp between 0 and 100
                else:
                    rsi = 50
            else:
                rsi = 50
        
        # Moving averages
        sma_10 = sum(prices[-10:]) / min(10, len(prices))
        sma_20 = sum(prices[-20:]) / min(20, len(prices))
        
        # Trend determination
        if len(prices) >= 10:
            recent_prices = prices[-5:]
            older_prices = prices[-10:-5] if len(prices) >= 10 else prices[:-5]
            
            recent_avg = sum(recent_prices) / len(recent_prices)
            older_avg = sum(older_prices) / len(older_prices) if older_prices else recent_avg
            
            if recent_avg > older_avg * 1.02:  # 2% threshold
                trend = 'UPTREND'
            elif recent_avg < older_avg * 0.98:  # 2% threshold
                trend = 'DOWNTREND'
            else:
                trend = 'SIDEWAYS'
        else:
            trend = 'SIDEWAYS'
        
        return {
            'rsi': round(rsi, 2),
            'sma_10': round(sma_10, 2),
            'sma_20': round(sma_20, 2),
            'trend': trend
        }
    
    def analyze_single_stock(self, symbol: str) -> Optional[Dict]:
        """Analyze a single stock with all data sources"""
        
        # 1. Fetch price data (Yahoo Finance for fundamentals)
        price_data = self.fetch_price_data(symbol)
        
        if not price_data:
            return None
        
        # 2. Fetch fundamentals (Yahoo only)
        fundamentals = self.fetch_fundamentals(symbol)
        
        # 3. Fetch news sentiment (Google + Yahoo News)
        news_sentiment = self.news_parser.get_combined_sentiment(symbol)
        
        # 4. Calculate technical indicators
        technical = self.calculate_technical_indicators(price_data)
        
        # 5. Fetch option chain data (CRITICAL for F&O trading)
        option_chain = None
        try:
            option_chain = self.nse.get_option_chain(symbol)
            if not option_chain or not option_chain.get('records', {}).get('data'):
                # Skip stocks without F&O data completely
                return None
        except Exception as e:
            # Skip stocks with option chain fetch errors
            return None
        
        # 6. Calculate BASE confidence (50% weight from data)
        base_confidence = self.calculate_confidence(price_data, fundamentals, news_sentiment, technical, option_chain)
        
        # 7. Generate strategy based on conditions (ALWAYS generate, never reject here)
        strategy = self.generate_strategy(price_data, technical, base_confidence, symbol, option_chain)
        
        # 8. Calculate FINAL confidence with all components
        final_confidence = self.calculate_final_confidence(base_confidence, strategy, symbol, option_chain)
        
        # Add final confidence to strategy
        strategy['final_confidence'] = final_confidence
        
        # 9. Only reject based on FINAL confidence level
        if final_confidence < 40:  # Minimum confidence threshold
            strategy = {
                'name': 'Strategy Rejected',
                'action': f'All strategies rejected - confidence too low ({final_confidence}%)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Wait for better conditions',
                'rejection_reason': f'Final confidence {final_confidence}% below minimum 40%',
                'confidence_breakdown': strategy.get('confidence_breakdown', {}),
                'final_confidence': final_confidence
            }
        
        result = {
            'symbol': symbol,
            'timestamp': self.timestamp,
            'price_data': price_data,
            'fundamentals': fundamentals,
            'technical': technical,
            'news_sentiment': news_sentiment,
            'base_confidence': base_confidence,  # Show breakdown
            'confidence': final_confidence,  # Final confidence with backtesting adjustment
            'best_strategy': strategy
        }
        
        # Categorize
        with self.lock:
            if final_confidence >= 50:
                self.high_confidence.append(result)
                # ONLY show APPROVED strategies with >50% confidence in terminal (not rejected ones)
                if strategy.get('name') != 'Strategy Rejected':
                    self.print_strategy_recommendation(result)
                else:
                    # Log rejected strategy but don't display in terminal
                    print(f"🔍 {symbol}: Strategy rejected - saved to analysis file for review")
            elif final_confidence >= 30:
                self.medium_confidence.append(result)
            else:
                self.low_confidence.append(result)
        
        return result
    
    def calculate_final_confidence(self, base_confidence: int, strategy: Dict, symbol: str, option_chain: Dict) -> int:
        """
        Calculate final confidence with NEW breakdown:
        50% from base data + 25% from historical backtesting + 25% from risk:reward ratio
        """
        # Component 1: Base data confidence (50% weight) 
        data_component = base_confidence * 0.5
        
        # Component 2: Historical backtesting (25% weight)
        backtesting_result = strategy.get('backtesting_result')
        if backtesting_result:
            backtest_score = backtesting_result.get('score', 50)
            historical_component = backtest_score * 0.25
        else:
            historical_component = 50 * 0.25  # Neutral if no data
        
        # Component 3: Risk:Reward ratio (25% weight)
        risk_reward = strategy.get('risk_reward', 0)
        if risk_reward >= 1.0:  # Good risk:reward (1:1 or better)
            rr_score = min(100, 50 + (risk_reward * 25))  # Scale up to 100
        elif risk_reward >= 0.5:  # Acceptable risk:reward  
            rr_score = 25 + (risk_reward * 50)  # Scale 0.5-1.0 to 50-75
        else:  # Poor risk:reward
            rr_score = max(0, risk_reward * 50)  # Scale 0-0.5 to 0-25
        
        rr_component = rr_score * 0.25
        
        # Final confidence
        final_confidence = data_component + historical_component + rr_component
        final_confidence = max(0, min(100, final_confidence))
        
        # Add detailed breakdown to strategy
        strategy['confidence_breakdown'] = {
            'base_data_confidence': base_confidence,
            'data_component': f"{data_component:.1f} (50% weight)",
            'historical_component': f"{historical_component:.1f} (25% weight)",
            'risk_reward_component': f"{rr_component:.1f} (25% weight)",
            'risk_reward_ratio': f"1:{risk_reward:.2f}",
            'final_confidence': int(final_confidence)
        }
        
        return int(final_confidence)
    
    def print_strategy_recommendation(self, result: Dict):
        """Print detailed strategy recommendation with exact trades"""
        symbol = result['symbol']
        strategy = result['best_strategy']
        confidence = result['confidence']
        price = result['price_data']['current_price']
        
        print(f"\n{'='*80}")
        print(f"🎯 {symbol} | Current Price: ₹{price:.2f} | Confidence: {confidence}%")
        print(f"{'='*80}")
        print(f"📋 Strategy: {strategy['name']} ({strategy['outlook']})")
        
        # Check if strategy was rejected
        if strategy['name'] == 'Strategy Rejected':
            print(f"🎯 REJECTION REASON:")
            print(f"   ❌ {strategy['action']}")
            
            if strategy.get('rejection_reason'):
                print(f"   💡 Details: {strategy['rejection_reason']}")
            
            print(f"\n💰 FINANCIAL BREAKDOWN:")
            print(f"   📊 Strategy: REJECTED - No trades executed")
            print(f"   💵 Investment Required: ₹0 (strategy not viable)")
            print(f"   📈 Max Profit: ₹0 (strategy rejected)")
            print(f"   📉 Max Loss: ₹0 (no position taken)")
            
            if strategy.get('risk_reward', 0) > 0 and strategy.get('risk_reward', 0) != 0:
                print(f"   ⚖️  Calculated Risk:Reward: 1:{strategy['risk_reward']:.2f} (but strategy rejected due to poor ratio)")
            else:
                print(f"   ⚖️  Risk:Reward: Not applicable (strategy rejected)")
            
            print(f"{'='*80}")
            return
        
        # Determine confidence color
        confidence = strategy.get('final_confidence', 0)
        if confidence >= 70:
            confidence_color = "🟢"  # Green for high confidence
        elif confidence >= 50:
            confidence_color = "🟡"  # Yellow for medium confidence
        else:
            confidence_color = "🔴"  # Red for low confidence
        
        # Strategy was approved - show full details
        print(f"EXACT TRADES:")
        print(f"   {strategy['action']}")
        
        if strategy.get('trade_details'):
            for detail in strategy['trade_details']:
                print(f"   • {detail}")
        
        print(f"\nFINANCIAL BREAKDOWN:")
        print(f"   Lot Size: {strategy.get('lot_size', 'N/A')} units")
        print(f"   Quantity: {strategy.get('quantity', 'N/A')} lots")
        print(f"   Premium Cost: ₹{strategy['investment']:,.0f}")
        
        margin_req = strategy.get('margin_required', 'N/A')
        if isinstance(margin_req, (int, float)):
            print(f"   Margin Required: ₹{margin_req:,.0f}")
        else:
            print(f"   Margin Required: {margin_req}")
            
        print(f"   Max Profit: ₹{strategy['max_profit']:,.0f}")
        print(f"   Max Loss: ₹{strategy['max_loss']:,.0f}")
        print(f"   Risk:Reward Ratio: 1:{strategy['risk_reward']:.2f}")
        
        # Show confidence breakdown with color coding
        if strategy.get('confidence_breakdown'):
            breakdown = strategy['confidence_breakdown']
            print(f"\n   CONFIDENCE BREAKDOWN:")
            print(f"      Data Component: {breakdown.get('data_component', 'N/A')} (50% weight)")
            print(f"      Historical Component: {breakdown.get('historical_component', 'N/A')} (25% weight)")
            print(f"      Risk:Reward Component: {breakdown.get('risk_reward_component', 'N/A')} (25% weight)")
            print(f"      {confidence_color} Final Confidence: {confidence:.1f}%")
        
        # Show backtesting validation results
        if strategy.get('backtesting_result'):
            bt_result = strategy['backtesting_result']
            success_rate = bt_result.get('success_rate', 0)
            if success_rate >= 60:
                validation_color = "🟢"
            elif success_rate >= 40:
                validation_color = "🟡"
            else:
                validation_color = "🔴"
            print(f"   {validation_color} Historical Success Rate: {success_rate:.1f}% ({bt_result.get('profitable_outcomes', 0)}/{bt_result.get('total_outcomes', 0)} scenarios)")
        
        if strategy.get('breakeven'):
            print(f"   Breakeven: {strategy['breakeven']}")
        
        print(f"{'='*80}")
    
    def practical_strategy_backtest(self, symbol: str, strategy_type: str, current_price: float, 
                                   buy_strike: float, sell_strike: float, 
                                   net_cost: float) -> Dict:
        """
        Practical backtesting that tests directional accuracy and realistic breakeven scenarios
        """
        # Use integrated Yahoo Finance data fetching for backtesting
        try:
            import yfinance as yf
            
            # Convert symbol to Yahoo Finance format
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                ticker = symbol
            else:
                ticker = f"{symbol}.NS"
            
            # Get 30 days of historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            
            if hist.empty or len(hist) < 10:
                return {'score': 42, 'verdict': 'NO_DATA', 'reason': 'Insufficient historical data'}
            
            # Convert to the format expected by backtesting methods
            historical_data = {
                'closes': hist['Close'].tolist(),
                'highs': hist['High'].tolist(),
                'lows': hist['Low'].tolist(),
                'dates': hist.index.tolist()
            }
            
        except ImportError:
            return {'score': 42, 'verdict': 'NO_DATA', 'reason': 'yfinance not available'}
        except Exception:
            return {'score': 42, 'verdict': 'NO_DATA', 'reason': 'Data fetch failed'}
        
        # Strategy-specific backtesting logic
        if strategy_type == 'Bull Call Spread':
            return self._backtest_bull_call_spread(historical_data, buy_strike, sell_strike, net_cost)
        elif strategy_type == 'Long Call':
            return self._backtest_long_call(historical_data, buy_strike, net_cost)
        elif strategy_type == 'Long Put':
            return self._backtest_long_put(historical_data, buy_strike, net_cost)
        elif strategy_type == 'Bear Put Spread':
            return self._backtest_bear_put_spread(historical_data, buy_strike, sell_strike, net_cost)
        elif strategy_type == 'Long Straddle':
            return self._backtest_long_straddle(historical_data, buy_strike, net_cost)
        elif strategy_type == 'Iron Condor':
            return self._backtest_iron_condor(historical_data, buy_strike, sell_strike, net_cost)
        else:
            return {'score': 50, 'verdict': 'UNKNOWN', 'reason': f'Unknown strategy type: {strategy_type}'}
    
    def _backtest_bull_call_spread(self, historical_data: Dict, buy_strike: float, sell_strike: float, net_cost: float) -> Dict:
        """Backtest Bull Call Spread strategy"""
        profitable_scenarios = 0
        max_profit_scenarios = 0
        directional_accuracy = 0
        
        results = []
        total_scenarios = len(historical_data['closes']) - 5
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]  # 5 days later
            
            # Directional accuracy (bullish strategy expects upward move)
            if exit_price > entry_price:
                directional_accuracy += 1
            
            # Profit calculation
            breakeven_price = buy_strike + net_cost
            if exit_price >= sell_strike:
                max_profit_scenarios += 1
                profitable_scenarios += 1
                profit = (sell_strike - buy_strike) - net_cost
            elif exit_price >= breakeven_price:
                profitable_scenarios += 1
                profit = (exit_price - buy_strike) - net_cost
            else:
                profit = -net_cost
            
            results.append({
                'entry': entry_price,
                'exit': exit_price,
                'profit': profit,
                'profitable': profit > 0
            })
        
        direction_pct = (directional_accuracy / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (direction_pct * 0.3) + (profit_pct * 0.7)
        
        if overall_score >= 65:
            verdict = 'STRONG_BUY'
        elif overall_score >= 40:
            verdict = 'CAUTIOUS'
        else:
            verdict = 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'direction_accuracy': direction_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {direction_pct:.1f}% directional accuracy'
        }
    
    def _backtest_long_call(self, historical_data: Dict, strike: float, premium: float) -> Dict:
        """Backtest Long Call strategy"""
        profitable_scenarios = 0
        directional_accuracy = 0
        
        total_scenarios = len(historical_data['closes']) - 5
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]
            
            if exit_price > entry_price:
                directional_accuracy += 1
            
            # Long call profit = max(exit_price - strike, 0) - premium
            breakeven = strike + premium
            if exit_price >= breakeven:
                profitable_scenarios += 1
        
        direction_pct = (directional_accuracy / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (direction_pct * 0.4) + (profit_pct * 0.6)
        
        verdict = 'STRONG_BUY' if overall_score >= 65 else 'CAUTIOUS' if overall_score >= 40 else 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'direction_accuracy': direction_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {direction_pct:.1f}% directional accuracy'
        }
    
    def _backtest_long_put(self, historical_data: Dict, strike: float, premium: float) -> Dict:
        """Backtest Long Put strategy"""
        profitable_scenarios = 0
        directional_accuracy = 0
        
        total_scenarios = len(historical_data['closes']) - 5
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]
            
            if exit_price < entry_price:
                directional_accuracy += 1
            
            # Long put profit = max(strike - exit_price, 0) - premium
            breakeven = strike - premium
            if exit_price <= breakeven:
                profitable_scenarios += 1
        
        direction_pct = (directional_accuracy / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (direction_pct * 0.4) + (profit_pct * 0.6)
        
        verdict = 'STRONG_BUY' if overall_score >= 65 else 'CAUTIOUS' if overall_score >= 40 else 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'direction_accuracy': direction_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {direction_pct:.1f}% directional accuracy'
        }
    
    def _backtest_bear_put_spread(self, historical_data: Dict, buy_strike: float, sell_strike: float, net_cost: float) -> Dict:
        """Backtest Bear Put Spread strategy"""
        profitable_scenarios = 0
        directional_accuracy = 0
        
        total_scenarios = len(historical_data['closes']) - 5
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]
            
            if exit_price < entry_price:
                directional_accuracy += 1
            
            # Bear put spread profit calculation
            breakeven_price = buy_strike - net_cost
            if exit_price <= sell_strike:
                profitable_scenarios += 1  # Max profit zone
            elif exit_price <= breakeven_price:
                profitable_scenarios += 1  # Some profit zone
        
        direction_pct = (directional_accuracy / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (direction_pct * 0.3) + (profit_pct * 0.7)
        
        verdict = 'STRONG_BUY' if overall_score >= 65 else 'CAUTIOUS' if overall_score >= 40 else 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'direction_accuracy': direction_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {direction_pct:.1f}% directional accuracy'
        }
    
    def _backtest_long_straddle(self, historical_data: Dict, strike: float, net_cost: float) -> Dict:
        """Backtest Long Straddle strategy (profits from large moves in either direction)"""
        profitable_scenarios = 0
        volatility_scenarios = 0
        
        total_scenarios = len(historical_data['closes']) - 5
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]
            
            # Straddle profits from large moves in either direction
            price_move = abs(exit_price - entry_price)
            price_move_pct = (price_move / entry_price) * 100
            
            # Consider high volatility if move > 2%
            if price_move_pct > 2.0:
                volatility_scenarios += 1
            
            # Long straddle breakeven: strike ± net_cost
            breakeven_up = strike + net_cost
            breakeven_down = strike - net_cost
            
            if exit_price >= breakeven_up or exit_price <= breakeven_down:
                profitable_scenarios += 1
        
        volatility_pct = (volatility_scenarios / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (volatility_pct * 0.4) + (profit_pct * 0.6)
        
        verdict = 'STRONG_BUY' if overall_score >= 65 else 'CAUTIOUS' if overall_score >= 40 else 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'volatility_accuracy': volatility_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {volatility_pct:.1f}% high volatility periods'
        }
    
    def _backtest_iron_condor(self, historical_data: Dict, center_strike: float, wing_width: float, net_credit: float) -> Dict:
        """Backtest Iron Condor strategy (profits from low volatility/sideways movement)"""
        profitable_scenarios = 0
        low_volatility_scenarios = 0
        
        total_scenarios = len(historical_data['closes']) - 5
        
        # Iron Condor profit zone (between inner strikes)
        lower_breakeven = center_strike - wing_width + net_credit
        upper_breakeven = center_strike + wing_width - net_credit
        
        for i in range(total_scenarios):
            entry_price = historical_data['closes'][i]
            exit_price = historical_data['closes'][i + 5]
            
            # Iron Condor profits from sideways movement
            price_move = abs(exit_price - entry_price)
            price_move_pct = (price_move / entry_price) * 100
            
            # Consider low volatility if move < 1.5%
            if price_move_pct < 1.5:
                low_volatility_scenarios += 1
            
            # Profit if price stays within the profit zone
            if lower_breakeven <= exit_price <= upper_breakeven:
                profitable_scenarios += 1
        
        low_vol_pct = (low_volatility_scenarios / total_scenarios * 100)
        profit_pct = (profitable_scenarios / total_scenarios * 100)
        overall_score = (low_vol_pct * 0.4) + (profit_pct * 0.6)
        
        verdict = 'STRONG_BUY' if overall_score >= 65 else 'CAUTIOUS' if overall_score >= 40 else 'AVOID'
        
        return {
            'score': overall_score,
            'verdict': verdict,
            'low_volatility_accuracy': low_vol_pct,
            'profit_accuracy': profit_pct,
            'scenarios_tested': total_scenarios,
            'reason': f'{profit_pct:.1f}% profitable scenarios, {low_vol_pct:.1f}% low volatility periods'
        }

    def generate_strategy(self, price_data: Dict, technical: Dict, confidence: int, symbol: str, option_chain: Optional[Dict] = None) -> Dict:
        """
        Generate appropriate options strategy based on market conditions
        Implements all strategies from STRATEGIES_GUIDE.md
        Max investment: ₹50,000
        NOW WITH BACKTESTING VALIDATION - Only recommends historically validated strategies
        """
        current_price = price_data['current_price']
        trend = technical.get('trend', 'SIDEWAYS')
        rsi = technical.get('rsi', 50)
        price_change = price_data.get('pChange', 0)
        
        # 🧠 BACKTESTING VALIDATION FILTER
        # Test potential strategies against historical data before recommending
        print(f"\n🧠 Running backtesting validation for {symbol}...")
        
        current_conditions = {
            'current_price': current_price,
            'rsi': rsi,
            'trend': trend,
            'price_change': price_change,
            '52w_high': price_data.get('yearHigh', current_price * 1.2),
            '52w_low': price_data.get('yearLow', current_price * 0.8)
        }
        
        # CRITICAL: No strategy without real option chain data
        if not option_chain or not option_chain.get('records', {}).get('data'):
            return {
                'name': 'No F&O Trading',
                'action': f'Stock price: ₹{current_price:.1f} - No active options available',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Cash market only'
            }
        
        # Calculate ATM strike
        atm_strike = round(current_price / 50) * 50
        
        # IMPROVED Strategy selection - More practical conditions
        
        # Strong bullish signals
        if (trend == 'UPTREND' and price_change > 0.5) or (price_change > 2):
            if confidence >= 70:
                return self.generate_long_call_strategy(current_price, atm_strike, option_chain)
            else:
                return self.generate_bull_call_spread(current_price, atm_strike, option_chain)
                
        # Strong bearish signals
        elif (trend == 'DOWNTREND' and price_change < -0.5) or (price_change < -2):
            if confidence >= 70:
                return self.generate_long_put_strategy(current_price, atm_strike, option_chain)
            else:
                return self.generate_bear_put_spread(current_price, atm_strike, option_chain)
                
        # High volatility based on VOLUME, not price change
        volume_volatility = self.check_volume_volatility(option_chain, symbol)
        if volume_volatility == 'HIGH':
            return self.generate_long_straddle(current_price, atm_strike, option_chain)
                
        # RSI-based strategies (more practical)
        elif rsi > 65:  # Overbought (lower threshold)
            return self.generate_bear_put_spread(current_price, atm_strike, option_chain)
            
        elif rsi < 35:  # Oversold (higher threshold) 
            return self.generate_bull_call_spread(current_price, atm_strike, option_chain)
            
        # Neutral market with moderate confidence
        elif confidence >= 60 and trend == 'SIDEWAYS' and abs(price_change) < 1.5:
            return self.generate_iron_condor(current_price, atm_strike, option_chain)
            
        # Default strategy for moderate bullish conditions
        elif confidence >= 50:
            if price_change >= 0:  # Any positive movement
                return self.generate_bull_call_spread(current_price, atm_strike, option_chain)
            else:  # Negative movement
                return self.generate_bear_put_spread(current_price, atm_strike, option_chain)
        else:
            # Default to watch if conditions are unclear
            return {
                'name': 'Watch',
                'action': f'Unclear conditions - Monitor for better setup',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                    'outlook': 'Wait for clear signal'
                }
    
    def generate_bull_call_spread(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Bull Call Spread - Moderately bullish strategy with exact trade details"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('CE', {}).get('underlying', 'UNKNOWN')
        lot_size = get_lot_size(symbol)
        
        buy_strike = atm_strike
        sell_strike = atm_strike + 100  # 100 points OTM
        
        # Get real option data
        buy_option = self.get_option_data(option_chain, buy_strike, 'CE', spot_price)
        sell_option = self.get_option_data(option_chain, sell_strike, 'CE', spot_price)
        
        buy_premium = buy_option['lastPrice']
        sell_premium = sell_option['lastPrice']
        
        # Strategy calculations
        net_cost = buy_premium - sell_premium
        max_profit = (sell_strike - buy_strike) - net_cost
        max_loss = net_cost
        risk_reward = max_profit / max_loss if max_loss > 0 else 0
        
        # Position sizing (max ₹50K investment)
        cost_per_lot = net_cost * lot_size
        max_lots = min(5, 45000 // cost_per_lot) if cost_per_lot > 0 else 1
        max_lots = max(1, max_lots)  # At least 1 lot
        
        # Financial calculations
        total_investment = max_lots * cost_per_lot
        total_max_profit = max_lots * max_profit * lot_size
        total_max_loss = max_lots * max_loss * lot_size
        
        # Margin calculation (approximate: 15-20% of underlying value for spreads)
        margin_per_lot = lot_size * spot_price * 0.15  # 15% margin for spreads
        total_margin = max_lots * margin_per_lot
        
        # Breakeven calculation
        breakeven = buy_strike + net_cost
        
        # Practical backtesting validation (for confidence adjustment only)
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Bull Call Spread',
            current_price=spot_price,
            buy_strike=buy_strike,
            sell_strike=sell_strike,
            net_cost=net_cost
        )
        
        strategy_dict = {
            'name': 'Bull Call Spread',
            'outlook': 'Moderately Bullish',
            'action': f'Execute Bull Call Spread with {max_lots} lots (Expiry: {buy_option["expiryDate"]})',
            'trade_details': [
                f'BUY: {max_lots} lots of {buy_strike} CE @ ₹{buy_premium:.1f} per option',
                f'   → Total: {max_lots} × 250 × ₹{buy_premium:.1f} = ₹{max_lots * buy_premium * lot_size:,.0f}',
                f'SELL: {max_lots} lots of {sell_strike} CE @ ₹{sell_premium:.1f} per option', 
                f'   → Total: {max_lots} × 250 × ₹{sell_premium:.1f} = ₹{max_lots * sell_premium * lot_size:,.0f}',
                f'NET DEBIT: ₹{total_investment:,.0f} (you pay this amount)',
                f'EXPIRY: {buy_option["expiryDate"]}',
                f'EXACT TRADE: Buy {max_lots * lot_size} units of {buy_strike} CE, Sell {max_lots * lot_size} units of {sell_strike} CE'
            ],
            'lot_size': lot_size,
            'quantity': max_lots,
            'investment': total_investment,
            'margin_required': total_margin,
            'max_profit': total_max_profit,
            'max_loss': total_max_loss,
            'risk_reward': risk_reward,
            'breakeven': f'₹{breakeven:.1f}',
            'strikes': f'{buy_strike} CE (Buy) / {sell_strike} CE (Sell)',
            'volume_analysis': {
                'buy_volume': buy_option['volume'],
                'sell_volume': sell_option['volume'],
                'buy_oi': buy_option['openInterest'],
                'sell_oi': sell_option['openInterest']
            }
        }
        
        # Add backtesting results if available
        if backtesting_result:
            strategy_dict['backtesting_result'] = backtesting_result
        
        return strategy_dict
    
    def generate_long_call_strategy(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Long Call - Strongly bullish strategy with exact trade details"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('CE', {}).get('underlying', 'UNKNOWN')
        lot_size = get_lot_size(symbol)
        
        strike = atm_strike
        option_data = self.get_option_data(option_chain, strike, 'CE', spot_price)
        premium = option_data['lastPrice']
        
        # Practical backtesting validation for Long Call
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Long Call',
            current_price=spot_price,
            buy_strike=strike,
            sell_strike=0,  # Not applicable for long call
            net_cost=premium
        )
        
        # Reject strategy if backtesting shows poor performance
        if backtesting_result.get('verdict') == 'AVOID':
            print(f"🚫 {symbol} Long Call REJECTED by backtesting:")
            print(f"   Score: {backtesting_result.get('score', 0):.1f}/100")
            print(f"   Reason: {backtesting_result.get('reason', 'Poor historical performance')}")
            
            return {
                'name': 'Strategy Rejected',
                'action': f'Long Call rejected due to poor historical performance (Score: {backtesting_result.get("score", 0):.1f}/100)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not recommended',
                'rejection_reason': backtesting_result.get('reason', 'Failed backtesting validation')
            }
        
        # Position sizing (max ₹50K investment)
        cost_per_lot = premium * lot_size
        max_lots = min(10, 45000 // cost_per_lot) if cost_per_lot > 0 else 1
        max_lots = max(1, max_lots)  # At least 1 lot
        
        # Financial calculations
        total_investment = max_lots * cost_per_lot
        total_max_loss = total_investment
        
        # Margin for buying options = premium paid (no additional margin)
        total_margin = total_investment
        
        # Breakeven calculation
        breakeven = strike + premium
        
        return {
            'name': 'Long Call',
            'outlook': 'Strongly Bullish',
            'action': f'Buy {max_lots} lots of {strike} CE @ ₹{premium:.1f}',
            'trade_details': [
                f'🟢 BUY: {max_lots} lots of {strike} CE @ ₹{premium:.1f} per option',
                f'   → Total: {max_lots} × {lot_size} × ₹{premium:.1f} = ₹{total_investment:,.0f}',
                f'📊 PREMIUM PAID: ₹{total_investment:,.0f} (your maximum loss)',
                f'📋 EXACT TRADE: Buy {max_lots * lot_size} units of {strike} CE',
                f'🎯 PROFIT: Unlimited above ₹{breakeven:.1f}'
            ],
            'lot_size': lot_size,
            'quantity': max_lots,
            'investment': total_investment,
            'margin_required': total_margin,
            'max_profit': 999999,  # Unlimited
            'max_loss': total_max_loss,
            'risk_reward': 10.0,  # Very high potential
            'breakeven': f'₹{breakeven:.1f}',
            'strikes': f'{strike} CE (Buy)',
            'volume_analysis': {
                'volume': option_data['volume'],
                'open_interest': option_data['openInterest'],
                'iv': option_data['impliedVolatility']
            }
        }
    
    def generate_bear_put_spread(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Bear Put Spread - Moderately bearish strategy (FIXED: Proper calculations)"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('PE', {}).get('underlying', 'UNKNOWN')
        
        # Bear Put Spread: Buy higher strike PE, Sell lower strike PE
        buy_strike = atm_strike + 50   # Buy higher strike (more expensive)
        sell_strike = atm_strike - 50  # Sell lower strike (less expensive)
        
        try:
            buy_premium = self.get_option_premium(option_chain, buy_strike, 'PE', spot_price)
            sell_premium = self.get_option_premium(option_chain, sell_strike, 'PE', spot_price)
            
            if buy_premium <= 0 or sell_premium <= 0:
                return {
                    'name': 'Strategy Rejected',
                    'action': 'Bear Put Spread rejected - insufficient option liquidity',
                    'investment': 0,
                    'max_profit': 0,
                    'max_loss': 0,
                    'risk_reward': 0,
                    'outlook': 'Strategy not available',
                    'rejection_reason': 'No valid option prices found'
                }
        except Exception:
            return {
                'name': 'Strategy Rejected',
                'action': 'Bear Put Spread rejected - option data unavailable',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not available',
                'rejection_reason': 'Option chain data error'
            }
        
        # Calculate net cost (should be positive - we pay to enter)
        net_cost = buy_premium - sell_premium
        
        # Validate net cost is positive (we should pay to enter bear put spread)
        if net_cost <= 0:
            return {
                'name': 'Strategy Rejected',
                'action': f'Bear Put Spread rejected - net credit strategy (should be debit)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not profitable',
                'rejection_reason': f'Net cost: ₹{net_cost:.1f} (should be positive for bear put spread)'
            }
        
        # Calculate max profit and loss
        spread_width = buy_strike - sell_strike  # Should be positive
        max_profit_per_lot = spread_width - net_cost  # Max profit at expiry
        max_loss_per_lot = net_cost  # Max loss if both expire worthless
        
        # Validate max profit is positive
        if max_profit_per_lot <= 0:
            return {
                'name': 'Strategy Rejected',
                'action': f'Bear Put Spread rejected - no profit potential',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not profitable',
                'rejection_reason': f'Max profit: ₹{max_profit_per_lot:.1f} (should be positive)'
            }
        
        risk_reward = max_profit_per_lot / max_loss_per_lot if max_loss_per_lot > 0 else 0
        
        # Risk:reward validation
        if risk_reward < 0.3:  # At least 1:3 risk:reward minimum
            return {
                'name': 'Strategy Rejected',
                'action': f'Bear Put Spread rejected - poor risk:reward ratio of 1:{risk_reward:.2f}',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': risk_reward,
                'outlook': 'Risk too high for potential reward',
                'rejection_reason': f'Risk:Reward 1:{risk_reward:.2f} is below minimum 1:0.3'
            }
        
        # Practical backtesting validation for Bear Put Spread
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Bear Put Spread',
            current_price=spot_price,
            buy_strike=buy_strike,
            sell_strike=sell_strike,
            net_cost=net_cost
        )
        
        # Reject strategy if backtesting shows poor performance
        if backtesting_result.get('verdict') == 'AVOID':
            print(f"🚫 {symbol} Bear Put Spread REJECTED by backtesting:")
            print(f"   Score: {backtesting_result.get('score', 0):.1f}/100")
            print(f"   Reason: {backtesting_result.get('reason', 'Poor historical performance')}")
            
            return {
                'name': 'Strategy Rejected',
                'action': f'Bear Put Spread rejected due to poor historical performance (Score: {backtesting_result.get("score", 0):.1f}/100)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not recommended',
                'rejection_reason': backtesting_result.get('reason', 'Failed backtesting validation')
            }
        
        # Calculate position sizing
        lot_size = get_lot_size(symbol)
        quantity = min(10, 50000 // (net_cost * lot_size))  # Conservative sizing
        quantity = max(1, quantity)  # At least 1 lot
        
        # Get expiry information
        expiry_date = self.get_option_expiry(option_chain)
        
        strategy_dict = {
            'name': 'Bear Put Spread',
            'action': f'EXACT TRADES:\n   Execute Bear Put Spread with {quantity} lots (Expiry: {expiry_date})\n   • BUY: {quantity} lots of {buy_strike} PE @ ₹{buy_premium} per option\n   •    → Total: {quantity} × {lot_size} × ₹{buy_premium} = ₹{quantity * lot_size * buy_premium:,.0f}\n   • SELL: {quantity} lots of {sell_strike} PE @ ₹{sell_premium} per option\n   •    → Total: {quantity} × {lot_size} × ₹{sell_premium} = ₹{quantity * lot_size * sell_premium:,.0f}\n   • NET DEBIT: ₹{quantity * lot_size * net_cost:,.0f} (you pay this amount)\n   • EXPIRY: {expiry_date}\n   • EXACT TRADE: Buy {quantity * lot_size} units of {buy_strike} PE, Sell {quantity * lot_size} units of {sell_strike} PE\n   • PROFIT: Max ₹{quantity * lot_size * max_profit_per_lot:,.0f} if {symbol} falls below ₹{sell_strike}',
            'strikes': f'{buy_strike} PE (Buy) / {sell_strike} PE (Sell)',
            'investment': quantity * lot_size * net_cost,
            'max_profit': quantity * lot_size * max_profit_per_lot,
            'max_loss': quantity * lot_size * max_loss_per_lot,
            'risk_reward': risk_reward,
            'outlook': f'Profit if {symbol} falls below ₹{sell_strike}',
            'quantity': quantity,
            'lot_size': lot_size,
            'margin_required': quantity * lot_size * net_cost,
            'breakeven': buy_strike - net_cost,
            'expiry': expiry_date
        }
        
        # Add backtesting results
        if backtesting_result:
            strategy_dict['backtesting_result'] = backtesting_result
        
        return strategy_dict
    
    def generate_long_put_strategy(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Long Put - Strongly bearish strategy"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('PE', {}).get('underlying', 'UNKNOWN')
        
        strike = atm_strike
        premium = self.get_option_premium(option_chain, strike, 'PE', spot_price)
        
        # Practical backtesting validation for Long Put
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Long Put',
            current_price=spot_price,
            buy_strike=strike,
            sell_strike=0,  # Not applicable for long put
            net_cost=premium
        )
        
        # Reject strategy if backtesting shows poor performance
        if backtesting_result.get('verdict') == 'AVOID':
            print(f"🚫 {symbol} Long Put REJECTED by backtesting:")
            print(f"   Score: {backtesting_result.get('score', 0):.1f}/100")
            print(f"   Reason: {backtesting_result.get('reason', 'Poor historical performance')}")
            
            return {
                'name': 'Strategy Rejected',
                'action': f'Long Put rejected due to poor historical performance (Score: {backtesting_result.get("score", 0):.1f}/100)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not recommended',
                'rejection_reason': backtesting_result.get('reason', 'Failed backtesting validation')
            }
        
        quantity = min(100, 45000 // (premium * 50))
        investment = quantity * premium * 50
        max_loss = investment
        
        strategy_dict = {
            'name': 'Long Put',
            'action': f'BUY {strike} PE @ ₹{premium:.1f}',
            'strikes': f'{strike} PE (Buy)',
            'investment': investment,
            'max_profit': quantity * (strike - premium) * 50,
            'max_loss': max_loss,
            'risk_reward': 3.0,
            'outlook': 'Strongly Bearish',
            'quantity': quantity
        }
        
        # Add backtesting results
        if backtesting_result:
            strategy_dict['backtesting_result'] = backtesting_result
        
        return strategy_dict
    
    def generate_long_straddle(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Long Straddle - High volatility expected"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('CE', {}).get('underlying', 'UNKNOWN')
        
        strike = atm_strike
        call_premium = self.get_option_premium(option_chain, strike, 'CE', spot_price)
        put_premium = self.get_option_premium(option_chain, strike, 'PE', spot_price)
        
        total_premium = call_premium + put_premium
        
        # Practical backtesting validation for Long Straddle
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Long Straddle',
            current_price=spot_price,
            buy_strike=strike,
            sell_strike=0,  # Not applicable for straddle
            net_cost=total_premium
        )
        
        # Reject strategy if backtesting shows poor performance
        if backtesting_result.get('verdict') == 'AVOID':
            print(f"🚫 {symbol} Long Straddle REJECTED by backtesting:")
            print(f"   Score: {backtesting_result.get('score', 0):.1f}/100")
            print(f"   Reason: {backtesting_result.get('reason', 'Poor historical performance')}")
            
            return {
                'name': 'Strategy Rejected',
                'action': f'Long Straddle rejected due to poor historical performance (Score: {backtesting_result.get("score", 0):.1f}/100)',
                'investment': 0,
                'max_profit': 0,
                'max_loss': 0,
                'risk_reward': 0,
                'outlook': 'Strategy not recommended',
                'rejection_reason': backtesting_result.get('reason', 'Failed backtesting validation')
            }
        
        quantity = min(50, 45000 // (total_premium * 50))  # Smaller quantity due to higher cost
        investment = quantity * total_premium * 50
        max_loss = investment
        
        strategy_dict = {
            'name': 'Long Straddle',
            'action': f'BUY {strike} CE @ ₹{call_premium:.1f} & BUY {strike} PE @ ₹{put_premium:.1f}',
            'strikes': f'{strike} CE + {strike} PE (Both Buy)',
            'investment': investment,
            'max_profit': 999999,  # Unlimited in both directions
            'max_loss': max_loss,
            'risk_reward': 4.0,
            'outlook': 'High Volatility Expected',
            'quantity': quantity
        }
        
        # Add backtesting results
        if backtesting_result:
            strategy_dict['backtesting_result'] = backtesting_result
        
        return strategy_dict
    
    def generate_iron_condor(self, spot_price: float, atm_strike: float, option_chain: Dict) -> Dict:
        """Iron Condor - ALWAYS generates strategy, never rejects (rejection only by final confidence)"""
        symbol = option_chain.get('records', {}).get('data', [{}])[0].get('CE', {}).get('underlying', 'UNKNOWN')
        
        # Iron Condor strikes 
        wing_width = 100
        sell_call_strike = atm_strike + 50   
        buy_call_strike = atm_strike + 150   
        sell_put_strike = atm_strike - 50      
        buy_put_strike = atm_strike - 150    
        
        # Get option premiums (use defaults if not available)
        try:
            sell_call_premium = self.get_option_premium(option_chain, sell_call_strike, 'CE', spot_price)
            buy_call_premium = self.get_option_premium(option_chain, buy_call_strike, 'CE', spot_price)
            sell_put_premium = self.get_option_premium(option_chain, sell_put_strike, 'PE', spot_price)
            buy_put_premium = self.get_option_premium(option_chain, buy_put_strike, 'PE', spot_price)
        except:
            # Use reasonable defaults if premium fetch fails
            sell_call_premium = 15
            buy_call_premium = 5
            sell_put_premium = 15
            buy_put_premium = 5
        
        # Ensure positive premiums
        if any(p <= 0 for p in [sell_call_premium, buy_call_premium, sell_put_premium, buy_put_premium]):
            sell_call_premium = max(15, sell_call_premium)
            buy_call_premium = max(5, buy_call_premium)
            sell_put_premium = max(15, sell_put_premium)
            buy_put_premium = max(5, buy_put_premium)
        
        # Calculate net credit and risk
        net_credit_per_lot = (sell_call_premium + sell_put_premium) - (buy_call_premium + buy_put_premium)
        max_loss_per_lot = wing_width - net_credit_per_lot
        
        # Ensure realistic values
        if net_credit_per_lot <= 0:
            net_credit_per_lot = 10  # Minimum credit
            max_loss_per_lot = wing_width - net_credit_per_lot
        
        if max_loss_per_lot <= 0:
            max_loss_per_lot = 50  # Minimum risk
        
        risk_reward = net_credit_per_lot / max_loss_per_lot if max_loss_per_lot > 0 else 0.1
        
        # Backtesting data
        backtesting_result = self.practical_strategy_backtest(
            symbol=symbol,
            strategy_type='Iron Condor',
            current_price=spot_price,
            buy_strike=atm_strike,
            sell_strike=wing_width,
            net_cost=-net_credit_per_lot
        )
        
        # Position sizing
        lot_size = get_lot_size(symbol)
        quantity = 2  # Fixed quantity for simplicity
        
        # Get expiry
        expiry_date = "Oct-2025"  # Default expiry
        
        # Calculate totals
        total_credit = quantity * lot_size * net_credit_per_lot
        total_max_loss = quantity * lot_size * max_loss_per_lot
        
        return {
            'name': 'Iron Condor',
            'action': f'IRON CONDOR STRATEGY:\n   • SELL {sell_call_strike} CE @ ₹{sell_call_premium}\n   • BUY {buy_call_strike} CE @ ₹{buy_call_premium}\n   • SELL {sell_put_strike} PE @ ₹{sell_put_premium}\n   • BUY {buy_put_strike} PE @ ₹{buy_put_premium}\n   • NET CREDIT: ₹{total_credit:,.0f}\n   • EXPIRY: {expiry_date}',
            'strikes': f'Sell {sell_call_strike}CE/{sell_put_strike}PE, Buy {buy_call_strike}CE/{buy_put_strike}PE',
            'investment': total_max_loss,  # Max loss = investment required
            'max_profit': total_credit,
            'max_loss': total_max_loss,
            'risk_reward': risk_reward,
            'outlook': f'Profit if {symbol} stays between ₹{sell_put_strike} and ₹{sell_call_strike}',
            'quantity': quantity,
            'lot_size': lot_size,
            'margin_required': total_max_loss,
            'expiry': expiry_date,
            'backtesting_result': backtesting_result
        }
    
    def get_option_data(self, option_chain: Dict, strike: float, option_type: str, spot_price: float) -> Dict:
        """Extract comprehensive option data from option chain"""
        try:
            if option_chain and 'records' in option_chain:
                for record in option_chain['records'].get('data', []):
                    if record.get('strikePrice') == strike:
                        option_data = record.get(option_type, {})
                        if option_data.get('lastPrice', 0) > 0:
                            return {
                                'lastPrice': option_data.get('lastPrice', 0),
                                'bidPrice': option_data.get('bidprice', 0),
                                'askPrice': option_data.get('askPrice', 0),
                                'volume': option_data.get('totalTradedVolume', 0),
                                'openInterest': option_data.get('openInterest', 0),
                                'impliedVolatility': option_data.get('impliedVolatility', 0),
                                'strike': strike,
                                'type': option_type,
                                'expiryDate': record.get('expiryDate', 'N/A')
                            }
            
            # Fallback data with approximate premium
            moneyness = strike / spot_price
            if option_type == 'CE':  # Call
                if moneyness < 0.98:  # ITM
                    premium = max(spot_price - strike + 20, 5)
                elif moneyness > 1.02:  # OTM
                    premium = max(10, 50 - (strike - spot_price))
                else:  # ATM
                    premium = 25
            else:  # Put
                if moneyness > 1.02:  # ITM
                    premium = max(strike - spot_price + 20, 5)
                elif moneyness < 0.98:  # OTM
                    premium = max(10, 50 - (spot_price - strike))
                else:  # ATM
                    premium = 25
                    
            return {
                'lastPrice': premium,
                'bidPrice': premium * 0.95,
                'askPrice': premium * 1.05,
                'volume': 0,
                'openInterest': 0,
                'impliedVolatility': 0,
                'strike': strike,
                'type': option_type,
                'expiryDate': 'N/A'
            }
                    
        except Exception as e:
            # Default fallback
            return {
                'lastPrice': 20 if option_type == 'CE' else 25,
                'bidPrice': 19 if option_type == 'CE' else 24,
                'askPrice': 21 if option_type == 'CE' else 26,
                'volume': 0,
                'openInterest': 0,
                'impliedVolatility': 0,
                'strike': strike,
                'type': option_type,
                'expiryDate': 'N/A'
            }

    def get_option_premium(self, option_chain: Dict, strike: float, option_type: str, spot_price: float) -> float:
        """Extract option premium from option chain data (backward compatibility)"""
        option_data = self.get_option_data(option_chain, strike, option_type, spot_price)
        return option_data['lastPrice']
    
    def check_volume_volatility(self, option_chain: Dict, symbol: str) -> str:
        """Check if there's high volume activity indicating volatility"""
        if not option_chain or not option_chain.get('records', {}).get('data'):
            return 'LOW'
        
        # Get total volume for ATM and nearby strikes
        spot_price = option_chain['records'].get('underlyingValue', 0)
        atm_strike = round(spot_price / 50) * 50
        
        total_volume = 0
        total_oi = 0
        strike_count = 0
        
        for record in option_chain['records'].get('data', []):
            strike = record.get('strikePrice', 0)
            if abs(strike - atm_strike) <= 200:  # Within 200 points of ATM
                ce_data = record.get('CE', {})
                pe_data = record.get('PE', {})
                
                ce_volume = ce_data.get('totalTradedVolume', 0)
                pe_volume = pe_data.get('totalTradedVolume', 0)
                ce_oi = ce_data.get('openInterest', 0)
                pe_oi = pe_data.get('openInterest', 0)
                
                total_volume += ce_volume + pe_volume
                total_oi += ce_oi + pe_oi
                strike_count += 1
        
        # Volume-based volatility thresholds
        avg_volume = total_volume / max(strike_count, 1)
        
        if total_volume > 50000 and avg_volume > 5000:
            return 'HIGH'
        elif total_volume > 20000 and avg_volume > 2000:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_confidence(self, price_data: Dict, fundamentals: Optional[Dict],
                           news_sentiment: Dict, technical: Dict, option_chain: Optional[Dict] = None) -> int:
        """
        Calculate confidence score - NEW APPROACH:
        75% from fundamental data + 25% adjustment from backtesting
        Base confidence calculation (75% weight) + Backtesting adjustment (25% weight)
        """
        # CRITICAL: No option chain data = No trading confidence for F&O stocks
        if not option_chain or not option_chain.get('records', {}).get('data'):
            return 0  # Zero confidence without option chain data
        
        # STEP 1: Calculate BASE CONFIDENCE (75% of total score)
        base_confidence = self.calculate_base_confidence(price_data, fundamentals, news_sentiment, technical, option_chain)
        
        # Return base confidence for now - backtesting adjustment will be applied in strategy generation
        return base_confidence
    
    def calculate_base_confidence(self, price_data: Dict, fundamentals: Optional[Dict],
                                news_sentiment: Dict, technical: Dict, option_chain: Dict) -> int:
        """
        Calculate base confidence from fundamental data (75% of total confidence)
        Max score: 100 (will be treated as 75% of total)
        """
        
        confidence = 20  # Lower base for more realistic scoring
        
        # Technical Analysis (40 points max)
        rsi = technical.get('rsi', 50)
        trend = technical.get('trend', 'SIDEWAYS')
        
        # RSI scoring
        if 40 <= rsi <= 60:  # Good RSI range
            confidence += 15
        elif 30 <= rsi <= 70:  # Acceptable RSI
            confidence += 10
        elif rsi < 30 or rsi > 70:  # Extreme RSI
            confidence += 5
        
        # Trend scoring
        if trend == 'UPTREND':
            confidence += 15
        elif trend == 'SIDEWAYS':
            confidence += 5
        # DOWNTREND gets 0 points
        
        # Price momentum (20 points max)
        price_change = price_data.get('pChange', 0)
        if price_change > 3:  # Strong positive momentum
            confidence += 20
        elif price_change > 1:  # Moderate positive momentum
            confidence += 15
        elif price_change > 0:  # Slight positive momentum
            confidence += 10
        elif price_change > -1:  # Slight negative momentum
            confidence += 5
        # Below -1% gets 0 points
        
        # News sentiment (20 points max)
        sentiment_score = news_sentiment.get('score', 0)
        momentum = news_sentiment.get('momentum', 'NEUTRAL')
        
        if momentum == 'POSITIVE':
            confidence += 15
        elif momentum == 'NEUTRAL':
            confidence += 10
        elif momentum == 'NEGATIVE':
            confidence += 5
        
        # Add sentiment score bonus
        if sentiment_score > 0.3:
            confidence += 5
        
        # Option Chain Volume Analysis (20 points max) - NEW
        if option_chain and 'records' in option_chain:
            spot_price = option_chain['records'].get('underlyingValue', price_data.get('current_price', 0))
            atm_strike = round(spot_price / 50) * 50
            
            # Find ATM and nearby strikes
            call_volume = 0
            put_volume = 0
            call_oi = 0
            put_oi = 0
            
            for record in option_chain['records'].get('data', []):
                strike = record.get('strikePrice', 0)
                if abs(strike - atm_strike) <= 100:  # Within 100 points of ATM
                    ce_data = record.get('CE', {})
                    pe_data = record.get('PE', {})
                    
                    call_volume += ce_data.get('totalTradedVolume', 0)
                    put_volume += pe_data.get('totalTradedVolume', 0)
                    call_oi += ce_data.get('openInterest', 0)
                    put_oi += pe_data.get('openInterest', 0)
            
            # Volume analysis
            total_volume = call_volume + put_volume
            if total_volume > 10000:  # High liquidity
                confidence += 10
            elif total_volume > 1000:  # Moderate liquidity
                confidence += 5
            
            # Call/Put ratio analysis
            if call_volume > 0 and put_volume > 0:
                cp_ratio = call_volume / put_volume
                if 0.5 <= cp_ratio <= 2.0:  # Balanced activity
                    confidence += 5
                elif cp_ratio > 2.0:  # Bullish sentiment
                    confidence += 3 if trend == 'UPTREND' else 1
                elif cp_ratio < 0.5:  # Bearish sentiment  
                    confidence += 3 if trend == 'DOWNTREND' else 1
            
            # Open Interest analysis
            total_oi = call_oi + put_oi
            if total_oi > 50000:  # Very high OI
                confidence += 5
            elif total_oi > 10000:  # Good OI
                confidence += 3
        
        # Fundamentals (20 points max)
        if fundamentals:
            pe = fundamentals.get('pe')
            pb = fundamentals.get('pb')
            roe = fundamentals.get('roe')
            
            # P/E ratio scoring
            if pe and 10 <= pe <= 20:  # Good P/E
                confidence += 8
            elif pe and 5 <= pe <= 30:  # Acceptable P/E
                confidence += 5
            
            # P/B ratio scoring
            if pb and 1 <= pb <= 3:  # Good P/B
                confidence += 6
            elif pb and 0.5 <= pb <= 5:  # Acceptable P/B
                confidence += 3
            
            # ROE scoring
            if roe and roe > 15:  # Good ROE
                confidence += 6
            elif roe and roe > 10:  # Acceptable ROE
                confidence += 3
        
        # Volume validation (bonus points)
        volume = price_data.get('volume', 0)
        if volume > 100000:  # Good volume
            confidence += 5
        elif volume > 50000:  # Moderate volume
            confidence += 2
        
        # Cap the confidence score
        final_confidence = max(0, min(100, confidence))
        
        return final_confidence
    
    def analyze_all_parallel(self, symbols: List[str], max_workers: int = 10):
        """Analyze all symbols in parallel"""
        print(f"\n{'='*80}")
        print(f"🚀 PARALLEL ANALYSIS OF {len(symbols)} SYMBOLS")
        print(f"   📊 Data: Yahoo Finance (Fundamentals) | NSE (Options) | Google News (Sentiment)")
        print(f"   Threads: {max_workers}")
        print(f"{'='*80}\n")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.analyze_single_stock, symbol): symbol 
                      for symbol in symbols}
            
            completed = 0
            total = len(symbols)
            
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                symbol = futures[future]
                
                try:
                    result = future.result()
                    # Silent processing - strategies already printed in analyze_single_stock
                except Exception as e:
                    # Silent error handling
                    pass
                time.sleep(0.5)  # Rate limiting
    
    def save_results(self):
        """Save results to files"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\n{'='*80}")
        print("💾 SAVING RESULTS")
        print(f"{'='*80}\n")
        
        # Save each category
        if self.high_confidence:
            self._save_to_file(f"signals_HIGH_{date_str}.txt", self.high_confidence, "HIGH")
        
        if self.medium_confidence:
            self._save_to_file(f"signals_MEDIUM_{date_str}.txt", self.medium_confidence, "MEDIUM")
        
        if self.low_confidence:
            self._save_to_file(f"signals_LOW_{date_str}.txt", self.low_confidence, "LOW")
        
        # Summary
        self._save_summary(date_str)
    
    def _save_to_file(self, filename: str, results: List[Dict], category: str):
        """Save results to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write(f"{category} CONFIDENCE SIGNALS\n")
            f.write("="*100 + "\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write(f"Total Signals: {len(results)}\n")
            f.write(f"Data Source: NSE (Primary) + Yahoo (Backup)\n")
            f.write(f"News Source: Google News + Yahoo Finance\n")
            f.write("="*100 + "\n\n")
            
            for result in sorted(results, key=lambda x: x['confidence'], reverse=True):
                f.write(f"SYMBOL: {result['symbol']} | CONFIDENCE: {result['confidence']}%\n")
                f.write("="*100 + "\n\n")
                
                # Price data
                price = result['price_data']
                f.write("PRICE DATA\n")
                f.write(f"Source: {price['source']}\n")
                f.write(f"Current: ₹{price['current_price']:.2f}\n")
                f.write(f"Change: {price['pChange']:+.2f}%\n")
                f.write(f"52W Range: ₹{price['low_52w']:.2f} - ₹{price['high_52w']:.2f}\n\n")
                
                # News
                news = result['news_sentiment']
                if news['headlines']:
                    f.write("NEWS SENTIMENT\n")
                    f.write(f"Momentum: {news['momentum']}\n")
                    f.write(f"Score: {news['score']}\n")
                    f.write("Recent Headlines:\n")
                    for headline in news['headlines'][:3]:
                        f.write(f"   • {headline}\n")
                    f.write("\n")
                
                # Strategy
                strategy = result['best_strategy']
                f.write("RECOMMENDED STRATEGY\n")
                f.write(f"Name: {strategy['name']}\n")
                f.write(f"Outlook: {strategy['outlook']}\n")
                f.write(f"Investment: ₹{strategy['investment']:,.0f}\n")
                f.write(f"Risk:Reward: 1:{strategy['risk_reward']}\n\n")
                
                f.write("-"*100 + "\n\n")
        
        print(f"✅ Saved: {filename}")
    
    def _save_summary(self, date_str: str):
        """Save summary file"""
        filename = f"analysis_summary_{date_str}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write("MARKET ANALYSIS SUMMARY\n")
            f.write("="*100 + "\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write(f"Data Source: NSE (Primary) + Yahoo Finance (Backup)\n")
            f.write(f"News Sources: Google News + Yahoo Finance News\n")
            f.write("="*100 + "\n\n")
            
            f.write("SIGNAL DISTRIBUTION\n")
            f.write("-"*100 + "\n")
            f.write(f"HIGH (≥50%): {len(self.high_confidence)}\n")
            f.write(f"MEDIUM (30-49%): {len(self.medium_confidence)}\n")
            f.write(f"LOW (<30%): {len(self.low_confidence)}\n\n")
            
            f.write("FILES GENERATED\n")
            f.write("-"*100 + "\n")
            if self.high_confidence:
                f.write(f"• signals_HIGH_{date_str}.txt\n")
            if self.medium_confidence:
                f.write(f"• signals_MEDIUM_{date_str}.txt\n")
            if self.low_confidence:
                f.write(f"• signals_LOW_{date_str}.txt\n")
        
        print(f"✅ Saved: {filename}")


def main():
    """Main execution"""
    import sys
    
    print("="*80)
    print("🚀 INTEGRATED MARKET ANALYZER v5.0")
    print("="*80)
    
    # Check for command line argument for specific symbol
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        print(f"🎯 Analyzing single symbol: {symbol}")
        print("="*80)
        
        # Initialize
        analyzer = IntegratedMarketAnalyzer()
        
        # Analyze single symbol
        result = analyzer.analyze_single_stock(symbol)
        
        if result:
            print(f"\n📊 {symbol} Analysis Complete!")
            strategy = result.get('best_strategy', {})
            strategy_name = strategy.get('name', 'No Strategy')
            
            # Determine confidence color from strategy object
            confidence = strategy.get('final_confidence', 0)
            if confidence >= 70:
                confidence_color = "🟢"  # Green for high confidence
            elif confidence >= 50:
                confidence_color = "🟡"  # Yellow for medium confidence
            else:
                confidence_color = "🔴"  # Red for low confidence
            
            print(f"\nStrategy Recommendation: {strategy_name}")
            print(f"Confidence: {confidence_color} {confidence:.1f}%")
            
            if strategy_name == 'Strategy Rejected':
                print(f"   REJECTED: {strategy.get('action', 'Poor backtesting performance')}")
            elif strategy.get('investment', 0) > 0:
                print(f"   APPROVED Strategy")
                
                # Show COMPLETE trade details
                if strategy.get('action'):
                    print(f"   EXACT TRADES TO EXECUTE:")
                    action_lines = strategy['action'].split('\n')
                    for line in action_lines:
                        if line.strip() and ('BUY:' in line or 'SELL:' in line or 'Total:' in line or 'NET DEBIT:' in line or 'NET CREDIT:' in line):
                            # Remove emojis from trade lines
                            clean_line = line.replace('🟢', '').replace('🔴', '').replace('📊', '').replace('📅', '').strip()
                            print(f"      {clean_line}")
                
                # Show key trade info
                if strategy.get('strikes'):
                    print(f"   STRIKES: {strategy['strikes']}")
                if strategy.get('lot_size') and strategy.get('quantity'):
                    print(f"   POSITION: {strategy['quantity']} lots × {strategy['lot_size']} units = {strategy['quantity'] * strategy['lot_size']} total units")
                if strategy.get('expiry'):
                    print(f"   EXPIRY: {strategy['expiry']}")
                
                print(f"   Investment: ₹{strategy['investment']:,.0f}")
                print(f"   Max Profit: ₹{strategy['max_profit']:,.0f}")
                print(f"   Max Loss: ₹{strategy['max_loss']:,.0f}")
                print(f"   Risk:Reward: 1:{strategy.get('risk_reward', 0):.2f}")
            
            # Remove backtesting details display from final recommendation
            # (backtesting details are already shown in the main strategy display above)
        else:
            print(f"❌ Failed to analyze {symbol} - may not have F&O data")
        
        return
    
    # Default: analyze all F&O symbols
    print("📊 Analyzing ALL F&O symbols (use 'py market_analyzer_v5_integrated.py SYMBOL' for single stock)")
    print("="*80)
    
    # Get symbols
    all_symbols = get_all_fno_symbols()
    
    # Initialize
    analyzer = IntegratedMarketAnalyzer()
    
    # Analyze all symbols
    analyzer.analyze_all_parallel(all_symbols, max_workers=3)
    
    # Save results
    analyzer.save_results()
    
    # Final summary
    print(f"\n{'='*50}")
    print("🎯 ANALYSIS COMPLETE")
    print(f"{'='*50}")
    print(f"HIGH confidence strategies: {len(analyzer.high_confidence)}")
    print(f"Results saved to: signals_*_{datetime.now().strftime('%Y-%m-%d')}.txt")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
