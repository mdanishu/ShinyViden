
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_count():
    try:
        # Use exact=True to get exact count
        response = supabase.table('price_history').select('id', count='exact').limit(1).execute()
        count = response.count
        print(f"Total rows in price_history: {count}")
    except Exception as e:
        print(f"Failed to fetch count: {e}")

if __name__ == "__main__":
    check_count()
