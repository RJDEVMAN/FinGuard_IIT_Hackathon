import pyTigerGraph as tg
from dotenv import load_dotenv
import os

load_dotenv()

# Create connection
conn = tg.TigerGraphConnection(
    host=os.getenv("TG_HOST"),
    graphname=os.getenv("TG_GRAPHNAME"),
    apiToken=os.getenv("TG_API_TOKEN"),
    username=os.getenv("TG_USERNAME"),
    password=os.getenv("TG_PASSWORD"),
    gsqlSecret=os.getenv("TG_SECRET_KEY")
)

# -------------------------------
# ✅ CONNECTION TEST FUNCTION
# -------------------------------
def test_connection():
    try:
        print("\n🔍 Testing TigerGraph Connection...")

        # 1️⃣ Test basic connectivity
        version = conn.getVersion()
        print("✅ Connected to TigerGraph!")
        print("🔹 Version:", version)

        # 2️⃣ Check graph exists
        graph_name = conn.graphname
        print("🔹 Graph:", graph_name)

        # 3️⃣ Fetch schema (VERY IMPORTANT)
        schema = conn.getSchema()
        print("✅ Schema Loaded!")

        # 4️⃣ List vertex types
        vertex_types = [v["Name"] for v in schema["VertexTypes"]]
        print("🔹 Vertex Types:", vertex_types)

        # 5️⃣ List edge types
        edge_types = [e["Name"] for e in schema["EdgeTypes"]]
        print("🔹 Edge Types:", edge_types)

        print("\nTigerGraph is FULLY CONNECTED AND READY!\n")

        return True

    except Exception as e:
        print("\nTigerGraph Connection FAILED!")
        print("Error:", str(e))
        print("\nCheck:")
        print("- TG_HOST is correct")
        print("- Instance is RUNNING")
        print("- API Token is valid")
        print("- Graph name is correct\n")

        return False
test_connection()

# -------------------------------
# AUTO TEST ON IMPORT (OPTIONAL)
# -------------------------------
#if __name__ == "__main__":
#    test_connection()
