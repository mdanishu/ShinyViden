
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_latest():
    try:
        response = supabase.table('price_history').select('date').order('date', desc=True).limit(1).execute()
        if response.data:
            print(f"Latest date in DB: {response.data[0]['date']}")
        else:
            print("No data found.")
    except Exception as e:
        print(f"Failed to fetch latest date: {e}")

if __name__ == "__main__":
    check_latest()
