FINGUARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── Base Theme ── */
html, body { margin: 0; padding: 0; }

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a2642 0%, #1a4d6d 50%, #0d3a5c 100%) !important;
    font-family: 'Sora', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0 !important;
}

[data-testid="stMain"] {
    background: linear-gradient(135deg, #0a2642 0%, #1a4d6d 50%, #0d3a5c 100%) !important;
}

/* Hide Streamlit Elements */
#MainMenu { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
footer { visibility: hidden; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f1419; }
::-webkit-scrollbar-thumb { background: #2d3e52; border-radius: 3px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d3a5c 0%, #0a2642 100%) !important;
    border-right: 1px solid #1a6080 !important;
}
[data-testid="stSidebarContent"] { padding: 1.5rem 1.2rem !important; }

[data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem !important;
    padding-bottom: 140px !important;
    max-width: 800px !important;
}

/* ── Header ── */
.fg-header {
    text-align: center;
    padding: 1.5rem 0 0.6rem 0;
    margin-bottom: 0.2rem;
}

.fg-header .shield {
    font-size: 3rem;
    display: block;
    margin-bottom: 0.4rem;
}

.fg-header h1 {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d9ff 0%, #0099ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
    text-transform: uppercase;
}

.fg-header p {
    color: #38bdf8;
    font-size: 0.7rem;
    margin: 0.4rem 0 0 0;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    font-style: italic;
}

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
}

.empty-state h3 { 
    font-size: 0.95rem; 
    color: #7f92b0; 
    margin-bottom: 0.3rem;
    font-weight: 500;
}

.empty-state p { 
    font-size: 0.78rem; 
    color: #4f5f72; 
    margin: 0; 
}

.chips {
    display: flex;
    gap: 0.6rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.chip {
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 20px;
    padding: 0.4rem 0.9rem;
    font-size: 0.75rem;
    color: #7f92b0;
}

/* ── Messages ── */
.msg-row {
    display: flex;
    margin-bottom: 0.8rem;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.msg-row.user { justify-content: flex-end; }
.msg-row.bot { justify-content: flex-start; }

.msg-bubble {
    max-width: 72%;
    padding: 0.75rem 1rem;
    border-radius: 14px;
    font-size: 0.85rem;
    line-height: 1.5;
    word-wrap: break-word;
}

.msg-bubble.user {
    background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%);
    color: #e0f2fe;
    border-bottom-right-radius: 2px;
}

.msg-bubble.bot {
    background: #1a2332;
    border: 1px solid #2d3e52;
    color: #cbd5e1;
    border-bottom-left-radius: 2px;
}

.msg-meta {
    font-size: 0.65rem;
    color: #4f5f72;
    margin-top: 0.2rem;
    padding: 0 0.2rem;
}

.msg-row.user .msg-meta { text-align: right; }
.msg-row.bot .msg-meta { text-align: left; }

/* ── File Chip ── */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    font-size: 0.78rem;
    color: #94a3b8;
}

/* ── Result Card ── */
.result-card {
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 0.4rem;
}

.decision-badge {
    display: inline-block;
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}

.badge-SAFE { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.badge-WARNING { background: #2d1f00; color: #fbbf24; border: 1px solid #92400e; }
.badge-FRAUD { background: #2d0505; color: #f87171; border: 1px solid #991b1b; }
.badge-UNKNOWN { background: #1a2332; color: #94a3b8; border: 1px solid #2d3e52; }

.risk-lbl {
    font-size: 0.65rem;
    color: #7f92b0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}

.risk-track {
    background: #2d3e52;
    border-radius: 999px;
    height: 6px;
    overflow: hidden;
    margin-bottom: 0.6rem;
}

.risk-fill { height: 100%; border-radius: 999px; }

.risk-pct {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.explanation {
    font-size: 0.78rem;
    color: #7f92b0;
    line-height: 1.6;
    border-top: 1px solid #2d3e52;
    padding-top: 0.6rem;
    margin-top: 0.2rem;
}

/* ── Streamlit Inputs ── */
[data-testid="stTextInput"] > div > div > input {
    background: #FFFFFF !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 12px !important;
    color: #1a1a1a !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 1rem !important;
    caret-color: #0099ff !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08) !important;
    transition: all 0.2s ease !important;
    min-height: 50px !important;
}

[data-testid="stTextInput"] > div > div > input::placeholder {
    color: #999999 !important;
    font-size: 0.95rem !important;
}

[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #0099ff !important;
    box-shadow: 0 0 0 4px rgba(0, 153, 255, 0.15), 0 2px 12px rgba(0, 0, 0, 0.12) !important;
    outline: none !important;
    background: #FFFFFF !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: #FFFFFF !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 12px !important;
    color: #0099ff !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    padding: 0.75rem 1.2rem !important;
    height: 50px !important;
    min-height: 50px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stButton"] > button:hover {
    background: #f0f8ff !important;
    border-color: #0099ff !important;
    box-shadow: 0 4px 16px rgba(0, 153, 255, 0.2) !important;
    transform: none !important;
}

[data-testid="stButton"] > button:active {
    background: #e6f2ff !important;
    border-color: #0066cc !important;
}

/* ── Columns ── */
[data-testid="stColumn"] {
    background: transparent !important;
}

.upload-buttons-container {
    background: transparent !important;
    display: flex;
    gap: 0.8rem;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] section {
    background: #1a2332 !important;
    border: 1px dashed #2d3e52 !important;
    border-radius: 8px !important;
    padding: 0.8rem !important;
}

[data-testid="stFileUploaderFileName"] { color: #7f92b0 !important; font-size: 0.75rem !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #1a2332 !important;
    border: 1px solid #2d3e52 !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] summary { color: #7f92b0 !important; font-size: 0.78rem !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: #38bdf8 !important; }

/* ── Sidebar Custom ── */
.sb-logo { 
    text-align: center; 
    padding: 0.8rem 0 1rem; 
    border-bottom: 1px solid #2d3e52; 
    margin-bottom: 1rem; 
}

.sb-logo h2 {
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0.2rem 0 0;
    background: linear-gradient(135deg, #38bdf8, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.sb-section { 
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #4f5f72;
    margin: 1rem 0 0.5rem;
    font-weight: 600;
}

.sb-team-card { 
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.6rem;
}

.sb-team-name { 
    font-size: 0.75rem;
    color: #38bdf8;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.sb-member { 
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    font-size: 0.75rem;
    color: #7f92b0;
}

.sb-dot { 
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #38bdf8;
    flex-shrink: 0;
}

.sb-desc { 
    font-size: 0.72rem;
    color: #4f5f72;
    line-height: 1.5;
}

.sb-stat { 
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
}

.sb-stat-val { 
    font-size: 1.1rem;
    font-weight: 600;
    color: #38bdf8;
}

.sb-stat-lbl { 
    font-size: 0.6rem;
    color: #4f5f72;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.sb-tech { 
    font-size: 0.72rem;
    color: #4f5f72;
    padding: 0.2rem 0;
}

/* ── Clear Button ── */
.clear-wrap [data-testid="stButton"] > button {
    background: #1a2332 !important;
    border: 1px solid #2d3e52 !important;
    color: #7f92b0 !important;
    box-shadow: none !important;
    font-size: 0.73rem !important;
}

.clear-wrap [data-testid="stButton"] > button:hover {
    border-color: #f87171 !important;
    color: #f87171 !important;
    transform: none !important;
}

/* ── Footer ── */
.fg-footer {
    text-align: center;
    font-size: 0.75rem;
    color: #38bdf8;
    letter-spacing: 0.05em;
    padding: 0.3rem 0;
    font-weight: 700;
}

/* ── Upload Button (Plus) ── */
.upload-plus-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    background: #0f1419;
    border: 2px solid #2d3e52;
    border-radius: 10px;
    font-size: 1.6rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.upload-plus-btn:hover {
    border-color: #38bdf8;
    background: #1a2332;
}

/* ── Modal Menu ── */
.upload-menu {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #1a2332;
    border: 1px solid #2d3e52;
    border-radius: 14px;
    padding: 1.2rem;
    z-index: 9999;
    min-width: 300px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
}

.upload-menu-item {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-bottom: 0.6rem;
}

.upload-menu-item:hover {
    background: #2d3e52;
}

.upload-menu-item:last-child {
    margin-bottom: 0;
}

.upload-menu-icon {
    font-size: 1.4rem;
}

.upload-menu-text {
    font-size: 0.85rem;
    color: #e2e8f0;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9998;
}
</style>
"""