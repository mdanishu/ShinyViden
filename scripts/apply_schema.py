
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Use Session Pooler for DDL (Creating tables)
DB_HOST = "aws-0-us-east-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.ythxmkftubpwnlgxcdht"
DB_PASS = os.getenv("supa_password")
DB_PORT = "5432"

SCHEMA_FILE = "schema.sql"

def apply_schema():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        conn.autocommit = True
        
        with open(SCHEMA_FILE, 'r') as f:
            sql = f.read()
            
        print("Applying schema...")
        with conn.cursor() as cur:
            cur.execute(sql)
            
        print("Schema applied successfully!")
        conn.close()
    except Exception as e:
        print(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
