# Meridian Wealth Financial Analyst Agent - Deployment Guide

## Project Overview

A production-ready FastAPI backend for an AI-powered financial advisor chatbot using the Lab 6.4 LangChain agent pattern with ReAct tool-calling, RAG pipeline, and web search capabilities.

## Architecture

### Backend Stack
- **Framework**: FastAPI with Uvicorn
- **LLM**: OpenAI GPT-4 Turbo (ReAct agent pattern)
- **Vector DB**: FAISS + text-embedding-3-small
- **Document Retrieval**: RAG pipeline over policy PDFs
- **Web Search**: Tavily API
- **Database**: SQLite with client portfolios and market data
- **Frontend**: Single HTML page (index.html) with JavaScript

### Directory Structure (Clean & Consolidated)

```
financial_analyst_app/
├── app.py                      # FastAPI entry point
├── requirements.txt            # Python dependencies
├── seed_db.py                  # Database seeding script
├── run_tests.py                # Test suite for Lab 6.4
├── test_agent.py               # Quick test script
├── DEPLOYMENT_GUIDE.md         # This file
├── README.md
├── scaffold.py                 # Unused utility
│
├── source/                     # Agent implementation
│   ├── __init__.py
│   ├── agent_runtime.py        # Core agent, tools, RAG pipeline
│   ├── databasequery.py        # Database helpers (optional)
│   ├── rag_pipeline.py         # RAG utilities (optional)
│   └── schemas.py              # Pydantic models
│
├── data/
│   ├── policy_document/        # 5 policy PDFs (extracted from Lab_6.4)
│   │   ├── Asset_Allocation_Policy.pdf
│   │   ├── Risk_Management_Guidelines.pdf
│   │   └── ...
│   │
│   └── vector_db/              # ✅ SINGLE DATABASE LOCATION
│       ├── meridian_wealth.db  # SQLite: clients, holdings, market_data
│       └── [FAISS index files]
│
├── frontend/                   # ✅ SINGLE HTML ENTRY POINT
│   ├── index.html              # Main chat UI
│   ├── css/
│   │   └── chat.css
│   ├── js/
│   │   └── chat.js
│   └── assets/
│       ├── styles.css
│       └── [other assets]
```

## Setup & Installation

### 1. Prerequisites
```bash
# Ensure you have Python 3.10+ and pip
python --version

# Create/activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Key packages:**
- fastapi, uvicorn
- langchain, langchain-openai, langchain-community, langchain-tavily
- faiss-cpu (or faiss-gpu)
- pypdf, python-dotenv

### 3. Configuration - Create `.env` file
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional, for fallback
```

### 4. Populate Database
```bash
# Create tables and seed test data (5 clients, 8 holdings)
python seed_db.py
```

**Output:**
```
✅ Database populated successfully!

Available Clients:
  CLT-001: Rajesh Mehta (Moderate-Aggressive) - AUM: ₹2,500,000
  CLT-002: Amit Choudhury (Aggressive) - AUM: ₹5,000,000
  CLT-003: Karan Malhotra (Moderate) - AUM: ₹1,800,000
  CLT-004: Neha Gupta (Conservative) - AUM: ₹1,200,000
  CLT-005: Rohan Singh (Moderate-Aggressive) - AUM: ₹3,500,000
```

### 5. Extract Policy PDFs
Copy 5 policy PDF files to `data/policy_document/`:
- Asset_Allocation_Policy.pdf
- Risk_Management_Guidelines.pdf
- Concentration_Limits_Policy.pdf
- Liquidity_Management_Policy.pdf
- ESG_Investment_Policy.pdf

(Extract from Lab_6.4 notebook if available)

## Running the Server

### Development Mode
```bash
cd financial_analyst_app
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Production Mode (Gunicorn)
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
```

### Server Initialization Output
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
✅ API keys loaded
⏳ Initializing RAG pipeline...
✅ RAG pipeline ready
⏳ Creating LLM and agent...
✅ Agent initialized successfully!
INFO:     Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

## API Endpoints

### Chat Endpoints
**POST** `/main/chat`
- Main interface for chatbot
- Request: `{"message": str, "client_name": str (optional)}`
- Response: `{"answer": str, "tools_used": list[str], "sources": list[str]}`

**POST** `/api/ask`
- Alternative chat endpoint
- Same request/response format

### Diagnostic Endpoints
**GET** `/health`
- Health check
- Response: `{"status": "ok"}`

**GET** `/agentinfo`
- Agent metadata and available tools
- Returns: agent name, version, tools list

**GET** `/diagnostic`
- Full system diagnostics
- Checks: API keys, dependencies, database, policy PDFs
- Returns: status, recommendations

### Frontend
**GET** `/`
- Serves `frontend/index.html`
- Single-page chat interface

## Tools Available to Agent

1. **portfolio_lookup(client_id)** → Client holdings, allocation, risk profile
2. **market_data_search(query)** → Search stocks by ticker, sector, company
3. **calculate_metrics(expression)** → Financial calculations (returns, comparisons)
4. **policy_retriever(query)** → RAG search over policy PDFs with citations
5. **web_search(query)** → Tavily live market news search

## Testing

### Quick Test
```bash
python test_agent.py
```

### Full Lab 6.4 Test Suite
```bash
python run_tests.py
```

**5 Test Cases:**
1. T1: Portfolio Lookup (CLT-001)
2. T2: Policy Concentration Limits Check
3. T3: IT Sector Comparison (CLT-001 vs CLT-002)
4. T4: Rebalancing Advice (CLT-005)
5. T5: Web Search (Banking sector outlook)

## Example Queries

```
1. "Show portfolio for CLT-001 with holdings breakdown and risk assessment"
2. "What are the concentration limits for CLT-001 given his Moderate-Aggressive profile?"
3. "Compare IT sector exposure between CLT-001 and CLT-002"
4. "Analyze CLT-005 portfolio and recommend rebalancing actions"
5. "What's the latest market outlook for banking sector in India?"
```

## Database Schema

### clients
- `client_id` (TEXT PRIMARY KEY): CLT-001, CLT-002, etc.
- `name`: Client name
- `risk_profile`: Conservative, Moderate, Moderate-Aggressive, Aggressive
- `investment_horizon`: Short, Medium, Long-term
- `aum_inr`: Assets under management
- `relationship_mgr`: Manager name
- `phone`, `email`, `city`, `join_date`, `last_review`

### holdings
- `client_id` (FK)
- `ticker`: Stock symbol (TCS, HDFC, INFY, etc.)
- `company_name`: Full company name
- `shares`, `avg_cost_basis`, `current_price`
- `sector`, `purchase_date`

### market_data
- `ticker` (PRIMARY KEY)
- `company_name`, `sector`
- `current_price`, `ytd_return_pct`, `pe_ratio`
- `analyst_rating`, `high_52w`, `low_52w`, `market_cap_cr`

## Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` file created with API keys
- [ ] Policy PDFs extracted to `data/policy_document/`
- [ ] `python seed_db.py` executed successfully
- [ ] Database verified in `data/vector_db/meridian_wealth.db`
- [ ] Server starts without errors
- [ ] Diagnostic endpoint shows ✅ Ready status
- [ ] Test queries execute successfully
- [ ] Frontend loads at http://127.0.0.1:8000

## Troubleshooting

### Agent initialization fails
```
Check /diagnostic endpoint:
GET http://127.0.0.1:8000/diagnostic
```

### "Client not found" errors
```
Verify database:
1. Confirm data/vector_db/meridian_wealth.db exists
2. Run: python seed_db.py
3. Check available clients in server logs
```

### RAG pipeline issues
```
Ensure policy PDFs in:
data/policy_document/ (need at least 1 PDF)
```

### API key errors
```
Verify .env file contains:
- OPENAI_API_KEY (required)
- TAVILY_API_KEY (required for web search)
```

## Performance Notes

- **Agent Initialization**: ~30-40 seconds on first request (RAG index building)
- **Query Processing**: 30-90 seconds (depends on tool calls)
- **Database Queries**: <100ms
- **RAG Search**: 500ms-2s
- **LLM Inference**: 10-30s

## File Cleanup (Already Done ✅)

Removed to consolidate project:
- ❌ `data/meridian_wealth.db` (old database root location)
- ❌ `frontend/briefing.html` (unused page)
- ❌ `frontend/assets/briefing.js` (unused script)
- ❌ Navigation link to briefing page in index.html

## Database Migration

If you had data in the old location:

```bash
# Old path (removed):
# data/meridian_wealth.db

# New path (active):
# data/vector_db/meridian_wealth.db

# Updated in:
# - source/agent_runtime.py (line 32)
# - app.py (line 139)
# - seed_db.py (line 3)
```

## Deployment to Production

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t meridian-agent:latest .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... -e TAVILY_API_KEY=tvly-... meridian-agent:latest
```

### Cloud Platforms
- **AWS**: Lambda + API Gateway, or EC2 with Gunicorn
- **GCP**: Cloud Run
- **Azure**: App Service
- **Heroku**: `Procfile`: `web: gunicorn -w 4 app:app`

## Support & Questions

For issues, refer to:
1. Lab 6.4 notebook for agent patterns
2. LangChain documentation
3. Server `/diagnostic` endpoint for system status

---

**Last Updated**: June 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
