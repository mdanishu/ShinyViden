
from openbb import obb
import pandas as pd
from datetime import datetime, timedelta
from .cache_manager import get_from_cache, set_to_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_EXPIRY_PRICE = 3600 * 1       # 1 hour
CACHE_EXPIRY_FUNDAM = 3600 * 24 * 7 # 1 week
CACHE_EXPIRY_MACRO = 3600 * 24 * 2  # 2 days

def get_price_history(ticker, interval="1d", provider="yfinance", start_date=None):
    """Fetches historical price data."""
    try:
        # Generate cache key including start_date to differentiatiate time windows
        cache_key = f"price_{ticker}_{interval}_{start_date}"
        cached = get_from_cache("get_price_history", ticker=ticker, interval=interval, start_date=start_date)
        if cached is not None:
            logger.info(f"Cache hit for {ticker} prices ({start_date})")
            return pd.read_json(cached, orient='split')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*20)).strftime("%Y-%m-%d")
            
        logger.info(f"Fetching {ticker} prices from {provider} (Start: {start_date})...")
        df = obb.equity.price.historical(
            symbol=ticker, start_date=start_date,
            interval=interval, provider=provider
        ).to_df()
        
        set_to_cache(df.to_json(orient='split', date_format='iso'),
                     "get_price_history", expire=CACHE_EXPIRY_PRICE, ticker=ticker, interval=interval, start_date=start_date)
        return df
    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {e}")
        return pd.DataFrame()

def get_key_metrics(ticker, provider="yfinance"):
    """Fetches key financial ratios/metrics."""
    try:
        cached = get_from_cache("get_key_metrics", ticker=ticker)
        if cached is not None:
            logger.info(f"Cache hit for {ticker} metrics")
            return pd.read_json(cached, orient='split')

        logger.info(f"Fetching {ticker} metrics from {provider}...")
        df = obb.equity.fundamental.metrics(symbol=ticker, provider=provider).to_df()
        
        if not df.empty:
            df = df.transpose().reset_index()
            df.columns = ["Metric", "Value"]
        
        set_to_cache(df.to_json(orient='split'), "get_key_metrics", expire=CACHE_EXPIRY_FUNDAM, ticker=ticker)
        return df
    except Exception as e:
        logger.error(f"Error fetching metrics for {ticker}: {e}")
        return pd.DataFrame()

# ── Macro Indicators ──────────────────────────────────────────────────

MACRO_INDICATORS = {
    "CPI": {
        "label": "US Consumer Price Index",
        "fetcher": lambda: obb.economy.cpi(country="united_states", provider="fred").to_df(),
        "color": "#3b82f6",   # Blue
    },
    "GDP": {
        "label": "US GDP Growth (Quarterly)",
        "fetcher": lambda: obb.economy.gdp.nominal(country="united_states", provider="oecd").to_df(),
        "color": "#8b5cf6",   # Purple
    },
    "Unemployment": {
        "label": "US Unemployment Rate",
        "fetcher": lambda: _fetch_fred_series("UNRATE"),
        "color": "#f97316",   # Orange
    },
    "Fed Funds Rate": {
        "label": "Effective Federal Funds Rate",
        "fetcher": lambda: _fetch_fred_series("FEDFUNDS"),
        "color": "#ef4444",   # Red
    },
    "10Y Treasury": {
        "label": "10-Year Treasury Yield",
        "fetcher": lambda: _fetch_fred_series("DGS10"),
        "color": "#eab308",   # Yellow
    },
}

def _fetch_fred_series(series_id: str) -> pd.DataFrame:
    """Helper to fetch a FRED series via OpenBB."""
    try:
        df = obb.economy.fred_series(symbol=series_id, provider="fred").to_df()
        return df
    except Exception as e:
        logger.warning(f"FRED series {series_id} failed: {e}")
        return pd.DataFrame()

def get_available_macro_indicators() -> list:
    """Returns list of available macro indicator keys."""
    return list(MACRO_INDICATORS.keys())

def get_macro_data(indicator_key: str, start_date: str = None) -> pd.DataFrame:
    """
    Fetches a macro indicator by key.
    Returns DataFrame with at least 'date' and 'value' columns.
    If start_date is provided, filters data >= start_date.
    """
    if indicator_key not in MACRO_INDICATORS:
        logger.error(f"Unknown indicator: {indicator_key}")
        return pd.DataFrame()
    
    try:
        # We cache the FULL history to avoid repeatedly fetching small slices from API
        # but we filter the RETURNED dataframe based on start_date
        
        # Version 2 cache key to force refresh after date fix
        cache_key = f"macro_v2_{indicator_key}"
        cached = get_from_cache("get_macro_data", indicator=indicator_key + "_v2")
        df = None
        
        if cached is not None:
            logger.info(f"Cache hit for macro {indicator_key}")
            df = pd.read_json(cached, orient='split')
        else:
            logger.info(f"Fetching macro: {indicator_key}...")
            fetcher = MACRO_INDICATORS[indicator_key]["fetcher"]
            df = fetcher()
            
            if not df.empty:
                # Normalize: ensure 'date' and 'value' columns
                df = _normalize_macro(df)
                
                # Cache the FULL dataset
                set_to_cache(df.to_json(orient='split', date_format='iso'),
                             "get_macro_data", expire=CACHE_EXPIRY_MACRO, indicator=indicator_key + "_v2")
        
        if df is None or df.empty:
            return pd.DataFrame()

        # LOGGING: Debug X-Axis Issue
        # logger.info(f"Macro Data ({indicator_key}) Columns: {df.columns.tolist()}")
        # logger.info(f"Macro Data ({indicator_key}) Dtypes:\n{df.dtypes}")
        # logger.info(f"Macro Data ({indicator_key}) Head:\n{df.head()}")

        # Apply Date Filtering if requested
        if start_date and 'date' in df.columns:
            # Ensure date is datetime for comparison
            # CRITICAL: Force conversion if it's object or int/float that looks like a date
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                 # Check for the specific nanosecond timestamp case seen in screenshot (1.74e18)
                 # If it's numeric, try unit='ns'
                 if pd.api.types.is_numeric_dtype(df['date']):
                     logger.info(f"Converting numeric date column for {indicator_key} (unit=ns likely)")
                     df['date'] = pd.to_datetime(df['date'], unit='ns', errors='coerce')
                 else:
                     df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            mask = df['date'] >= pd.to_datetime(start_date)
            df_filtered = df.loc[mask].copy()
            return df_filtered.sort_values('date')
            
        return df
        
    except Exception as e:
        err_str = str(e).lower()
        if "api_key" in err_str or "credential" in err_str:
            logger.warning(f"API Key missing for {indicator_key}. Returning empty DF.")
            return pd.DataFrame()
        logger.error(f"Error fetching macro {indicator_key}: {e}")
        return pd.DataFrame()

def _normalize_macro(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes macro DataFrames to have 'date' and 'value' columns."""
    if df.empty:
        return df
    
    # Flatten multi-index if present
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    
    # Reset index if date is likely in index (often True for OpenBB/Pandas)
    # Check if index name contains 'date' or is a DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        # The new column usually gets named 'index' or 'Date'
    elif df.index.name and ('date' in df.index.name.lower() or 'period' in df.index.name.lower()):
        df = df.reset_index()

    # Lowercase columns
    df.columns = [str(c).lower() for c in df.columns]
    
    # Search for date column
    date_col = None
    if 'date' in df.columns:
        date_col = 'date'
    else:
        # Fuzzy search
        for col in df.columns:
            if 'date' in col or 'period' in col or 'time' in col:
                df = df.rename(columns={col: 'date'})
                date_col = 'date'
                break
                
    # If we found a date column, force to datetime
    if date_col:
        # coerce errors to NaT, then drop NaT if any
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
    
    # Search for value column
    if 'value' not in df.columns:
        # Use the last numeric column as value
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        if numeric_cols:
            df = df.rename(columns={numeric_cols[-1]: 'value'})
    
    return df

# Keep backwards compat
def get_cpi_data(provider="fred"):
    """Legacy wrapper. Use get_macro_data('CPI') instead."""
    return get_macro_data("CPI")
