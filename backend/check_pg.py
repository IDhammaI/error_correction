import psycopg
from core.config import settings

def check_pg():
    try:
        # Try to connect to the local PG on 5432 first as per original .env
        conn_str = "postgresql://postgres:123456@localhost:5432/ctb"
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector';")
                result = cur.fetchone()
                if result:
                    print(f"FOUND: {result}")
                else:
                    print("NOT FOUND: vector extension not available in pg_available_extensions")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_pg()
