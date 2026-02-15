
import os
from supabase import create_client, Client

url = "https://ythxmkftubpwnlgxcdht.supabase.co"
key = "sb_publishable_b5R5lL7pnEkXEovNSZk03Q_dvIpyUw6"

try:
    print(f"Connecting to {url}...")
    supabase: Client = create_client(url, key)
    # Try to select from a non-existent table just to check connection/auth
    # It should return a 404 or 401 or empty list, but not a connection error
    response = supabase.table("non_existent_table").select("*").limit(1).execute()
    print("API Connection Successful (Response received)")
    print(response)
except Exception as e:
    print(f"API Failed: {e}")
