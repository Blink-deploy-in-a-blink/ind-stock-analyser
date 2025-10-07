"""
Complete F&O Stocks and Indices List for Indian Market
Last Updated: October 2024
"""

# All NSE F&O Stocks (184+ stocks)
FNO_STOCKS = [
    # A
    'ACC', 'ADANIENT', 'ADANIPORTS', 'ABCAPITAL', 'ABFRL', 'ALKEM', 'AMBUJACEM',
    'APOLLOHOSP', 'APOLLOTYRE', 'ASHOKLEY', 'ASIANPAINT', 'ASTRAL', 'ATUL', 
    'AUROPHARMA', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 
    'BALKRISIND', 'BALRAMCHIN', 'BANDHANBNK', 'BANKBARODA', 'BATAINDIA',
    
    # B-C
    'BEL', 'BERGEPAINT', 'BHARATFORG', 'BHARTIARTL', 'BHEL', 'BIOCON', 
    'BOSCHLTD', 'BPCL', 'BRITANNIA', 'BSOFT', 'CANBK', 'CANFINHOME', 
    'CHAMBLFERT', 'CHOLAFIN', 'CIPLA', 'COALINDIA', 'COFORGE', 'COLPAL',
    'CONCOR', 'COROMANDEL', 'CROMPTON', 'CUB', 'CUMMINSIND', 'DABUR',
    
    # D-E
    'DALBHARAT', 'DEEPAKNTR', 'DELTACORP', 'DIVISLAB', 'DIXON', 'DLF', 
    'DRREDDY', 'EICHERMOT', 'ESCORTS', 'EXIDEIND',
    
    # F-H
    'FEDERALBNK', 'GAIL', 'GLENMARK', 'GMRINFRA', 'GNFC', 'GODREJCP', 
    'GODREJPROP', 'GRANULES', 'GRASIM', 'GUJGASLTD', 'HAL', 'HAVELLS', 
    'HCLTECH', 'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 
    'HINDCOPPER', 'HINDPETRO', 'HINDUNILVR',
    
    # I
    'IBULHSGFIN', 'ICICIBANK', 'ICICIGI', 'ICICIPRULI', 'IDEA', 'IDFC', 
    'IDFCFIRSTB', 'IEX', 'IGL', 'INDHOTEL', 'INDIACEM', 'INDIAMART', 
    'INDIANB', 'INDIGO', 'INDUSINDBK', 'INDUSTOWER', 'INFY', 'INTELLECT',
    'IOC', 'IPCALAB', 'IRB', 'IRCTC', 'ITC', 'JINDALSTEL', 'JKCEMENT',
    'JSWSTEEL', 'JUBLFOOD', 'KOTAKBANK',
    
    # L
    'L&TFH', 'LALPATHLAB', 'LAURUSLABS', 'LICHSGFIN', 'LT', 'LTIM', 'LTTS',
    'LUPIN', 'LXCHEM',
    
    # M
    'M&M', 'M&MFIN', 'MANAPPURAM', 'MARICO', 'MARUTI', 'MCDOWELL-N', 
    'MCX', 'METROPOLIS', 'MFSL', 'MGL', 'MOTHERSON', 'MPHASIS', 'MRF', 
    'MUTHOOTFIN',
    
    # N-O
    'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NMDC', 'NTPC', 
    'OBEROIRLTY', 'OFSS', 'ONGC', 'PAGEIND', 'PEL', 'PERSISTENT', 
    'PETRONET', 'PFC', 'PIDILITIND', 'PIIND', 'PNB', 'POLYCAB', 'POWERGRID',
    
    # R
    'PVRINOX', 'RAMCOCEM', 'RBLBANK', 'RECLTD', 'RELIANCE', 'SAIL', 
    'SBICARD', 'SBILIFE', 'SBIN', 'SHREECEM', 'SHRIRAMFIN', 'SIEMENS', 
    'SRF', 'SUNPHARMA', 'SUNTV', 'SYNGENE',
    
    # T
    'TATACOMM', 'TATACONSUM', 'TATAMOTORS', 'TATAPOWER', 'TATASTEEL', 
    'TCS', 'TECHM', 'TITAN', 'TORNTPHARM', 'TORNTPOWER', 'TRENT', 'TVSMOTOR',
    
    # U-Z
    'UBL', 'ULTRACEMCO', 'UPL', 'VEDL', 'VOLTAS', 'WIPRO', 'ZEEL', 'ZYDUSLIFE',
    
    # Additional stocks with F&O
    'AARTIIND', 'ABBOTINDIA', 'ABFRL', 'ADANIENSOL', 'ADANIGREEN', 'ADANIPOWER',
    'AFFLE', 'AJANTPHARM', 'APLLTD', 'ANANDRATHI', 'APARINDS', 'ARE&M',
    'ASTRAZEN', 'AWL', 'BAJAJHLDNG', 'BASF', 'BATAINDIA', 'BAYERCROP',
    'BHARATFORG', 'BIKAJI', 'BLS', 'BRIGADE', 'BSE', 'CASTROLIND',
    'CEATLTD', 'CENTURYTEX', 'CGPOWER', 'CLEAN', 'COALINDIA', 'GODREJIND',
    'GODREJPROP', 'GRASIM', 'GSPL', 'GUJGASLTD', 'HAPPSTMNDS', 'HATSUN',
    'HONAUT', 'JBCHEPHARM', 'JKLAKSHMI', 'JKPAPER', 'JMFINANCIL', 'JSL',
    'KAJARIACER', 'KEI', 'KPITTECH', 'LICI', 'LODHA', 'MAHABANK',
    'MANAPPURAM', 'MANYAVAR', 'MAXHEALTH', 'MEDANTA', 'NAM-INDIA',
    'NATIONALUM', 'NAVINFLUOR', 'NSLNISP', 'OIL', 'PAYTM', 'PERSISTENT',
    'PETRONET', 'PHOENIXLTD', 'PNBHOUSING', 'POONAWALLA', 'RAIN',
    'RAJESHEXPO', 'RKFORGE', 'RTNINDIA', 'SCHNEIDER', 'SHARDACROP',
    'SJVN', 'SONACOMS', 'STARHEALTH', 'SUMICHEM', 'SUPREMEIND',
    'SUZLON', 'SWANENERGY', 'SYMPHONY', 'TATACHEM', 'TATAELXSI',
    'TATATECH', 'TIINDIA', 'TIMKEN', 'TRIDENT', 'UNIONBANK',
    'UNITDSPR', 'VBL', 'VEDL', 'WHIRLPOOL', 'YESBANK', 'ZFCVINDIA'
]

# All NSE Indices with F&O
FNO_INDICES = [
    '^NSEI',        # Nifty 50
    '^NSEBANK',     # Bank Nifty
    'NIFTYFIN',     # Nifty Financial Services
    'NIFTYMID',     # Nifty Midcap Select
    'NIFTYIT',      # Nifty IT
]

# Get all symbols (stocks + indices)
def get_all_fno_symbols():
    """Return complete list of F&O stocks and indices"""
    return FNO_STOCKS + FNO_INDICES

# Get count
def get_fno_count():
    """Return count of F&O symbols"""
    return {
        'stocks': len(FNO_STOCKS),
        'indices': len(FNO_INDICES),
        'total': len(FNO_STOCKS) + len(FNO_INDICES)
    }

if __name__ == "__main__":
    counts = get_fno_count()
    print(f"F&O Stocks: {counts['stocks']}")
    print(f"F&O Indices: {counts['indices']}")
    print(f"Total: {counts['total']}")
