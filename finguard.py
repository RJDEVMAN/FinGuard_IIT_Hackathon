import streamlit as st
import os
import tempfile
from datetime import datetime

# Page config MUST be first Streamlit call 
st.set_page_config(
    page_title="FinGuard — AI Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import styles 
from style import FINGUARD_CSS
st.markdown(FINGUARD_CSS, unsafe_allow_html=True)

# Import LangGraph directly 
from graph.graph_backend import app as graph_app, app_converse as graph_app_converse

# SESSION STATE
for key, default in [
    ("messages", []),
    ("total_analyzed", 0),
    ("fraud_detected", 0),
    ("pending_file", None),
    ("show_upload_menu", False),
    ("show_file_picker", False),
    ("upload_type", "doc"),
    ("analysis_context", {}),  # Stores data from last analysis for conversation
    ("last_file_info", None),  # Track last uploaded file for context
    ("text_input_value", ""),  # Track text input for Enter key support
    ("last_processed_input", None),  # Prevent infinite loop on reruns
]:
    if key not in st.session_state:
        st.session_state[key] = default

# HELPERS
def ts_now() -> str:
    return datetime.now().strftime("%H:%M")

def risk_color(score: float) -> str:
    if score < 0.3:   return "#4ade80"
    elif score < 0.6: return "#fbbf24"
    return "#f87171"

def file_icon(name: str) -> str:
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    return {"pdf":"📄","docx":"📝","doc":"📝",
            "mp3":"🎵","wav":"🎵",
            "png":"🖼️","jpg":"🖼️","jpeg":"🖼️"}.get(ext, "📎")

def save_temp(uploaded) -> str:
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded.getbuffer())
        return f.name

def is_follow_up_question(user_text: str) -> bool:
    """Detect if user input is a follow-up question about previous analysis rather than new analysis."""
    if not st.session_state.get("analysis_context"):
        return False
    
    follow_up_keywords = [
        "what", "how", "can you", "tell me", "explain", "why",
        "statistics", "data", "information", "more about", "details",
        "recent", "history", "trends", "analysis", "compared",
        "average", "range", "what should", "should i", "can i",
        "previous", "that", "this", "it", "them"
    ]
    
    text_lower = user_text.lower()
    
    # If they reference previous data/analysis with a question, it's a follow-up
    has_question = any(text_lower.startswith(kw) for kw in follow_up_keywords) or "?" in user_text
    has_context_ref = any(word in text_lower for word in ["statistics", "data", "information", "details", "analysis", "recent"])
    
    return has_question and has_context_ref

# LANGRAPH BACKEND 
@st.cache_resource
def initialize_graphs():
    """Cache the LangGraph instances to avoid reloading."""
    return graph_app, graph_app_converse

_app, _app_converse = initialize_graphs()

def call_backend(user_input: str, mode: str = "analyze", context: dict = None, include_insights: bool = False) -> dict:
    """Call LangGraph directly (no HTTP).
    
    Args:
        user_input: The user's input (text, file path, or question)
        mode: Either "analyze" (for new fraud analysis) or "converse" (for follow-up questions)
        context: Optional analysis context from previous interactions
        include_insights: If True, generate conversation insights about the analysis (for media+query)
    """
    try:
        if mode == "analyze":
            result = _app.invoke({"user_input": user_input})
            
            # Generate conversation insights if requested 
            insights = ""
            if include_insights:
                insights_context = {
                    # Core Decision & Risk Fields
                    "stock": result.get("stock", "UNKNOWN"),
                    "decision": result.get("decision", "UNKNOWN"),
                    "risk_score": result.get("risk_score", 0.0),
                    "risk_level": result.get("risk_level", "UNKNOWN"),
                    "fraud_score": result.get("fraud_score", 0.0),
                    "fraud_reason": result.get("fraud_reason", ""),
                    "message": result.get("message", ""),
                    
                    # Content & Analysis Fields
                    "clean_text": result.get("clean_text", ""),
                    "input_type": result.get("input_type", "text"),
                    "intent": result.get("intent", "hold"),
                    "urgency": result.get("urgency", "low"),
                    
                    # Detailed Analysis Fields
                    "fraud_signals": result.get("fraud_signals", {}),
                    "web_insights": result.get("web_insights", {}),
                    "graph_features": result.get("graph_features", {}),
                }
                insights_result = _app_converse.invoke({
                    "user_input": user_input,
                    "context": insights_context
                })
                insights = insights_result.get("response", "")
            
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
                "conversation_insights": insights,  # Add insights for display
                # Pass all FinGuard State fields for conversation context
                "clean_text": result.get("clean_text", ""),
                "input_type": result.get("input_type", "text"),
                "fraud_signals": result.get("fraud_signals", {}),
                "fraud_reason": result.get("fraud_reason", ""),
                "intent": result.get("intent", "hold"),
                "urgency": result.get("urgency", "low"),
            }
        else:  # converse mode
            result = _app_converse.invoke({
                "user_input": user_input,
                "context": context or {}
            })
            return {
                "response": result.get("response", ""),
                "message": result.get("response", ""),
                "mode": "converse"
            }
            
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }

# RENDER HELPERS
def render_result_card(result: dict) -> str:
    """Render result card with decision badge and explanation (fraud score hidden)."""
    raw_decision = result.get("decision", "UNKNOWN")
    decision   = raw_decision.upper().strip().split()[0] if raw_decision else "UNKNOWN"
    risk_level = result.get("risk_level", "")
    message    = result.get("message") or "No explanation available."

    badge = decision if decision in ("SAFE","WARNING","FRAUD") else "UNKNOWN"
    level_tag = (
        f'<span style="font-size:0.68rem;color:#7f92b0;margin-left:0.6rem;">{risk_level}</span>'
        if risk_level else ""
    )

    return f"""
<div class="result-card">
  <div style="margin-bottom:0.8rem;">
    <span class="decision-badge badge-{badge}">{badge}</span>{level_tag}
  </div>
  <div class="explanation">{message}</div>
</div>"""


def render_messages():
    """Render all messages in session state."""
    for msg in st.session_state.messages:
        role      = msg["role"]
        content   = msg.get("content", "")
        ts        = msg.get("ts", "")
        result    = msg.get("result")
        file_info = msg.get("file_info")
        is_conversation = msg.get("is_conversation", False)
        side      = "user" if role == "user" else "bot"

        if file_info:
            icon = file_icon(file_info["name"])
            
            # Build query display if present
            query_section = ""
            if content and "Query:" in content:
                query_text = content.split("Query: ")[-1].strip()
                query_section = f"""
    <div style="margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid #334155;">
      <div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.4rem;">📝 Your Query</div>
      <div style="font-size:0.82rem;color:#cbd5e1;line-height:1.5;">{query_text}</div>
    </div>"""
            
            html = f"""
<div class="msg-row {side}">
  <div>
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:0.8rem;max-width:500px;">
      <div class="file-chip">
        <span style="font-size:1.4rem;">{icon}</span>
        <div>
          <div style="color:#94a3b8;font-weight:500;font-size:0.82rem;">{file_info['name']}</div>
          <div style="font-size:0.68rem;color:#7f92b0;">{file_info.get('size','')}</div>
        </div>
      </div>{query_section}
    </div>
    <div class="msg-meta">{ts}</div>
  </div>
</div>"""

        elif is_conversation and role == "bot":
            # Render conversation response (research/insights)
            html = f"""
<div class="msg-row bot">
  <div style="max-width:600px;width:100%;">
    <div class="msg-bubble bot" style="padding:0.9rem 1rem;border-left:3px solid #00d9ff;">
      <div style="font-size:0.68rem;color:#4f5f72;margin-bottom:0.6rem;letter-spacing:0.08em;text-transform:uppercase;font-weight:600;">
        📊 Analysis Insights
      </div>
      <div style="font-size:0.82rem;line-height:1.6;color:#cbd5e1;">{content}</div>
    </div>
    <div class="msg-meta">{ts}</div>
  </div>
</div>"""

        elif result and role == "bot":
            card = render_result_card(result)
            html = f"""
<div class="msg-row bot">
  <div style="max-width:500px;width:100%;">
    <div class="msg-bubble bot" style="padding:0.7rem 0.85rem;max-width:100%;border:none;background:#1a2332;border-left:3px solid #38bdf8;">
      <div style="font-size:0.7rem;color:#4f5f72;margin-bottom:0.5rem;letter-spacing:0.06em;text-transform:uppercase;">
        🛡️ Analysis Result
      </div>
      {card}
    </div>
    <div class="msg-meta">{ts}</div>
  </div>
</div>"""

        elif role == "bot":
            html = f"""
<div class="msg-row bot">
  <div>
    <div class="msg-bubble bot">{content}</div>
    <div class="msg-meta">{ts}</div>
  </div>
</div>"""

        else:
            html = f"""
<div class="msg-row user">
  <div>
    <div class="msg-bubble user">{content}</div>
    <div class="msg-meta">{ts}</div>
  </div>
</div>"""

        st.markdown(html, unsafe_allow_html=True)

# PROCESS & RESPOND
def process_and_respond(user_input: str, display_text: str, file_info: dict = None, additional_query: str = ""):
    """Send input to backend and append response to chat.
    
    Args:
        user_input: The main input (file path or text query)
        display_text: What to show in chat (filename or query)
        file_info: File metadata if file was uploaded
        additional_query: Extra query text to include with file
    """
    ts = ts_now()
    
    # Clear textbox immediately before processing
    st.session_state.text_input_value = ""
    
    # Combine file path with additional query if provided
    if file_info and additional_query:
        combined_input = f"{user_input} | ADDITIONAL_QUERY: {additional_query}"
        display_combined = f"{file_info['name']}\n\nQuery: {additional_query}"
    else:
        combined_input = user_input
        display_combined = display_text

    # Determine if this is a follow-up question or new analysis
    is_follow_up = is_follow_up_question(combined_input) and not file_info
    mode = "converse" if is_follow_up else "analyze"
    
    # Generate conversation insights always when media is uploaded
    include_insights = bool(file_info)  # Always include insights for media

    # Add user message with media context
    user_msg = {"role": "user", "content": display_combined, "ts": ts}
    if file_info:
        user_msg["file_info"] = file_info  # Media contributes to conversation state
        user_msg["media_type"] = "document"  # Track media type
    st.session_state.messages.append(user_msg)

    # Call backend with appropriate mode and context
    with st.spinner("🔍  Analyzing financial data..."):
        # Always pass context so media contributes to conversation state
        backend_context = st.session_state.get("analysis_context", {})
        if file_info and backend_context:
            backend_context["media_source"] = file_info  # Track media in conversation state
        
        result = call_backend(
            combined_input,
            mode=mode,
            context=backend_context,
            include_insights=include_insights  # Pass flag for generating insights
        )

    bot_ts = ts_now()

    # Add bot response
    if "error" in result:
        st.session_state.messages.append({
            "role": "bot", "content": result["error"], "ts": bot_ts,
        })
    else:
        # Store context from analysis for follow-up questions (now includes ALL FinGuard State)
        if mode == "analyze":
            st.session_state.analysis_context = {
                # Core Decision & Risk Fields
                "stock": result.get("stock", "UNKNOWN"),
                "decision": result.get("decision", "UNKNOWN"),
                "risk_score": result.get("risk_score", 0.0),
                "risk_level": result.get("risk_level", "UNKNOWN"),
                "fraud_score": result.get("fraud_score", 0.0),
                "fraud_reason": result.get("fraud_reason", ""),
                
                # Content & Analysis Fields
                "clean_text": result.get("clean_text", ""),
                "input_type": result.get("input_type", "text"),
                "intent": result.get("intent", "hold"),
                "urgency": result.get("urgency", "low"),
                
                # Detailed Analysis Fields
                "fraud_signals": result.get("fraud_signals", {}),
                "web_insights": result.get("web_insights", {}),
                "graph_features": result.get("graph_features", {}),
                "market_data": result.get("market_data", {}),
                
                # Media & Context
                "file_info": file_info,  # Media stored in analysis context
                "media_source": file_info,  # Also track media source explicitly
            }
            st.session_state.last_file_info = file_info
            
            st.session_state.total_analyzed += 1
            dec = (result.get("decision") or "").upper().strip().split()[0]
            if dec == "FRAUD":
                st.session_state.fraud_detected += 1
            
            # Show Risk Score Card
            st.session_state.messages.append({
                "role": "bot", "content": "", "ts": bot_ts, "result": result,
            })
            
            # Show Conversation Insights if media was uploaded WITH a query
            if include_insights and result.get("conversation_insights"):
                st.session_state.messages.append({
                    "role": "bot",
                    "content": result.get("conversation_insights"),
                    "ts": ts_now(),
                    "is_conversation": True
                })
        else:
            # Conversation mode - show research/insights as text (for follow-up questions)
            st.session_state.messages.append({
                "role": "bot", 
                "content": result.get("message", result.get("response", "I don't have information to answer that question based on the previous analysis.")), 
                "ts": bot_ts,
                "is_conversation": True
            })

    # Clear pending file and text input after processing
    st.session_state.pending_file = None
    st.session_state.text_input_value = ""
    st.session_state.show_upload_menu = False
    st.session_state.show_file_picker = False
    # Reset the processed input hash to allow new inputs
    st.session_state.last_processed_input = None
    st.rerun()

# SIDEBAR
with st.sidebar:
    st.markdown("""
<div class="sb-logo">
  <div style="font-size:2rem;">🛡️</div>
  <h2>FinGuard</h2>
  <div style="font-size:0.65rem;color:#38bdf8;letter-spacing:0.12em;text-transform:uppercase;font-weight:600;font-style:italic;">
    We see Threats, we kill them!
  </div>
</div>
<div class="sb-section">Status</div>
<div class="sb-team-card">
  <div class="sb-team-name">Real-time Fraud Detection</div>
  <div class="sb-member"><span class="sb-dot"></span>AI-Powered Analysis</div>
  <div class="sb-member"><span class="sb-dot"></span>Graph Intelligence</div>
  <div class="sb-member"><span class="sb-dot"></span>Market Insights</div>
</div>
<div class="sb-section">About</div>
<div class="sb-desc">
  Advanced financial fraud detection system combining LangGraph, TigerGraph, and market research. Real-time analysis of financial interactions.
</div>
<div class="sb-section">Session Stats</div>
""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
<div class="sb-stat">
  <div class="sb-stat-val">{st.session_state.total_analyzed}</div>
  <div class="sb-stat-lbl">Analyzed</div>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="sb-stat">
  <div class="sb-stat-val" style="color:#f87171;">{st.session_state.fraud_detected}</div>
  <div class="sb-stat-lbl">Fraud Found</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Tech Stack</div>', unsafe_allow_html=True)
    for tech in ["🧠 LangGraph","🕸️ TigerGraph","⚡ Groq LLM","🔍 Tavily Search","💬 Conversational AI"]:
        st.markdown(f'<div class="sb-tech">{tech}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Controls</div>', unsafe_allow_html=True)
    st.markdown('<div class="clear-wrap">', unsafe_allow_html=True)
    if st.button("🗑️  Clear Chat", use_container_width=True):
        st.session_state.messages       = []
        st.session_state.total_analyzed = 0
        st.session_state.fraud_detected = 0
        st.session_state.pending_file   = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
<div style="margin-top:2rem;">
  <div class="fg-footer">Made with 💓 by killers_of_threats</div>
</div>""", unsafe_allow_html=True)

# MAIN CHAT AREA
st.markdown("""
<div class="fg-header">
  <span class="shield">🛡️</span>
  <h1>FinGuard</h1>
  <p>We see Threats, we kill them!</p>
</div>""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
<div class="empty-state">
  <h3>Start a fraud analysis</h3>
  <p>Describe a suspicious message, upload a file, or ask follow-up questions about previous analyses.</p>
</div>""", unsafe_allow_html=True)
else:
    render_messages()

# INPUT SECTION
st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)

# SIMPLIFIED INPUT SECTION 

col_plus, col_text, col_send = st.columns([1, 10, 1], gap="small")

with col_plus:
    # Plus button for file upload - white styling
    if st.button("➕", key="upload_btn", help="Upload file", use_container_width=True):
        st.session_state.show_upload_menu = True

with col_text:
    # Text input with larger font
    def on_text_change():
        st.session_state.text_input_value = st.session_state.user_input_field
    
    user_text = st.text_input(
        "message",
        value=st.session_state.text_input_value,
        placeholder="Describe suspicious activity, upload media, or ask follow-up questions...",
        label_visibility="collapsed",
        on_change=on_text_change,
        key="user_input_field",
    )

with col_send:
    # Send button - white styling
    send_clicked = st.button("⬆️", key="send_btn", help="Send (Enter key also works)", use_container_width=True)

# FILE UPLOAD 
if st.session_state.show_upload_menu:
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Custom styled upload menu with white background
    st.markdown("""
    <style>
    .upload-buttons-container {
        display: flex;
        gap: 0.8rem;
        margin: 0.4rem 0;
    }
    </style>
    <div class="upload-buttons-container">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📄 PDF/DOCX", key="doc_upload", use_container_width=True):
            st.session_state.upload_type = "doc"
            st.session_state.show_upload_menu = False
            st.session_state.show_file_picker = True
    
    with col2:
        if st.button("🖼️ Image", key="img_upload", use_container_width=True):
            st.session_state.upload_type = "img"
            st.session_state.show_upload_menu = False
            st.session_state.show_file_picker = True
    
    with col3:
        if st.button("🎵 Audio", key="aud_upload", use_container_width=True):
            st.session_state.upload_type = "aud"
            st.session_state.show_upload_menu = False
            st.session_state.show_file_picker = True
    
    st.markdown("</div>", unsafe_allow_html=True)

# Simple file uploader 
if st.session_state.get("show_file_picker", False):
    upload_type = st.session_state.get("upload_type", "doc")
    
    file_types_map = {
        "doc": ["pdf", "docx"],
        "img": ["png", "jpg", "jpeg"],
        "aud": ["mp3", "wav"]
    }
    
    type_label_map = {
        "doc": "Document (PDF, DOCX)",
        "img": "Image (PNG, JPG, JPEG)",
        "aud": "Audio (MP3, WAV)"
    }
    
    uploaded_file = st.file_uploader(
        f"Upload {type_label_map.get(upload_type, 'file')}",
        type=file_types_map.get(upload_type, []),
        key="file_upload_simple"
    )
    
    if uploaded_file is not None:
        path = save_temp(uploaded_file)
        size_kb = round(uploaded_file.size / 1024, 1)
        st.session_state.pending_file = {
            "name": uploaded_file.name,
            "path": path,
            "size": f"{size_kb} KB"
        }
        
        st.markdown(f"""
<div style="background: #1a4d6d; padding: 0.8rem; border-radius: 8px; border-left: 3px solid #00d9ff; margin-top: 0.4rem;">
  <div style="display: flex; align-items: center; gap: 0.8rem;">
    <div style="font-size: 1.4rem;">{file_icon(uploaded_file.name)}</div>
    <div>
      <div style="color: #e2e8f0; font-weight: 500; font-size: 0.85rem;">{uploaded_file.name}</div>
      <div style="color: #38bdf8; font-size: 0.75rem;">📦 {size_kb} KB • Ready to analyze</div>
    </div>
  </div>
  <div style="color: #cbd5e1; font-size: 0.8rem; margin-top: 0.6rem;">💡 Tip: Add a question above to ask about this file</div>
</div>""", unsafe_allow_html=True)

# SEND / ANALYZE
if send_clicked:
    pf = st.session_state.pending_file
    text_query = user_text.strip() if user_text else ""
    
    # Create a hash of the current input to prevent reprocessing on reruns
    import hashlib
    current_input_hash = hashlib.md5(f"{pf}{text_query}".encode()).hexdigest() if (pf or text_query) else None
    
    # Check if this is a new input (not previously processed)
    if current_input_hash != st.session_state.get("last_processed_input"):
        # Handle different input scenarios
        if pf and text_query:
            # Both file and text - combined analysis with query
            st.session_state.last_processed_input = current_input_hash
            process_and_respond(
                user_input=pf["path"],
                display_text=pf["name"],
                file_info={"name": pf["name"], "size": pf["size"]},
                additional_query=text_query
            )
        elif pf and not text_query:
            # File only (button clicked with file)
            st.session_state.last_processed_input = current_input_hash
            process_and_respond(
                user_input=pf["path"],
                display_text=pf["name"],
                file_info={"name": pf["name"], "size": pf["size"]},
            )
        elif text_query and not pf:
            # Text only (no file)
            st.session_state.last_processed_input = current_input_hash
            process_and_respond(
                user_input=text_query,
                display_text=text_query,
            )
        else:
            # Empty input
            st.warning("📝 Type a message or 📎 attach a file", icon="⚠️")
    else:
        pass

# FOOTER
st.markdown("""
<div style='margin-top: 3rem; text-align: center; padding-top: 1rem; border-top: 1px solid #1a6080;'>
    <div class="fg-footer">
        Made with 💓 by <strong>killers_of_threats</strong>
    </div>
</div>""", unsafe_allow_html=True)