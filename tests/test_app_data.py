
from data_manager import get_available_tickers, fetch_ticker_data

print("Fetching available tickers...")
tickers = get_available_tickers()
print(f"Found {len(tickers)} tickers.")
if len(tickers) > 0:
    print(f"First 5: {tickers[:5]}")
    
    first_ticker = tickers[0]
    print(f"Fetching data for {first_ticker} (All time)...")
    df = fetch_ticker_data(first_ticker, period='All time')
    
    if not df.empty:
        print(f"Successfully fetched {len(df)} rows.")
        print(f"Date Range: {df['Date'].min()} to {df['Date'].max()}")
        print(df.tail())
    else:
        print("Fetched empty dataframe.")
else:
    print("No tickers found.")
