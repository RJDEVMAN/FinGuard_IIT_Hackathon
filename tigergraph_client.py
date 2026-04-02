import pyTigerGraph as tg
import os

# Initialize conn as None at module level (so it can be imported)
conn = None

def test_connection():
    global conn
    try:
        conn = tg.TigerGraphConnection(
            host=os.getenv("TG_HOST"),
            graphname=os.getenv("TG_GRAPH_NAME"),
            gsqlSecret=os.getenv("TG_SECRET_KEY"),
            tgCloud=True
        )
        conn.getToken(os.getenv("TG_SECRET_KEY"))
        print("✓ TigerGraph connection successful!")
        return True
    except Exception as e:
        print(f"⚠ TigerGraph connection failed: {str(e)[:80]}")
        conn = None
        return False
