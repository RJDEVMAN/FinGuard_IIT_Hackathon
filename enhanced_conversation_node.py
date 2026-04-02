# Enhanced Conversation Node - Full FinGuard State Context
import hashlib
from typing import Dict, Any
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

_response_cache: Dict[str, str] = {}

def groq_generate_optimized(prompt: str, system: str = """You are a fraud analyst at FinGuard. Explain fraud findings clearly using specific data points.""") -> str:
    cache_key = hashlib.sha256(f"{system}||{prompt}".encode()).hexdigest()
    if cache_key in _response_cache:
        return _response_cache[cache_key]
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
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

def conversation_node_enhanced(state):
    user_input = state.get("user_input", "")
    context = state.get("context", {})
    
    # Extract all available context fields
    stock = context.get("stock", "UNKNOWN")
    decision = context.get("decision", "UNKNOWN")
    risk_score = context.get("risk_score")
    risk_level = context.get("risk_level", "UNKNOWN")
    fraud_score = context.get("fraud_score")
    fraud_reason = context.get("fraud_reason", "")
    
    clean_text = context.get("clean_text", "")
    input_type = context.get("input_type", "text")
    intent = context.get("intent", "hold")
    urgency = context.get("urgency", "low")
    
    fraud_signals = context.get("fraud_signals", {})
    web_insights = context.get("web_insights", {})
    graph_features = context.get("graph_features", {})
    
    context_text = ""
    
    if clean_text:
        context_text += f"EXTRACTED CONTENT ({input_type.upper()}):\n{clean_text[:400]}\n\n"
    
    if risk_score is not None:
        context_text += f"RISK SCORE: {risk_score * 100:.1f}% ({risk_level})\n"
        context_text += f"FRAUD PROBABILITY: {fraud_score * 100:.1f}%\n"
        context_text += f"DECISION: {decision}\n"
        if fraud_reason:
            context_text += f"REASON: {fraud_reason}\n"
        context_text += "\n"
    
    context_text += f"INTENT: {intent.upper()} | URGENCY: {urgency.upper()} | STOCK: {stock}\n\n"
    
    if fraud_signals:
        active_signals = [k for k, v in fraud_signals.items() if v]
        if active_signals:
            context_text += f"FRAUD SIGNALS: {', '.join(active_signals)}\n\n"
    
    web_data = web_insights.get("insights", "")
    if web_data:
        context_text += f"WEB INSIGHTS:\n{web_data[:300]}\n\n"
    
    if graph_features:
        context_text += f"PATTERN ANALYSIS: {graph_features}\n"
    
    why_keywords = ["why", "how", "explain", "what means", "reason"]
    is_explanation_q = any(kw in user_input.lower() for kw in why_keywords)
    
    system_prompt = """You are a fraud analyst at FinGuard. Explain findings clearly with specific data points and actionable insights."""
    
    if is_explanation_q:
        prompt = f"""Explain the fraud analysis in detail.

CONTEXT:
{context_text[:700]}

QUESTION: {user_input}

Directly explain: WHY was this fraud decision made? Reference specific signals and provide protective actions."""
    else:
        prompt = f"""Answer about the fraud analysis.

CONTEXT:
{context_text[:700]}

QUESTION: {user_input}

Answer directly using specific data from the analysis."""
    
    result = groq_generate_optimized(prompt, system=system_prompt)
    
    state["response"] = result or f"Decision: {decision} ({risk_score * 100:.1f}% risk). {fraud_reason}"
    
    return state
