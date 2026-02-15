
from openbb_manager import get_price_history, get_key_metrics, get_cpi_data
import time

def test_manager():
    ticker = "AAPL"
    
    print("\n--- Testing Price History ---")
    start = time.time()
    df = get_price_history(ticker, interval="1d")
    print(f"Fetched {len(df)} rows in {time.time() - start:.2f}s")
    if not df.empty:
        print(df.tail(3))
        
    print("\n--- Testing Cache (Price) ---")
    start = time.time()
    df_cached = get_price_history(ticker, interval="1d")
    print(f"Fetched {len(df_cached)} rows in {time.time() - start:.2f}s (Should be faster)")

    # Fundamentals and Macro might fail if providers (yfinance/fred) change API structure output
    # but let's try
    try:
        print("\n--- Testing Metrics ---")
        df_metrics = get_key_metrics(ticker)
        print(f"Fetched Metrics: {df_metrics.shape}")
        if not df_metrics.empty:
            print(df_metrics.head())
    except Exception as e:
        print(f"Metrics failed: {e}")

    try:
        print("\n--- Testing CPI (Macro) ---")
        df_cpi = get_cpi_data()
        print(f"Fetched CPI: {df_cpi.shape}")
        if not df_cpi.empty:
            print(df_cpi.tail())
    except Exception as e:
        print(f"CPI failed: {e}")

if __name__ == "__main__":
    test_manager()
