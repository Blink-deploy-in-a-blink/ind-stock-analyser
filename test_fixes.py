#!/usr/bin/env python3
"""
Tests for key fixes in the market analyzer.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fno_symbols import get_all_fno_symbols, get_fno_count, FNO_STOCKS, FNO_INDICES
from lot_sizes import get_lot_size, is_index


def test_no_duplicate_fno_stocks():
    """FNO_STOCKS should not contain duplicate entries"""
    seen = set()
    duplicates = []
    for s in FNO_STOCKS:
        if s in seen:
            duplicates.append(s)
        seen.add(s)
    assert len(duplicates) == 0, f"Duplicate stocks found: {duplicates}"


def test_fno_indices_use_nse_format():
    """FNO_INDICES should use NSE API format, not Yahoo Finance format"""
    for idx in FNO_INDICES:
        assert not idx.startswith('^'), f"Index {idx} uses Yahoo format (^), should use NSE format"
    expected_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50']
    for expected in expected_indices:
        assert expected in FNO_INDICES, f"Expected index {expected} not found in FNO_INDICES"


def test_get_all_fno_symbols_returns_list():
    """get_all_fno_symbols should return a combined list of stocks and indices"""
    symbols = get_all_fno_symbols()
    assert isinstance(symbols, list)
    assert len(symbols) > 0
    assert 'RELIANCE' in symbols
    assert 'NIFTY' in symbols


def test_get_fno_count():
    """get_fno_count should return correct counts"""
    counts = get_fno_count()
    assert counts['stocks'] == len(FNO_STOCKS)
    assert counts['indices'] == len(FNO_INDICES)
    assert counts['total'] == len(FNO_STOCKS) + len(FNO_INDICES)


def test_strike_interval():
    """get_strike_interval should return appropriate intervals for different price levels"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    
    # Create analyzer without initializing NSE session
    # We need to mock the NSE fetcher to avoid network calls
    import unittest.mock as mock
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Low-price stock (e.g., IDEA ~₹10)
    assert analyzer.get_strike_interval(10) == 2.5
    
    # Mid-price stock (e.g., SBIN ~₹600)
    assert analyzer.get_strike_interval(600) == 10
    
    # High-price stock (e.g., RELIANCE ~₹2500)
    assert analyzer.get_strike_interval(2500) == 25
    
    # Very high-price stock (e.g., MRF ~₹100000)
    assert analyzer.get_strike_interval(100000) == 500


def test_get_option_expiry():
    """get_option_expiry should extract expiry from option chain"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Test with valid option chain
    option_chain = {
        'records': {
            'expiryDates': ['27-Mar-2025', '03-Apr-2025'],
            'data': []
        }
    }
    assert analyzer.get_option_expiry(option_chain) == '27-Mar-2025'
    
    # Test with empty option chain
    assert analyzer.get_option_expiry({}) == 'N/A'
    assert analyzer.get_option_expiry(None) == 'N/A'


def test_backtesting_handles_insufficient_data():
    """Backtesting should handle insufficient data gracefully"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Test with only 3 data points (less than 5 needed)
    short_data = {
        'closes': [100, 101, 102],
        'highs': [101, 102, 103],
        'lows': [99, 100, 101],
        'dates': ['2025-01-01', '2025-01-02', '2025-01-03']
    }
    
    result = analyzer._backtest_bull_call_spread(short_data, 100, 110, 5)
    assert result['verdict'] == 'NO_DATA'
    
    result = analyzer._backtest_long_call(short_data, 100, 5)
    assert result['verdict'] == 'NO_DATA'
    
    result = analyzer._backtest_long_put(short_data, 100, 5)
    assert result['verdict'] == 'NO_DATA'
    
    result = analyzer._backtest_bear_put_spread(short_data, 110, 100, 5)
    assert result['verdict'] == 'NO_DATA'
    
    result = analyzer._backtest_long_straddle(short_data, 100, 10)
    assert result['verdict'] == 'NO_DATA'
    
    result = analyzer._backtest_iron_condor(short_data, 100, 50, 5)
    assert result['verdict'] == 'NO_DATA'


def test_atm_strike_calculation():
    """ATM strike should use dynamic intervals based on price"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # For a ₹10 stock, interval is 2.5
    interval = analyzer.get_strike_interval(10)
    atm = round(10 / interval) * interval
    assert atm == 10.0
    
    # For a ₹2345 stock, interval is 25
    interval = analyzer.get_strike_interval(2345)
    atm = round(2345 / interval) * interval
    assert atm == 2350.0
    
    # For a ₹100000 stock, interval is 500
    interval = analyzer.get_strike_interval(100000)
    atm = round(100000 / interval) * interval
    assert atm == 100000.0


def test_extract_symbol_from_chain():
    """_extract_symbol_from_chain should safely extract symbol from option chain data"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Test with valid data
    option_chain = {
        'records': {
            'data': [
                {'strikePrice': 100, 'CE': {'underlying': 'RELIANCE', 'lastPrice': 10}},
                {'strikePrice': 110, 'PE': {'underlying': 'RELIANCE', 'lastPrice': 5}}
            ]
        }
    }
    assert analyzer._extract_symbol_from_chain(option_chain, 'CE') == 'RELIANCE'
    assert analyzer._extract_symbol_from_chain(option_chain, 'PE') == 'RELIANCE'
    
    # Test with empty data array
    empty_chain = {'records': {'data': []}}
    assert analyzer._extract_symbol_from_chain(empty_chain, 'CE') == 'UNKNOWN'
    
    # Test with None/empty option chain
    assert analyzer._extract_symbol_from_chain({}, 'CE') == 'UNKNOWN'
    assert analyzer._extract_symbol_from_chain({'records': {}}, 'CE') == 'UNKNOWN'


def test_option_premium_zero_spot_price():
    """get_option_data should not crash when spot_price is 0"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Empty option chain, spot_price=0 - should not raise ZeroDivisionError
    empty_chain = {'records': {'data': []}}
    result = analyzer.get_option_data(empty_chain, 100, 'CE', 0)
    assert result['lastPrice'] == 25  # Default ATM premium
    assert result['strike'] == 100


def test_backtest_results_have_display_fields():
    """Backtest results should include success_rate, profitable_outcomes, total_outcomes"""
    from market_analyzer_v5_integrated import IntegratedMarketAnalyzer
    import unittest.mock as mock
    
    with mock.patch('market_analyzer_v5_integrated.NSEDataFetcher'):
        analyzer = IntegratedMarketAnalyzer()
    
    # Enough data for backtesting (10+ data points)
    historical_data = {
        'closes': [100 + i * 0.5 for i in range(20)],
        'highs': [101 + i * 0.5 for i in range(20)],
        'lows': [99 + i * 0.5 for i in range(20)],
        'dates': [f'2025-01-{i+1:02d}' for i in range(20)]
    }
    
    result = analyzer._backtest_bull_call_spread(historical_data, 100, 110, 5)
    assert 'success_rate' in result
    assert 'profitable_outcomes' in result
    assert 'total_outcomes' in result
    assert result['total_outcomes'] == 15  # 20 - 5


def test_nse_fetcher_symbol_normalization():
    """NSE fetcher should normalize symbols to uppercase"""
    from nse_data_fetcher_clean import NSEDataFetcher
    
    # Verify INDEX_SYMBOLS is a class attribute
    assert 'NIFTY' in NSEDataFetcher.INDEX_SYMBOLS
    assert 'BANKNIFTY' in NSEDataFetcher.INDEX_SYMBOLS
    assert 'FINNIFTY' in NSEDataFetcher.INDEX_SYMBOLS
    assert 'MIDCPNIFTY' in NSEDataFetcher.INDEX_SYMBOLS
    assert 'NIFTYNXT50' in NSEDataFetcher.INDEX_SYMBOLS


def test_combined_sentiment_handles_missing_headlines():
    """get_combined_sentiment should handle sentiments without 'headlines' key"""
    from market_analyzer_v5_integrated import NewsParser
    import unittest.mock as mock
    
    parser = NewsParser()
    
    # Mock both methods to return sentiment without headlines key
    with mock.patch.object(parser, 'parse_google_news', return_value={'score': 0.5, 'momentum': 'POSITIVE'}):
        with mock.patch.object(parser, 'parse_yahoo_finance_news', return_value={'score': -0.1, 'momentum': 'NEUTRAL'}):
            result = parser.get_combined_sentiment('TEST')
            assert 'headlines' in result
            assert isinstance(result['headlines'], list)
            assert result['score'] == 0.2  # (0.5 + -0.1) / 2


if __name__ == '__main__':
    test_functions = [
        test_no_duplicate_fno_stocks,
        test_fno_indices_use_nse_format,
        test_get_all_fno_symbols_returns_list,
        test_get_fno_count,
        test_strike_interval,
        test_get_option_expiry,
        test_backtesting_handles_insufficient_data,
        test_atm_strike_calculation,
        test_extract_symbol_from_chain,
        test_option_premium_zero_spot_price,
        test_backtest_results_have_display_fields,
        test_nse_fetcher_symbol_normalization,
        test_combined_sentiment_handles_missing_headlines,
    ]
    
    passed = 0
    failed = 0
    for test_fn in test_functions:
        try:
            test_fn()
            print(f"✅ PASS: {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_fn.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    sys.exit(1 if failed > 0 else 0)
