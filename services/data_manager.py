
import os
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Load credentials from environment variables
# In production, these should be set in the deployment environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None

def get_supabase_client() -> Client:
    """Singleton to get the Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            # Fallback for local testing if env vars are missing, or raise error
            # For now, let's assume they are present or will be provided
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Supabase client: {e}")
    return _supabase_client

def get_available_tickers():
    """Fetches distinct tickers from the database."""
    try:
        supabase = get_supabase_client()
        # Fetching list of tickers from 'market_summary' table is most efficient
        response = supabase.table('market_summary').select('ticker').execute()
        if response.data:
            tickers = [item['ticker'] for item in response.data]
            return sorted(list(set(tickers)))
        return []
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return []

def fetch_ticker_data(ticker: str, period: str = 'All time') -> pd.DataFrame:
    """
    Fetches historical data for a specific ticker from 'price_history'.
    """
    supabase = get_supabase_client()
    
    # First, get the latest date for this ticker to anchor our period
    # This ensures "1 year" means "Last available year of data", handling stale data gracefully
    latest_query = supabase.table('price_history').select('date').eq('ticker', ticker).order('date', desc=True).limit(1).execute()
    
    if not latest_query.data:
        return pd.DataFrame()
        
    latest_date_str = latest_query.data[0]['date']
    latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')

    query = supabase.table('price_history').select("*").eq('ticker', ticker)
    
    # Calculate cutoff date based on period relative to LATEST DATA
    if period != 'All time':
        end_date = latest_date
        start_date = None
        if period == '3 months':
            start_date = end_date - timedelta(days=90)
        elif period == '6 months':
            start_date = end_date - timedelta(days=180)
        elif period == '1 year':
            start_date = end_date - timedelta(days=365)
        elif period == '5 years':
            start_date = end_date - timedelta(days=365 * 5)
        
        if start_date:
            # print(f"DEBUG: Querying {ticker} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            query = query.gte('date', start_date.strftime('%Y-%m-%d'))
    
    # Order by date DESC to get the LATEST data first (due to API row limits)
    query = query.order('date', desc=True).limit(2000)
    
    response = query.execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        # Rename columns to match existing app logic if needed
        # DB: date, price, ma_50, ma_200
        # App: Date, Price, 50d MA, 200d MA
        rename_map = {
            'date': 'Date',
            'price': 'Price',
            'ma_50': '50d MA',
            'ma_200': '200d MA'
        }
        # Only rename columns that exist
        df = df.rename(columns=rename_map)
        
        # Ensure date is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
        # IMPORTANT: Sort by Date ASC for plotting
        df = df.sort_values(by='Date', ascending=True)
            
        return df
    
    return pd.DataFrame()

def save_ticker_history(ticker: str, df: pd.DataFrame):
    """
    Saves/Upserts OHLCV data to Supabase 'price_history' table.
    Expects df with columns: date, open, high, low, close, volume (normalized names).
    """
    if df.empty: return

    supabase = get_supabase_client()
    
    # Prepare list of dicts for upsert
    records = []
    for _, row in df.iterrows():
        # Ensure date is string YYYY-MM-DD
        date_str = row['date'].strftime('%Y-%m-%d') if pd.api.types.is_datetime64_any_dtype(df['date']) else str(row['date'])[:10]
        
        # safely get values
        record = {
            "ticker": ticker.upper(),
            "date": date_str,
            "price": row.get('close', row.get('price', 0)), # map close/price to 'price' column in DB
            "open": row.get('open', 0),
            "high": row.get('high', 0),
            "low": row.get('low', 0),
            "volume": row.get('volume', 0),
            # Calculate MAs on the fly if not present? 
            # Ideally we just store raw data. But schema might require ma_50/ma_200 if not nullable.
            # Let's assume they are nullable or we can calc them.
            # For efficiency, let's skip MAs for now or send 0/None.
            # "ma_50": None, 
            # "ma_200": None
        }
        records.append(record)
    
    if not records: return

    try:
        # Batch upsert (Supabase handles this well)
        # Using upsert on (ticker, date) primary key constraint
        # Chunking just in case of limits
        chunk_size = 1000
        for i in range(0, len(records), chunk_size):
            batch = records[i:i+chunk_size]
            supabase.table('price_history').upsert(batch).execute()
            
        print(f"Successfully saved {len(records)} rows for {ticker} to Supabase.")
    except Exception as e:
        print(f"Error saving to Supabase for {ticker}: {e}")
