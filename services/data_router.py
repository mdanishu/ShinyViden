
from openbb import obb
import pandas as pd
from datetime import datetime, timedelta
from services.openbb_manager import get_price_history as get_equity_history
from services.cache_manager import get_from_cache, set_to_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_EXPIRY_CRYPTO = 300 # 5 minutes for crypto (volatile)

def fetch_unified_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Unified fetcher for both Equity and Crypto.
    Detects asset class based on symbol format (e.g. 'BTC-USD' -> Crypto).
    
    Args:
        symbol: Ticker symbol (e.g. AAPL, BTC-USD)
        period: Time window ('1d', '1w', '1mo', '1y', '5y', '10y', 'max')
        interval: Data resolution ('1d', '1h', etc)
    """
    symbol = symbol.upper().strip()
    
    # Calculate start date from period
    start_date = calculate_start_date(period)
    
    # 1. Detect Asset Class
    is_crypto = symbol.endswith("-USD")
    
    # 2. Try Supabase First (Persisted "Researched" Data)
    # We map 'period' to data_manager semantics if needed, or just fetch 'All time' and filterdf
    # data_manager.fetch_ticker_data returns formatted DF with 'Date', 'Price' etc.
    # But this app expects 'date', 'close', 'high', 'low'...
    # We need to standardize. 
    # Let's import data_manager here to avoid circular imports at top level if any
    from services.data_manager import fetch_ticker_data, save_ticker_history
    
    df_supabase = pd.DataFrame()
    try:
        # Map period to data_manager strings
        sup_period = 'All time'
        if period == '1y': sup_period = '1 year'
        elif period == '5y': sup_period = '5 years'
        
        raw_sup = fetch_ticker_data(symbol, period=sup_period)
        if not raw_sup.empty:
            # Check staleness: Is the latest date recent?
            latest_date = raw_sup['Date'].max()
            if latest_date >= pd.Timestamp.now() - pd.Timedelta(days=2): # Allow weekends
                 logger.info(f"Supabase hit for {symbol}. Normalized logic applying.")
                 # Normalize column names from Supabase (Date, Price) -> (date, close)
                 df_supabase = raw_sup.rename(columns={
                     'Date': 'date', 
                     'Price': 'close',
                     '50d MA': 'ma_50', # Optional, filtering relies on 'close'
                     '200d MA': 'ma_200'
                 })
                 # Ensure proper index/columns
                 df_supabase = _normalize_frame(df_supabase)
    except Exception as e:
        logger.error(f"Supabase fetch error: {e}")

    if not df_supabase.empty:
        return df_supabase

    # 3. Fallback to OpenBB (Live/Cache)
    logger.info(f"Supabase miss/stale for {symbol}. Fetching live via OpenBB...")
    
    df = pd.DataFrame()
    if is_crypto:
        df = _fetch_crypto_history(symbol, start_date=start_date, interval=interval)
    else:
        # Default to Equity
        df = get_equity_history(symbol, interval=interval, start_date=start_date)
        if df.empty:
            # Fallback: User might have typed "BTC" instead of "BTC-USD"
            fallback_symbol = f"{symbol}-USD"
            logger.info(f"Equity fetch failed for {symbol}. Trying Crypto fallback: {fallback_symbol}")
            df = _fetch_crypto_history(fallback_symbol, start_date=start_date, interval=interval)
            if not df.empty: symbol = fallback_symbol # Update symbol for saving

    # Normalize BEFORE saving (Fixes KeyError: 'date' if Index is Date)
    df = _normalize_frame(df)

    # 4. Save to Supabase (Write-Behind)
    if not df.empty:
        try:
             logger.info(f"Saving new research for {symbol} to Supabase...")
             save_ticker_history(symbol, df)
        except Exception as e:
             logger.error(f"Failed to save to Supabase: {e}")
            
    return df

def calculate_start_date(period: str) -> str:
    """Converts period string to 'YYYY-MM-DD'."""
    today = datetime.now()
    
    if period == "1d":
        delta = timedelta(days=5) # Fetch a bit more context for charts
    elif period == "1w":
        delta = timedelta(weeks=1)
    elif period == "1m":
        delta = timedelta(days=30)
    elif period == "3m":
        delta = timedelta(days=90)
    elif period == "6m":
        delta = timedelta(days=180)
    elif period == "1y":
        delta = timedelta(days=365)
    elif period == "5y":
        delta = timedelta(days=365 * 5)
    elif period == "10y":
        delta = timedelta(days=365 * 10)
    else:
        # 'max' or unknown
        delta = timedelta(days=365 * 20)
        
    return (today - delta).strftime("%Y-%m-%d")

def _fetch_crypto_history(symbol: str, start_date: str, interval: str = "1d") -> pd.DataFrame:
    """
    Fetches crypto history via OpenBB (yfinance).
    """
    try:
        # Check Cache
        cached = get_from_cache("fetch_crypto_history", symbol=symbol, interval=interval, start_date=start_date)
        if cached is not None:
             logger.info(f"Cache hit for Crypto {symbol}")
             return pd.read_json(cached, orient='split')

        logger.info(f"Fetching Crypto {symbol} from yfinance (Start: {start_date})...")
        
        df = obb.crypto.price.historical(
            symbol=symbol,
            provider="yfinance",
            interval=interval,
            start_date=start_date
        ).to_df()
        
        # Cache normalized result
        df_norm = _normalize_frame(df)
        set_to_cache(df_norm.to_json(orient='split', date_format='iso'), "fetch_crypto_history", expire=CACHE_EXPIRY_CRYPTO, symbol=symbol, interval=interval, start_date=start_date)
        
        return df_norm

    except Exception as e:
        logger.error(f"Error fetching crypto {symbol}: {e}")
        return pd.DataFrame()

def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures DataFrame has standard columns: date, open, high, low, close, volume.
    OpenBB Providers might return 'Close', 'close', 'Adj Close', etc.
    """
    if df.empty: return df
    
    # Reset index if date is in index
    if 'date' not in df.columns:
        df = df.reset_index()
        # Rename 'index' to 'date' if that happened
        if 'index' in df.columns:
            df = df.rename(columns={'index': 'date'})
            
    # Lowercase all columns
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure 'date' is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        
    return df
