# NSE F&O Lot Sizes (as of October 2025)
# Source: NSE official F&O lot size data

FNO_LOT_SIZES = {
    # Major Stocks
    'RELIANCE': 250,
    'TCS': 150,
    'INFY': 300,
    'HDFCBANK': 550,
    'ICICIBANK': 1375,
    'HINDUNILVR': 300,
    'ITC': 1600,
    'SBIN': 1500,
    'BHARTIARTL': 1800,
    'ASIANPAINT': 150,
    'MARUTI': 100,
    'AXISBANK': 1200,
    'LT': 225,
    'TITAN': 294,
    'ULTRACEMCO': 100,
    'WIPRO': 1200,
    'ADANIPORTS': 1200,
    'ADANIENT': 400,
    'APOLLOHOSP': 125,
    'BAJAJ-AUTO': 250,
    'BAJFINANCE': 125,
    'BAJAJFINSV': 500,
    'BPCL': 2400,
    'BRITANNIA': 200,
    'CIPLA': 800,
    'COALINDIA': 4000,
    'DIVISLAB': 300,
    'DRREDDY': 125,
    'EICHERMOT': 250,
    'GRASIM': 600,
    'HCLTECH': 700,
    'HEROMOTOCO': 600,
    'HINDALCO': 2000,
    'INDUSINDBK': 900,
    'KOTAKBANK': 400,
    'JSWSTEEL': 1500,
    'M&M': 600,
    'NTPC': 4000,
    'NESTLEIND': 50,
    'ONGC': 4000,
    'POWERGRID': 2700,
    'SUNPHARMA': 1000,
    'TATACONSUM': 1200,
    'TATAMOTORS': 3000,
    'TATASTEEL': 800,
    'TECHM': 600,
    'UPL': 1500,
    
    # Indices (Value in index points, not lot size)
    'NIFTY': 25,      # ₹25 per point
    'BANKNIFTY': 15,  # ₹15 per point
    'FINNIFTY': 25,   # ₹25 per point
    'MIDCPNIFTY': 50, # ₹50 per point
    
    # Default for unknown stocks
    'DEFAULT': 1000
}

def get_lot_size(symbol: str) -> int:
    """Get the lot size for a given F&O symbol"""
    return FNO_LOT_SIZES.get(symbol.upper(), FNO_LOT_SIZES['DEFAULT'])

def is_index(symbol: str) -> bool:
    """Check if symbol is an index"""
    indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTYNXT50']
    return symbol.upper() in indices