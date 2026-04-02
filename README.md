# **FinGuard - AI-Powered Fraud Detection System**

## **Project Overview**

FinGuard is an advanced financial fraud detection system built for the IIT Delhi Hackathon. 
It combines cutting-edge AI technologies to analyze financial messages, documents, 
and transactions in real-time to identify fraud patterns and provide actionable insights.

**Tagline:** "We see Threats, we kill them!"
### **Key Features**
✅ Multi-format input support (text, PDF, DOCX, images, audio)  
✅ Real-time fraud detection using LLM analysis  
✅ Graph-based pattern recognition via TigerGraph  
✅ Market intelligence through web search  
✅ Conversational follow-up questions about analyses  
✅ Session-based conversation context preservation  
✅ Risk scoring with severity classifications  

## **Project Architecture**

### **Technology Stack**
- **Frontend:** Streamlit (Python web framework)
- **Backend Orchestration:** LangGraph (workflow management)
- **LLM:** Groq (llama-3.1-8b-instant)
- **Graph Database:** TigerGraph (pattern analysis)
- **Web Search:** Tavily API (market insights)
- **API Server:** FastAPI + Uvicorn
- **Document Processing:** PyMuPDF, python-docx, pytesseract
- **Data Processing:** Pandas, NumPy, scikit-learn

### **File Structure**
FinGuard_IIT_Delhi hackathon/
├── finguard.py                          # Main Streamlit application (UI & orchestration)
├── style.py                             # CSS styling for Streamlit interface
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables (credentials)
│
├── graph/
│   └── graph_backend.py                # LangGraph workflow & analysis nodes
│
├── endpoints_connection.py              # FastAPI endpoints
├── tigergraph_client.py                 # TigerGraph database connection
├── enhanced_conversation_node.py        # Enhanced conversation handling
│
├── compressed_pattern_dataset.py        # Pattern data processing utility
├── compressed_transaction_vertex.py     # Transaction vertex optimization
│
└── finguard_backend/                   # Virtual environment (optional)


## **Workflow & Data Flow**

### **Analysis Pipeline (5-Node LangGraph)**

The system uses a sequential LangGraph with the following processing nodes:

User Input (Text/File)
         ↓
[1] EXTRACT CONTEXT NODE
    ├─ Processes multiple file formats
    ├─ PDF extraction (PyMuPDF)
    ├─ DOCX extraction (python-docx)
    ├─ Image OCR (pytesseract)
    ├─ Audio transcription (Groq Whisper)
    └─ Stock detection & intent classification
         ↓
[2] FRAUD DETECTION NODE
    ├─ Rule-based signal detection (5 patterns)
    ├─ LLM-based fraud analysis (Groq)
    ├─ Pattern extraction
    └─ Fraud score calculation
         ↓
[3] GRAPH INTELLIGENCE NODE
    ├─ TigerGraph vertex/edge insertion
    ├─ Pattern relationship mapping
    ├─ Graph query execution
    └─ Network risk scoring
         ↓
[4] WEB SEARCH NODE
    ├─ Tavily search API integration
    ├─ Market intelligence collection
    ├─ Insight caching
    └─ Web risk assessment
         ↓
[5] RISK SCORING & DECISION NODE
    ├─ Multi-factor risk aggregation
    ├─ Threshold-based decision making
    ├─ LLM-generated explanations
    └─ Final decision (SAFE/WARNING/FRAUD/CRITICAL_FRAUD)
         ↓
    Response to User

### **Conversation Pipeline (Single-Node)**
- Accepts follow-up questions about previous analyses
- Uses comprehensive context from analysis
- Provides detailed explanations without re-analyzing

## **Key Components Overview**

### **1. Frontend (finguard.py)**
- Streamlit application with responsive UI
- Session state management for conversation flow
- File upload with temporary file handling
- Message rendering with result cards
- Sidebar with statistics and controls

**Key Functions:**
- `call_backend()` - Routes to analysis or conversation mode
- `process_and_respond()` - Handles user input and displays results
- `render_messages()` - Displays chat history with formatting
- `is_follow_up_question()` - Detects follow-up vs. new analysis

### **2. Backend Graph (graph/graph_backend.py)**
- Defines `FinGuardState` - TypedDict for analysis state
- Implements 5 processing nodes
- LLM caching to avoid duplicate API calls
- Web search caching for market data

**Key Functions:**
- `extract_context()` - File processing and text extraction
- `fraud_detection_node()` - Fraud pattern detection
- `graph_intelligence_node()` - TigerGraph analysis
- `web_search_node()` - Market data collection
- `risk_score_calculation()` - Final scoring and decision
- `conversation_node()` - Context-aware answer generation

### **3. Styling (style.py)**
- Dark-themed CSS for FinGuard branding
- Gradient backgrounds (blue/teal)
- Custom message bubbles
- Responsive card layouts
- Sidebar styling

### **4. Database Connection (tigergraph_client.py)**
- Establishes TigerGraph connection
- Initializes with cloud credentials
- Token generation and connection testing

### **5. API Endpoints (endpoints_connection.py)**
- POST `/analyze` - Accepts text/file for analysis
- Supports `mode` parameter: "analyze" or "converse"
- Returns structured fraud detection results

### **Step 1: Clone the Repository**
bash
# Clone the repository
git clone https://github.com/[your-username]/FinGuard_IIT_Delhi.git
cd FinGuard_IIT_Delhi\ hackathon

# Or if downloading as ZIP, extract and navigate to the folder
cd Desktop/"FinGuard_IIT_Delhi hackathon"

### **Step 2: Create a Virtual Environment (Recommended)**

**On Windows:**
bash
python -m venv finguard_env
finguard_env\Scripts\activate

**On macOS/Linux:**
bash
python3 -m venv finguard_env
source finguard_env/bin/activate

### **Step 3: Install Dependencies**
bash
# Install all required packages
pip install -r requirements.txt

**Key Dependencies:**
langgraph - Graph orchestration
streamlit - Web UI framework
pyTigerGraph==1.8.0 - TigerGraph client
fastapi - API framework
groq - Groq LLM API
tavily-python - Web search API
pymupdf - PDF processing
python-docx - Word document processing
pytesseract - OCR for images

### **Step 4: Install Tesseract OCR**
**On Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run: `tesseract-ocr-w64-setup-v5.x.x.exe`
3. Default installation path: `C:\Program Files\Tesseract-OCR`

**On macOS:**
```bash
brew install tesseract
```

**On Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### **Step 5: Create .env File**

Create a .env file in the project root with your API credentials:

```env
# Groq LLM API
GROQ_API_KEY=your_groq_api_key_here

# Tavily Web Search
TAVILY_WEB_SEARCH_KEY=your_tavily_api_key_here

# TigerGraph Database Credentials
TG_HOST=your_tigergraph_host
TG_GRAPH_NAME=your_graph_name
TG_SECRET_KEY=your_tigergraph_secret

# Optional: Tesseract Path (if not in default location)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### **How to Get API Keys:**

1. **Groq API Key:**
   - Visit: https://console.groq.com
   - Sign up and create API key
   - Copy key to .env

2. **Tavily API Key:**
   - Visit: https://tavily.com
   - Sign up and generate API key
   - Copy key to .env

3. **TigerGraph Credentials:**
   - Access your TigerGraph instance
   - Get host URL, graph name, and secret key(code is present in my tigergraph_client.py file, access it from there).
   - Populate .env with credentials

## **Execution Steps**
bash
# Activate virtual environment first
# On Windows:
finguard_env\Scripts\activate
# On macOS/Linux:
source finguard_env/bin/activate

# Run Streamlit app (automatically opens browser)
streamlit run finguard.py

The application will start on `http://localhost:8501`

## **Usage Guide**

### **1. Text-Based Fraud Analysis**
1. Open the application at `http://localhost:8501`
2. In the message input field, type a suspicious financial message
3. Click "⬆️ Send" or press Enter
4. View analysis results (Risk Score, Decision, Explanation)

### **2. Document Analysis**
1. Click "➕" button to open upload menu
2. Select "📄 PDF/DOCX" for documents
3. Upload a PDF or Word document
4. **Optional**: Add a query/question in the text field
5. Click "⬆️ Send"
6. View extracted content and fraud analysis

### **3. Image Analysis**
1. Click "➕" button
2. Select "🖼️ Image"
3. Upload PNG, JPG, or JPEG file
4. Add optional query about the image
5. System extracts text via OCR and analyzes for fraud

### **4. Audio Analysis**
1. Click "➕" button
2. Select "🎵 Audio"
3. Upload MP3 or WAV file
4. System transcribes audio and analyzes for fraud
5. View transcribed text and fraud score

### **5. Follow-Up Questions**
1. After analyzing content, ask follow-up questions:
   - "Why was this detected as fraud?"
   - "What are the specific risk factors?"
   - "How can I protect against this?"
2. System answers using full context from previous analysis

### **6. Session Management**
- Click "🗑️ Clear Chat" to reset conversation
- Sidebar shows: Total analyzed count, Fraud detected count
- All conversations isolated per session

## 🔍 **Fraud Detection Patterns**
The system detects these fraud indicators:
| Pattern | Detection Method | Risk Level |
|---------|------------------|-----------|
| **Urgency Pressure** | High-urgency keywords + time pressure | High |
| **Fear Triggers** | Panic words (crash, loss, drop, panic) | High |
| **Authority Claims** | False expert/insider claims | Medium |
| **Manipulation** | Emotional pressure + intent combo | Medium |
| **Greed Exploitation** | Guaranteed profit, 100% claims | High |
| **Graph Patterns** | TigerGraph relationship analysis | Medium |
| **Web Verification** | Market data authenticity check | Variable |

## **Risk Scoring Algorithm**
Final Risk = (0.25 × Fraud_Score) + (0.20 × Graph_Score) + (0.15 × Web_Risk)

Decision Thresholds:
├─ 0.00-0.25 → SAFE (Green)
├─ 0.25-0.50 → WARNING (Yellow)
├─ 0.50-0.75 → FRAUD (Red)
└─ 0.75-1.00 → CRITICAL_FRAUD (Dark Red)

**Fraud Score Components:**
- Rule-based signals (40%)
- LLM analysis (60%)

**Graph Score:**
- Pattern risk (25%)
- Message volume risk (20%)
- Transaction risk (25%)
- Network risk (30%)

## **Project Structure Details**

### **State Management (FinGuardState)**
python
class FinGuardState(TypedDict):
    user_input: str                    # Raw user input
    clean_text: str                    # Extracted text
    input_type: str                    # text/document/image/audio
    stock: str                         # Detected stock symbol
    urgency: str                       # high/low
    intent: str                        # buy/sell/hold
    fraud_signals: Dict               # Detection flags
    fraud_score: float                # 0-1 fraud probability
    fraud_reason: str                 # LLM explanation
    web_insights: Dict                # Market data
    graph_features: Dict              # Graph analysis results
    risk_score: float                 # Final risk 0-1
    risk_level: str                   # risk category
    decision: str                     # SAFE/WARNING/FRAUD
    message: str                      # Final explanation

### **Conversation Flow**
1. User submits text/file → Analysis mode triggered
2. System stores all analysis data in `analysis_context`
3. Follow-up questions detected → Conversation mode triggered
4. Previous context passed to LLM for answering
5. Response includes full context reasoning

## **Security & Privacy**

- Temporary files auto-deleted after processing
- Session state isolated per browser
- No data persistence (in-memory only)
- API keys stored in .env (excluded from git)
- TigerGraph connection secured with secret key

## **Future Enhancements**

- [ ] Real-time WebSocket for live fraud alerts
- [ ] Multi-language support
- [ ] Advanced visualization dashboard
- [ ] Fraud pattern export (CSV/JSON)
- [ ] Historical analysis storage
- [ ] Email/SMS alerts
- [ ] Machine learning model fine-tuning
- [ ] Blockchain integration for audit trail
