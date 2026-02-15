
from data_manager import fetch_ticker_data
from analytics import calculate_regime, calculate_volatility, generate_verdict
import pandas as pd

# Fetch data for a known ticker
ticker = "AAPL"
print(f"Fetching data for {ticker}...")
df = fetch_ticker_data(ticker, period='1 year')

if not df.empty:
    print(f"Data fetched: {len(df)} rows.")
    
    # Test Regime
    regime, desc = calculate_regime(df)
    print(f"\nREGIME: {regime}")
    print(f"Desc: {desc}")
    
    # Test Volatility
    vol_level, vol_val = calculate_volatility(df)
    print(f"\nVOLATILITY: {vol_level}")
    print(f"Value: {vol_val:.2f}%")
    
    # Test Verdict
    verdict, _, _ = generate_verdict(ticker, df)
    print(f"\nVERDICT:\n{verdict}")

else:
    print("Failed to fetch data.")
