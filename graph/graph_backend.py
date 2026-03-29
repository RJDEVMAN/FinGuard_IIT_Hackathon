# Imports
from typing import TypedDict, Dict, Any
from langgraph.graph import START, StateGraph, END
import os
import fitz
import docx
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tavily import TavilyClient
load_dotenv()

# Initialising Gemini AI
gemini_key = os.getenv("GEMINI_API_KEY")
tavily_key = TavilyClient(os.getenv("TAVILY_WEB_SEARCH_KEY"))
client = genai.Client()

# LangGraph class
class FinGuardState(TypedDict, total=False):
    user_input: str
    clean_text: str 
    input_type: str  
    web_insights: Dict[str, Any]
    stock: str
    urgency: str
    intent: str
    fraud_signals: Dict[str, Any]
    graph_features: Dict[str, Any]
    market_data: Dict[str, Any]
    risk_score: float
    risk_level: str
    estimated_loss: float
    decision: str
    message: str

# Node - 1: Context Extraction Node
def extract_context(state: FinGuardState):

    user_input = state["user_input"]
    text = ""

    if os.path.exists(user_input):

        ext = os.path.splitext(user_input)[1].lower()

        # IMAGE OCR
        if ext in [".png", ".jpg", ".jpeg"]:
            try:
                import pytesseract
                from PIL import Image

                text = pytesseract.image_to_string(Image.open(user_input))
                state["input_type"] = "image"

            except:
                state["input_type"] = "image_error"
                text = ""

        # PDF
        elif ext == ".pdf":
            try:
                doc = fitz.open(user_input)
                text = "".join([page.get_text() for page in doc])
                state["input_type"] = "document"
            except:
                state["input_type"] = "pdf_error"

        # DOCX
        elif ext == ".docx":
            try:
                doc = docx.Document(user_input)
                text = "\n".join([p.text for p in doc.paragraphs])
                state["input_type"] = "document"
            except:
                state["input_type"] = "docx_error"

        # AUDIO (FIXED WITH PROMPT)
        elif ext in [".mp3", ".wav"]:
            try:
                with open(user_input, "rb") as f:
                    audio_bytes = f.read()

                audio_part = types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/mp3"
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        """Transcribe this audio and extract ONLY:
- stock names
- financial claims
- urgency signals
- manipulation cues

Return clean text only.""",
                        audio_part
                    ]
                )

                text = response.text
                state["input_type"] = "audio"

            except:
                state["input_type"] = "audio_error"

    else:
        text = user_input
        state["input_type"] = "text"

    state["clean_text"] = text
    lower = text.lower()

    # STOCK DETECTION
    stocks = ["TCS", "INFY", "RELIANCE", "TATASTEEL", "ADOBE"]
    state["stock"] = next((s for s in stocks if s.lower() in lower), "UNKNOWN")

    # INTENT
    state["intent"] = "buy" if "buy" in lower else "sell" if "sell" in lower else "hold"

    # URGENCY
    state["urgency"] = "high" if any(w in lower for w in ["urgent","now","immediately"]) else "low"

    return state

# Node - 2: Fraud Detection Node
def fraud_detection_node(state: FinGuardState):

    text = state.get("clean_text", "").lower()
    intent = state.get("intent", "")
    urgency = state.get("urgency", "")

    # RULE-BASED SIGNALS
    fraud_signals = {
        "urgency_pressure": False,
        "fear_trigger": False,
        "authority_claim": False,
        "manipulation": False,
        "greed": False
    }

    # Urgency pressure
    if urgency == "high" or any(word in text for word in ["urgent", "immediately", "now"]):
        fraud_signals["urgency_pressure"] = True

    # Fear trigger
    if any(word in text for word in ["crash", "loss", "drop", "panic"]):
        fraud_signals["fear_trigger"] = True

    # Authority fraud
    if any(word in text for word in ["insider", "expert", "source", "confirmed"]):
        fraud_signals["authority_claim"] = True

    # Manipulation (strong trading push)
    if intent in ["sell", "buy"] and urgency == "high":
        fraud_signals["manipulation"] = True

    # Greed trigger
    if any(word in text for word in ["guaranteed", "100%", "sure profit"]):
        fraud_signals["greed"] = True

    # RULE SCORE
    rule_score = sum(fraud_signals.values()) / len(fraud_signals)

    # LLM ANALYSIS 
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are the financial fraud detection agent of FinGuard. 
Your main task revolves around psychological analysis of the extracted content.
Analyze this message and determine:
- Is it manipulative or misleading?
- What tactics are used?
- Give a fraud probability between 0 and 1.

Message:
{text}

Return STRICT format:
Fraud Probability: <number>
Reason: <two lines explanation>
"""
        )

        output = response.text

        fraud_prob = 0.5
        reason = ""

        for line in output.split("\n"):
            if "Fraud Probability" in line:
                try:
                    fraud_prob = float(line.split(":")[-1].strip())
                except:
                    pass
            elif "Reason" in line:
                reason += line.split(":", 1)[-1].strip()

    except Exception:
        fraud_prob = 0.5
        reason = "LLM failed"

    # FINAL SCORE 
    try:
        final_score = (0.4 * rule_score) + (0.6 * fraud_prob)
    except:
        final_score = 0.5

    # SAVE TO STATE
    state["fraud_signals"] = fraud_signals
    state["fraud_score"] = round(final_score, 2)
    # Fallback
    if "fraud_score" not in state:
        state["fraud_score"] = 0.5
    state["fraud_reason"] = reason

    return state

# Node-3: TigerGraph Node
from tigergraph_client import conn

def graph_intelligence_node(state: FinGuardState):

    text = state["clean_text"]
    stock = state["stock"]
    fraud_signals = state["fraud_signals"]
    fraud_score = state.get("fraud_score", 0.5)

    import uuid
    message_id = str(uuid.uuid4())
    txn_id = str(uuid.uuid4())
    user_id = "user_1"

    # RULE BASED PATTERNS
    rule_patterns = [k for k, v in fraud_signals.items() if v]

    # LLM EXTRACTION
    try:
        llm_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Extract additional fraud patterns from message.
Message:
{text}
Return comma-separated patterns:
"""
        )

        llm_patterns = [
            p.strip().lower()
            for p in llm_response.text.split(",")
            if p.strip()
        ]

    except:
        llm_patterns = []

    # MERGING
    patterns = list(set(rule_patterns + llm_patterns))

    if not patterns:
        patterns = ["neutral"]

    # TRANSACTION EXTRACTION
    txn_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Extract transaction signals:

- amount
- action (buy/sell/withdraw/hold)

Message:
{text}

Return:
Amount: <number>
Action: <type>
"""
    )

    amount = 10000
    action = "unknown"

    for line in txn_response.text.split("\n"):
        if "Amount" in line:
            try:
                amount = float(line.split(":")[1].strip())
            except:
                pass
        if "Action" in line:
            action = line.split(":")[1].strip().lower()

    if action not in ["buy", "sell", "withdraw", "hold"]:
        action = "unknown"

    # GRAPH INSERT
    try:
        conn.upsertVertex("User", user_id, {})
        conn.upsertVertex("Message", message_id, {"text": text})
        conn.upsertVertex("Stock", stock, {})

        conn.upsertEdge("User", user_id, "sent", "Message", message_id, {})
        conn.upsertEdge("Message", message_id, "mentions", "Stock", stock, {})

        # PATTERN STORAGE 
        for p in patterns:
            conn.upsertVertex("Pattern", p, {
                "source": "rule" if p in rule_patterns else "llm"
            })

            conn.upsertEdge(
                "Message", message_id,
                "has_pattern",
                "Pattern", p,
                {}
            )

            conn.upsertEdge(
                "Pattern", p,
                "affects",
                "Stock", stock,
                {}
            )

        # TRANSACTION STORAGE
        conn.upsertVertex("Transaction", txn_id, {
            "amount": float(amount),
            "action": action,
            "is_fraud": fraud_score > 0.6
        })

        conn.upsertEdge(
            "Message", message_id,
            "triggers",
            "Transaction", txn_id,
            {}
        )

        conn.upsertEdge(
            "Transaction", txn_id,
            "involves",
            "Stock", stock,
            {}
        )

    except Exception as e:
        print("Graph error:", e)

    # GRAPH QUERY
    try:
        data = conn.runInstalledQuery(
            "unifiedRiskAnalysis",
            {"stock_name": stock}
        )[0]
    except:
        data = {
            "pattern_count": 1,
            "txn_count": 1,
            "fraud_txn_count": 1
        }

    # FEATURES
    state["graph_features"] = {
        "pattern_risk": min(data["pattern_count"] / 10, 1.0),
        "transaction_risk": min(data["fraud_txn_count"] / (data["txn_count"] + 1), 1.0),
        "network_risk": min((data["pattern_count"] + data["fraud_txn_count"]) / 20, 1.0)
    }

    return state
# Node - 4: Web Search Node
def web_search(state: FinGuardState):

    stock = state["stock"]

    response = tavily_key.search(query=stock, search_depth="advanced")

    insight = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Check if this news indicates fraud patterns.
Extract patterns ONLY.
News:
{response}

Return list:
"""
    )

    patterns = insight.text.split(",")

    # FEEDBACK INTO GRAPH
    for p in patterns:
        p = p.strip()
        conn.upsertVertex("Pattern", p, {})
        conn.upsertEdge("Pattern", p, "affects", "Stock", stock, {})

    state["web_insights"] = {"insights": insight.text}

    return state

# Node - 5:- Risk Scoring and Decision Agent
def risk_score_calculation(state: FinGuardState):

    # EXTRACT INPUTS
    fraud_score = state.get("fraud_score", 0.5)
    graph = state.get("graph_features", {})
    web = state.get("web_insights", {})

    stock = state.get("stock", "UNKNOWN")
    text = state.get("clean_text", "")

    # GRAPH SCORE AGGREGATION
    graph_score = (
        0.25 * graph.get("pattern_risk", 0) +
        0.20 * graph.get("message_volume_risk", 0) +
        0.25 * graph.get("transaction_risk", 0) +
        0.30 * graph.get("network_risk", 0)
    )

    # WEB RISK EXTRACTION 
    web_text = str(web.get("insights", "")).lower()

    web_risk = 0.3  # default

    if any(word in web_text for word in ["fake", "manipulated", "not verified", "scam"]):
        web_risk = 0.8
    elif any(word in web_text for word in ["verified", "trusted", "authentic"]):
        web_risk = 0.2

    # FINAL RISK SCORE
    final_risk = (
        0.4 * fraud_score +
        0.4 * graph_score +
        0.2 * web_risk
    )

    final_risk = round(min(final_risk, 1.0), 2)

    # RISK LEVEL CLASSIFICATION
    if final_risk < 0.3:
        risk_level = "LOW"
        decision = "SAFE"
    elif final_risk < 0.7:
        risk_level = "MEDIUM"
        decision = "WARNING"
    else:
        risk_level = "HIGH"
        decision = "FRAUD"

    # LLM FINAL EXPLANATION
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are the final decision agent of FinGuard.

You are given:
- User Message: {text}
- Stock: {stock}
- Fraud Score: {fraud_score}
- Graph Risk Score: {round(graph_score, 2)}
- Web Risk Score: {web_risk}

Based on these, generate:
1. Final Decision (SAFE / WARNING / FRAUD)
2. A short explanation (3-4 lines, simple for users)

Be clear and direct.

Output format:
Decision: <decision>
Explanation: <text>
"""
        )

        output = response.text

        explanation = ""
        decision_llm = decision  # fallback

        for line in output.split("\n"):
            if "Decision" in line:
                decision_llm = line.split(":")[-1].strip()
            elif "Explanation" in line:
                explanation += line.split(":", 1)[-1].strip()

    except Exception:
        explanation = "Unable to generate explanation."
        decision_llm = decision

    # FINAL OUTPUT
    state["risk_score"] = final_risk
    state["risk_level"] = risk_level
    state["decision"] = decision_llm
    state["message"] = explanation

    return state

# Compiling the graph
builder = StateGraph(FinGuardState)

builder.add_node("extract", extract_context)
builder.add_node("fraud", fraud_detection_node)
builder.add_node("graph", graph_intelligence_node)
builder.add_node("web", web_search)
builder.add_node("risk", risk_score_calculation)

builder.add_edge(START, "extract")
builder.add_edge("extract", "fraud")
builder.add_edge("fraud", "graph")
builder.add_edge("graph", "web")
builder.add_edge("web", "risk")
builder.add_edge("risk", END)

app = builder.compile()
print("Graph compiled successfully!")