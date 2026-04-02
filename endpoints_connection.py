from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from graph.graph_backend import app as graph_app, app_converse as graph_app_converse
from tigergraph_client import test_connection

test_connection()  # Ensure TigerGraph connection is established before starting the API
app = FastAPI()

class InputData(BaseModel):
    user_input: str
    mode: str = "analyze"  # "analyze" or "converse"
    context: Optional[Dict[str, Any]] = None  # Context from previous analysis

@app.post("/analyze")
def analyze(data: InputData):
    try:
        if data.mode == "analyze":
            # New fraud analysis
            result = graph_app.invoke({"user_input": data.user_input})
        else:
            # Conversation mode - answer questions about previous analysis
            payload = {
                "user_input": data.user_input,
                "context": data.context or {}
            }
            result = graph_app_converse.invoke(payload)

        # Explicit None-safe returns
        if data.mode == "analyze":
            return {
                "decision": result.get("decision") or "UNKNOWN",
                "risk_score": result.get("risk_score") or 0.0,
                "risk_level": result.get("risk_level") or "UNKNOWN",
                "message": result.get("message") or "No explanation available.",
                "fraud_score": result.get("fraud_score") or 0.0,
                "stock": result.get("stock") or "UNKNOWN",
                "web_insights": result.get("web_insights", {}),
                "graph_features": result.get("graph_features", {}),
                "market_data": result.get("market_data", {}),
            }
        else:
            # Conversation mode response
            return {
                "response": result.get("response", result.get("message")),
                "message": result.get("response", result.get("message")),
                "mode": "converse"
            }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }