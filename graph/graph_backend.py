# Imports
from typing import TypedDict, Dict, Any
from langgraph.graph import START, StateGraph, END
import os
import fitz
import docx
import hashlib
from groq import Groq                          
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# Initialising Groq & Tavily
GROQ_API_KEY = os.getenv("GROQ_API_KEY")      
TAVILY_API_KEY = os.getenv("TAVILY_WEB_SEARCH_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing in .env")

if not TAVILY_API_KEY:
    raise ValueError("❌ TAVILY_WEB_SEARCH_KEY missing in .env")

# Establishing clients
client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

_response_cache: Dict[str, str] = {}

# Initialize TigerGraph connection 
try:
    from tigergraph_client import test_connection, conn
    test_connection()
    TIGERGRAPH_AVAILABLE = True if conn else False
    if TIGERGRAPH_AVAILABLE:
        print("✓ TigerGraph connection established")
except Exception as e:
    print(f"⚠ TigerGraph not available (proceeding without graph analysis)")
    TIGERGRAPH_AVAILABLE = False
    conn = None
    conn = None

def groq_generate(prompt: str, system: str = """You are FinGuard, a fraud detection expert.
Analyze financial messages for fraud patterns and scams. Be concise and direct.""") -> str:
    cache_key = hashlib.sha256(f"{system}||{prompt}".encode()).hexdigest()
    if cache_key in _response_cache:
        return _response_cache[cache_key]
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            max_completion_tokens=512,  
            temperature=0.2,
        )
        result = (response.choices[0].message.content or "").strip()
        _response_cache[cache_key] = result  
        return result
    except Exception as e:
        print(f"[Groq LLM ERROR]: {e}")
        return ""

# Web insights cache 
_web_cache: Dict[str, str] = {}

# LangGraph State
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
    fraud_score: float
    fraud_reason: str

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

        # AUDIO
        elif ext in [".mp3", ".wav"]:
            try:
                with open(user_input, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(user_input), f.read()),
                        model="whisper-large-v3-turbo",
                        prompt="Financial message. Extract stock names, financial claims, urgency signals, manipulation cues.",
                        response_format="text",
                        language="en",
                        temperature=0.0
                    )
                text = (transcription if isinstance(transcription, str) else getattr(transcription, "text", "")) or ""
                state["input_type"] = "audio"
            except Exception as e:
                print(f"[Audio transcription error]: {e}")
                state["input_type"] = "audio_error"
                text = ""

    else:
        text = user_input if isinstance(user_input, str) else ""
        state["input_type"] = "text"

    state["clean_text"] = text
    lower = text.lower()

    # STOCK DETECTION
    stocks = ["TCS", "INFY", "RELIANCE", "TATASTEEL", "ADOBE"]
    state["stock"] = next((s for s in stocks if s.lower() in lower), "UNKNOWN")

    # INTENT
    state["intent"] = "buy" if "buy" in lower else "sell" if "sell" in lower else "hold"

    # URGENCY
    state["urgency"] = "high" if any(w in lower for w in ["urgent", "now", "immediately"]) else "low"

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

    if urgency == "high" or any(word in text for word in ["urgent", "immediately", "now"]):
        fraud_signals["urgency_pressure"] = True
    if any(word in text for word in ["crash", "loss", "drop", "panic"]):
        fraud_signals["fear_trigger"] = True
    if any(word in text for word in ["insider", "expert", "source", "confirmed"]):
        fraud_signals["authority_claim"] = True
    if intent in ["sell", "buy"] and urgency == "high":
        fraud_signals["manipulation"] = True
    if any(word in text for word in ["guaranteed", "100%", "sure profit"]):
        fraud_signals["greed"] = True

    rule_score = sum(fraud_signals.values()) / len(fraud_signals)

    prompt = f"""Analyze this message for fraud. Return exactly THREE sections.

SECTION 1 - FRAUD ANALYSIS:
Fraud Probability: <0-1>
Reason: <one line>

SECTION 2 - PATTERNS:
<comma-separated fraud keywords>

SECTION 3 - TRANSACTION:
Amount: <number or 10000>
Action: <buy|sell|withdraw|hold|unknown>

Message: {text}"""
    output = groq_generate(prompt)   

    # Defaults
    fraud_prob = 0.5
    reason = ""
    llm_patterns = []
    amount = 10000
    action = "unknown"

    # Split output into sections
    sec1, sec2, sec3 = "", "", ""
    if "SECTION 2" in output:
        parts = output.split("SECTION 2")
        sec1 = parts[0]
        remainder = parts[1]
        if "SECTION 3" in remainder:
            sec2_sec3 = remainder.split("SECTION 3")
            sec2 = sec2_sec3[0]
            sec3 = sec2_sec3[1]
        else:
            sec2 = remainder
    else:
        sec1 = output  # fallback

    # Parse Section 1
    for line in sec1.split("\n"):
        if "Fraud Probability" in line:
            try:
                fraud_prob = float(line.split(":")[-1].strip())
            except:
                pass
        elif "Reason" in line:
            reason += line.split(":", 1)[-1].strip()

    # Parse Section 2
    llm_patterns = [
        p.strip().lower()
        for p in sec2.replace("- FRAUD PATTERNS:", "").split(",")
        if p.strip()
    ]

    # Parse Section 3
    for line in sec3.split("\n"):
        if "Amount" in line:
            try:
                amount = float(line.split(":")[1].strip())
            except:
                pass
        if "Action" in line:
            action = line.split(":")[1].strip().lower()

    if action not in ["buy", "sell", "withdraw", "hold"]:
        action = "unknown"

    # FINAL FRAUD SCORE
    try:
        final_score = (0.4 * rule_score) + (0.6 * fraud_prob)
    except:
        final_score = 0.5

    state["fraud_signals"] = fraud_signals
    state["fraud_score"] = round(final_score, 2)
    state["fraud_reason"] = reason
    state["_llm_patterns"] = llm_patterns
    state["_txn_amount"] = amount
    state["_txn_action"] = action

    return state

# Node - 3: TigerGraph Node
def graph_intelligence_node(state: FinGuardState):

    text = state.get("clean_text") or ""
    stock = state.get("stock") or "UNKNOWN"
    fraud_signals = state.get("fraud_signals") or {}
    fraud_score = state.get("fraud_score", 0.5)

    import uuid
    message_id = str(uuid.uuid4())
    txn_id = str(uuid.uuid4())
    user_id = "user_1"

    rule_patterns = [k for k, v in fraud_signals.items() if v]

    llm_patterns = state.get("_llm_patterns") or []
    patterns = list(set(rule_patterns + llm_patterns))
    if not patterns:
        patterns = ["neutral"]

    amount = state.get("_txn_amount") or 10000
    action = state.get("_txn_action") or "unknown"
    if action not in ["buy", "sell", "withdraw", "hold"]:
        action = "unknown"

    # GRAPH INSERT (only if TigerGraph is available)
    if TIGERGRAPH_AVAILABLE and conn:
        try:
            conn.upsertVertex("User", user_id, {})
            conn.upsertVertex("Message", message_id, {"text": text})
            conn.upsertVertex("Stock", stock, {})

            conn.upsertEdge("User", user_id, "sent", "Message", message_id, {})
            conn.upsertEdge("Message", message_id, "mentions", "Stock", stock, {})

            for p in patterns:
                conn.upsertVertex("Pattern", p, {
                    "source": "rule" if p in rule_patterns else "llm"
                })
                conn.upsertEdge("Message", message_id, "has_pattern", "Pattern", p, {})
                conn.upsertEdge("Pattern", p, "affects", "Stock", stock, {})

            conn.upsertVertex("Transaction", txn_id, {
                "amount": float(amount),
                "action": action,
                "is_fraud": fraud_score > 0.5
            })
            conn.upsertEdge("Message", message_id, "triggers", "Transaction", txn_id, {})
            conn.upsertEdge("Transaction", txn_id, "involves", "Stock", stock, {})

        except Exception as e:
            print("Graph error:", e)

    # GRAPH QUERY (only if TigerGraph is available)
    if TIGERGRAPH_AVAILABLE and conn:
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
    else:
        # Use default values if TigerGraph is unavailable
        data = {
            "pattern_count": 1,
            "txn_count": 1,
            "fraud_txn_count": 1
        }

    state["graph_features"] = {
        "pattern_risk": min(data["pattern_count"] / 10, 1.0),
        "transaction_risk": min(data["fraud_txn_count"] / (data["txn_count"] + 1), 1.0),
        "network_risk": min((data["pattern_count"] + data["fraud_txn_count"]) / 20, 1.0)
    }

    return state

# Node - 4: Web Search Node
def web_search_node(state: FinGuardState):
    stock = state.get("stock") or "UNKNOWN"

    if stock in _web_cache:
        state["web_insights"] = {"insights": _web_cache[stock]}
        return state

    try:
        response = tavily_client.search(query=stock, search_depth="advanced")
        insight_text = response.get("answer", "") or ""
    except Exception as e:
        print(f"[Tavily error]: {e}")
        insight_text = ""

    # Store in graph if available
    if TIGERGRAPH_AVAILABLE and conn:
        for p in insight_text.split(","):
            p = p.strip()
            if p:
                try:
                    conn.upsertVertex("Pattern", p, {})
                    conn.upsertEdge("Pattern", p, "affects", "Stock", stock, {})
                except:
                    pass

    _web_cache[stock] = insight_text
    state["web_insights"] = {"insights": insight_text}

    return state

# Node - 5: Risk Scoring and Decision Agent
def risk_score_calculation(state: FinGuardState):

    fraud_score = state.get("fraud_score", 0.5)
    graph = state.get("graph_features", {})
    web = state.get("web_insights", {})
    stock = state.get("stock", "UNKNOWN")
    text = state.get("clean_text", "")

    graph_score = (
        0.25 * graph.get("pattern_risk", 0) +
        0.20 * graph.get("message_volume_risk", 0) +
        0.25 * graph.get("transaction_risk", 0) +
        0.30 * graph.get("network_risk", 0)
    )

    web_text = str(web.get("insights", "")).lower()
    web_risk = 0.3
    if any(word in web_text for word in ["fake", "manipulated", "not verified", "scam"]):
        web_risk = 0.8
    elif any(word in web_text for word in ["verified", "trusted", "authentic"]):
        web_risk = 0.2

    final_risk = (
        0.25 * fraud_score +
        0.20 * graph_score +
        0.15 * web_risk
    )
    final_risk = round(min(final_risk, 1.0), 2)

    # ROBUST THRESHOLDS: Handles extreme fraud cases
    # Enhanced to handle edge cases with very high fraud scores
    if final_risk < 0.25:
        risk_level = "LOW"
        decision = "SAFE"
    elif final_risk < 0.50:
        risk_level = "MEDIUM"
        decision = "WARNING"
    elif final_risk < 0.75:
        risk_level = "HIGH"
        decision = "FRAUD"
    else:
        # Extreme fraud case (75%+ risk)
        risk_level = "CRITICAL"
        decision = "CRITICAL_FRAUD"

    text_safe = text.replace("{", "(").replace("}", ")")
    # Enhanced prompt for extreme fraud cases
    severity_note = ""
    if final_risk > 0.75:
        severity_note = "\n EXTREME FRAUD CASE - Provide urgent guidance."
    
    prompt = f"""Final fraud decision for FinGuard.

User Message: {text_safe[:200]}
Stock: {stock}
Fraud Score: {fraud_score}
Graph Risk: {round(graph_score, 2)}
Web Risk: {web_risk}
Final Risk: {final_risk}{severity_note}

Output format ONLY:
Decision: <SAFE|WARNING|FRAUD|CRITICAL_FRAUD>
Explanation: <2-3 lines with preventive actions>"""
    output = groq_generate(prompt)   

    explanation = ""
    decision_llm = decision  # fallback

    if output:
        for line in output.split("\n"):
            if "Decision" in line:
                decision_llm = line.split(":")[-1].strip()
            elif "Explanation" in line:
                explanation += line.split(":", 1)[-1].strip()
    else:
        print(f"[Node 5 LLM ERROR]: Empty response from Groq")
        # Handle extreme fraud cases gracefully
        if final_risk > 0.75:
            explanation = f"CRITICAL FRAUD ALERT: This transaction exhibits extreme fraud indicators across all risk factors. Take immediate protective action."
        else:
            explanation = f"Fraud detection analysis complete. Decision: {decision}"
        decision_llm = decision

    state["risk_score"] = final_risk
    state["risk_level"] = risk_level
    state["decision"] = decision_llm
    state["message"] = explanation

    return state

# CONVERSATION MODE 
class ConversationState(TypedDict, total=False):
    user_input: str
    context: Dict[str, Any]  # From previous analysis
    response: str

# Node - Conversation: Answer user questions without generating risk scores
def conversation_node(state: ConversationState):
    """
    Answer user questions about previously analyzed data.
    Uses comprehensive context from previous analysis including extracted content,
    fraud signals, web insights, graph features, and market data.
    Also provides insights about risk scores and explains fraud detection rationale.
    """
    user_input = state.get("user_input", "")
    context = state.get("context", {})
    
    # Extract ALL FinGuard State fields for comprehensive conversation context
    web_insights = context.get("web_insights", {})
    graph_features = context.get("graph_features", {})
    market_data = context.get("market_data", {})
    file_info = context.get("file_info", {})
    risk_score = context.get("risk_score")
    fraud_score = context.get("fraud_score")
    decision = context.get("decision")
    risk_level = context.get("risk_level")
    
    # Extract additional FinGuard State fields for enriched context
    stock = context.get("stock", "UNKNOWN")
    clean_text = context.get("clean_text", "")  # Extracted content from audio/documents
    input_type = context.get("input_type", "text")  # Type of input: audio, pdf, image, text
    fraud_signals = context.get("fraud_signals", {})  # Specific fraud signals detected
    fraud_reason = context.get("fraud_reason", "")  # Explanation of fraud detection
    intent = context.get("intent", "hold")  # User's apparent intent: buy/sell/hold
    urgency = context.get("urgency", "low")  # Urgency level: low/medium/high
    
    # Build comprehensive context-aware prompt
    context_text = ""
    
    # 1. Stock Information
    if stock and stock != "UNKNOWN":
        context_text += f"STOCK BEING DISCUSSED: {stock}\n\n"
    
    # 2. Extracted Content from Media (Audio/PDF/Image)
    if clean_text and input_type != "text":
        context_text += f"EXTRACTED CONTENT FROM {input_type.upper()}:\n"
        context_text += f"{clean_text[:1000]}...\n\n" if len(clean_text) > 1000 else f"{clean_text}\n\n"
    
    # 3. Fraud Signals & Detection Rationale
    if fraud_signals:
        context_text += f"FRAUD SIGNALS DETECTED:\n"
        signal_descriptions = {
            "urgency_pressure": "Artificial urgency/time pressure tactics",
            "fear_trigger": "Fear-based manipulation or panic inducement",
            "authority_claim": "False authority claims or impersonation",
            "manipulation": "Emotional manipulation or psychological pressure",
            "greed": "Exploitation of greed or excessive profit promises"
        }
        for signal, detected in fraud_signals.items():
            if detected:
                description = signal_descriptions.get(signal, signal.replace('_', ' ').title())
                context_text += f"- {description}\n"
        context_text += "\n"
    
    if fraud_reason:
        context_text += f"FRAUD DETECTION REASONING:\n{fraud_reason}\n\n"
    
    # 4. Risk Score & Decision Analysis
    if risk_score is not None:
        context_text += f"ANALYSIS RESULTS:\n"
        context_text += f"- Final Risk Score: {risk_score} ({risk_level})\n"
        context_text += f"- Fraud Probability: {fraud_score}\n"
        context_text += f"- Decision: {decision}\n"
        if intent and intent != "hold":
            context_text += f"- Apparent Intent: {intent.upper()}\n"
        if urgency and urgency != "low":
            context_text += f"- Urgency Level: {urgency.upper()}\n"
        context_text += "\n"
    
    # 5. Web & Market Insights
    if web_insights:
        context_text += f"WEB MARKET INSIGHTS:\n{web_insights.get('insights', 'N/A')}\n\n"
    if market_data:
        context_text += f"MARKET DATA:\n{str(market_data)}\n\n"
    
    # 6. Graph Analysis Findings
    if graph_features:
        context_text += f"GRAPH ANALYSIS FINDINGS:\n"
        for key, value in graph_features.items():
            context_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        context_text += "\n"
    
    # 7. File Information
    if file_info:
        context_text += f"PREVIOUS FILE ANALYZED: {file_info.get('name', 'N/A')} ({input_type.upper()})\n"
    
    system_prompt = """You are a fraud analyst at FinGuard. Explain fraud detection findings clearly using specific data points."""
    
    # Detect question type to tailor response
    question_lower = user_input.lower()
    is_explanation_question = any(
        word in question_lower 
        for word in ["why", "how", "explain", "reason", "what", "how much", "detect", "fraud", "score", "risk"]
    )
    
    if is_explanation_question:
        prompt = f"""Explain the fraud analysis based on context:

CONTEXT:
{context_text[:800] if context_text else "No analysis data."}

QUESTION: {user_input}

Directly explain: WHY was this detected as fraud? Reference specific patterns and provide preventive actions."""
    else:
        prompt = f"""Answer the question about fraud analysis:

CONTEXT:
{context_text[:800] if context_text else "No analysis data."}

QUESTION: {user_input}

Provide relevant details with specific data points and actionable recommendations."""
    
    response = groq_generate(prompt, system=system_prompt)
    
    state["response"] = response or "I apologize, but I couldn't generate a response. Please try rephrasing your question."
    
    return state

# Compile Main Analysis Graph
builder = StateGraph(FinGuardState)

builder.add_node("extract", extract_context)
builder.add_node("fraud", fraud_detection_node)
builder.add_node("graph", graph_intelligence_node)
builder.add_node("web", web_search_node)
builder.add_node("risk", risk_score_calculation)

builder.add_edge(START, "extract")
builder.add_edge("extract", "fraud")
builder.add_edge("fraud", "graph")
builder.add_edge("graph", "web")
builder.add_edge("web", "risk")
builder.add_edge("risk", END)

app = builder.compile()
print("Main Analysis Graph compiled successfully!")

# Compile Conversation Graph
builder_converse = StateGraph(ConversationState)
builder_converse.add_node("converse", conversation_node)
builder_converse.add_edge(START, "converse")
builder_converse.add_edge("converse", END)

app_converse = builder_converse.compile()
print("Conversation Graph compiled successfully!")