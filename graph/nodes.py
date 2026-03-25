# Imports
from typing import TypedDict, Dict, Any
from langgraph.graph import START, StateGraph, END
import os
import fitz
import docx
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

# Initialising Gemini AI
gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client()

# LangGraph class
class FinGuardState(TypedDict, total=False):
    user_input: str
    clean_text: str 
    input_type: str  
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

# Node - 1: Extraction Engine
def extract_context(state: FinGuardState):

    user_input = state["user_input"]
    text = ""

    # FILE INPUT
    if os.path.exists(user_input):

        ext = os.path.splitext(user_input)[1].lower()

        # IMAGE
        if ext in [".png", ".jpg", ".jpeg"]:
            try:
                import pytesseract
                from PIL import Image

                text = pytesseract.image_to_string(Image.open(user_input))
                state["input_type"] = "image"

            except Exception:
                text = ""
                state["input_type"] = "image_error"

        # PDF
        elif ext == ".pdf":
            try:
                doc = fitz.open(user_input)
                text = ""
                for page in doc:
                    text += page.get_text()

                state["input_type"] = "document"

            except:
                text = ""
                state["input_type"] = "pdf_error"

        # DOCX
        elif ext == ".docx":
            try:
                doc = docx.Document(user_input)
                text = ""

                for para in doc.paragraphs:
                    text += para.text + "\n"

                state["input_type"] = "document"

            except:
                text = ""
                state["input_type"] = "docx_error"

        # AUDIO
        elif ext in [".mp3", ".wav"]:
            try:
                with open(user_input, "rb") as f:
                    audio_bytes = f.read()

                mime = "audio/mp3" if ext == ".mp3" else "audio/wav"

                audio_part = types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        """Transcribe this audio and extract only financial or market-related content.""",
                        audio_part
                    ]
                )

                text = response.text
                state["input_type"] = "audio"

            except:
                text = ""
                state["input_type"] = "audio_error"

        # UNKNOWN FILE
        else:
            text = ""
            state["input_type"] = "unsupported_file"

    # TEXT INPUT
    else:
        text = user_input
        state["input_type"] = "text"

    # CLEAN TEXT
    state["clean_text"] = text
    lower_text = text.lower()

    # STOCK DETECTION 
    list_of_stocks = ["TATAPOWER", "TATASTEEL", "TCS", "INFY", "RELIANCE"]

    found_stock = "UNKNOWN"
    for stock in list_of_stocks:
        if stock.lower() in lower_text:
            found_stock = stock
            break

    state["stock"] = found_stock

    # INTENT DETECTION
    if "sell" in lower_text:
        state["intent"] = "sell"
    elif "buy" in lower_text:
        state["intent"] = "buy"
    else:
        state["intent"] = "hold"

    # URGENCY DETECTION
    if any(word in lower_text for word in ["urgent", "immediately", "now"]):
        state["urgency"] = "high"
    else:
        state["urgency"] = "low"

    return state

# Node - 2: Fraud Detection Agent
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
    final_score = (0.4 * rule_score) + (0.6 * fraud_prob)

    # SAVE TO STATE
    state["fraud_signals"] = fraud_signals
    state["fraud_score"] = round(final_score, 2)
    state["fraud_reason"] = reason

    return state

# Node-3: TigerGraph Node
