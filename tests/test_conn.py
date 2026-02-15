
import psycopg2

DB_HOST = "aws-0-us-east-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.ythxmkftubpwnlgxcdht"
DB_PASS = "7CyGvtTLL2jXE5eA"
DB_PORT = "5432"

try:
    print("Connecting...")
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    print("Connected successfully!")
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
