
import os
import pandas as pd
from supabase import create_client, Client
import time
from dotenv import load_dotenv

load_dotenv()

# Use Service Key for bypassing RLS during seed
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

CSV_FILE = "Stock_History.csv"

def check_table_exists(table_name="price_history"):
    try:
        # Try to select 1 row. If table doesn't exist, API throws error.
        supabase.table(table_name).select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Check failed for {table_name}: {e}")
        return False

def seed_data_api():
    print(f"Reading {CSV_FILE}...")
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"Error: {CSV_FILE} not found.")
        return

    # Standardize column names
    df.rename(columns={
        'Date': 'date',
        'Price': 'price',
        '50d MA': 'ma_50',
        '200d MA': 'ma_200',
        'Ticker': 'ticker'
    }, inplace=True)
    
    # Convert date
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # Select columns
    data_to_insert = df[['ticker', 'date', 'price', 'ma_50', 'ma_200']].copy()
    
    # Deduplicate based on ticker and date, keeping the last entry
    data_to_insert.drop_duplicates(subset=['ticker', 'date'], keep='last', inplace=True)
    
    # Fill NaN with None (must cast to object first to hold None)
    data_to_insert = data_to_insert.astype(object).where(pd.notnull(data_to_insert), None)
    
    records = data_to_insert.to_dict(orient='records')
    total_records = len(records)
    print(f"Preparing to insert {total_records} rows into 'price_history'...")
    
    batch_size = 1000
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        try:
            # upsert=True is important to avoid duplicates if re-running
            # on_conflict needs constraint name or columns. API uses primary key or unique constraints.
            # We defined UNIQUE(ticker, date) in schema.
            response = supabase.table('price_history').upsert(batch, on_conflict='ticker,date').execute()
            print(f"Inserted batch {i} to {i+len(batch)}")
        except Exception as e:
            print(f"Error inserting batch {i}: {e}")
            # If table doesn't exist, this will fail.
            return

    print("Data seeding completed for price_history.")
    
    # Now populate market_summary with distinct tickers
    # We can't do complex INSERT INTO ... SELECT via API easily without RPC.
    # So we'll do it in python.
    
    print("Populating market_summary...")
    unique_tickers = df['ticker'].unique()
    summary_records = [{'ticker': t, 'last_updated': datetime.now().isoformat()} for t in unique_tickers]
    
    try:
        supabase.table('market_summary').upsert(summary_records, on_conflict='ticker').execute()
        print("Market summary initialized.")
    except Exception as e:
         print(f"Error populating market_summary: {e}")


if __name__ == "__main__":
    from datetime import datetime
    
    print("Checking if 'price_history' table exists...")
    if check_table_exists():
        print("Table exists. Starting seed...")
        seed_data_api()
    else:
        print("ERROR: Table 'price_history' does not exist.")
        print("Please run the SQL in 'schema.sql' in your Supabase SQL Editor first.")
