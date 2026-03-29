from fastapi import FastAPI
from pydantic import BaseModel
from graph_backend import app as graph_app
from tigergraph_client import test_connection
test_connection()  # Ensure TigerGraph connection is established before starting the API
app = FastAPI()

class InputData(BaseModel):
    user_input: str

@app.post("/analyze")
def analyze(data: InputData):
    try:
        result = graph_app.invoke({"user_input": data.user_input})

        return {
            "decision": result.get("decision"),
            "risk_score": result.get("risk_score"),
            "message": result.get("message")
        }

    except Exception as e:
        return {"error": str(e)}