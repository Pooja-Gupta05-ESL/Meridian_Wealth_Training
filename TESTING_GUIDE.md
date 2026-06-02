# Meridian Wealth AI Desk — Testing Guide

## Quick Start

### 1. Check Agent Health
Open your browser and go to:
```
http://127.0.0.1:8000/diagnostic
```

This shows:
- ✅/❌ API keys configured
- ✅/❌ LangChain packages installed
- ✅/❌ Database populated
- ✅/❌ Policy PDFs available
- **Recommendations** for fixes

---

## Setup Steps to Enable Live Agent

### Step 1: Configure API Keys

**Create `.env` file** in `financial_analyst_app/`:
```bash
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here
```

Get keys from:
- **OpenAI:** https://platform.openai.com/api-keys
- **Tavily:** https://tavily.com/dashboard

### Step 2: Install LangChain Packages
```powershell
cd "d:\AI Training\financial_analyst_app"
..\Training\.venv\Scripts\Activate.ps1

pip install langchain langchain-openai langchain-community langchain-tavily faiss-cpu pypdf
```

### Step 3: Add Policy PDFs
1. Extract `policy_documents.zip` from `Lab_6.4_Financial_Analyst_Agent.ipynb`
2. Place PDFs in: `data/policy_document/`
3. Expected files: 5 PDF policy documents

### Step 4: Seed Database (if empty)
If database has 0 clients/holdings:
1. Run `Lab_4.1_Document_Loaders_Chunking.ipynb` OR
2. Run `Lab_4.2_Embeddings_Vector_Stores.ipynb`

This populates: `data/meridian_wealth.db`

### Step 5: Restart Server
```powershell
# Kill existing process
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force

# Restart
Set-Location "d:\AI Training\financial_analyst_app"
& "..\Training\.venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
```

---

## Testing via Web UI

### Access Chat Interface
```
http://127.0.0.1:8000/
```

**Features:**
- Left: Chat log with message history
- Right: Connection status, Agent info, Tools called
- Enter client name (optional) and message
- Send button triggers agent

### What Good Responses Look Like

✅ **Live Agent Response:**
```
Financial Analyst Response for Rajesh Mehta

Portfolio Summary:
- Total Value: ₹2,450,000
- Overall Return: +18.5%
- Top Sector: IT (42%)

Market Context:
- IT sector YTD: +22.3% (analyst rating: Strong Buy)
- Pharma: +8.1%

Policy Compliance:
[Investment_Policy_Framework.pdf | Page 5]
"Maximum single-stock concentration for Moderate-Aggressive profile is 10%."

Current allocation check: ✅ COMPLIANT

Recommendations:
- Increase Pharma from 12% → 18%
- Trim IT from 42% → 35%
```

❌ **Scaffold Response (Agent not ready):**
```
This is the FastAPI scaffold response. Integrate your LangChain/LangGraph agent 
in source/agent_runtime.py to return live analysis.

Data check: clients=0, holdings=0.
```

---

## Testing via PowerShell API

### Test 1: Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get | ConvertTo-Json
```

**Expected:** `{ "status": "ok" }`

---

### Test 2: Agent Info
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/agentinfo" -Method Get | ConvertTo-Json
```

**Expected:**
```json
{
  "name": "Financial Analyst Agent",
  "version": "1.0.0",
  "status": "ready",
  "tools": ["portfolio_lookup", "market_data_search", "calculate_metrics", "policy_retriever", "tavily_search"]
}
```

---

### Test 3: Diagnostic Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/diagnostic" -Method Get | ConvertTo-Json -Depth 5
```

**Expected Output:**
```json
{
  "api_keys": {
    "openai": "✅ Set",
    "tavily": "✅ Set"
  },
  "dependencies": {
    "langchain": "✅ Installed",
    "langchain_openai": "✅ Installed",
    ...
  },
  "database": {
    "file": "✅ Found (150 KB)",
    "clients_count": 50,
    "holdings_count": 250
  },
  "policy_pdfs": {
    "directory": "✅ Found",
    "count": 5,
    "files": ["Investment_Policy_Framework.pdf", ...]
  },
  "status": "✅ Ready"
}
```

---

### Test 4: Portfolio Lookup (Live Agent)
```powershell
$body = @{
    message = "What is the portfolio allocation for client CLT-001?"
    client_name = "Rajesh Mehta"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Output $result.answer
Write-Output "Tools: $($result.tools_used)"
```

---

## 4 Canonical Test Queries

### **Test 1: Client Quarterly Briefing**
```powershell
$msg = @"
Prepare a quarterly briefing for Client CLT-001 (Rajesh Mehta).
Include portfolio performance, market context, policy compliance check,
and rebalancing recommendations.
"@

$body = @{ message = $msg; client_name = "Rajesh Mehta" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" -Method Post -ContentType "application/json" -Body $body
$result.answer
```

**✅ Expected:** Portfolio summary + market outlook + policy compliance + recommendations

**Tools Used:** `portfolio_lookup`, `market_data_search`, `policy_retriever`, `web_search`

---

### **Test 2: Cross-Client Comparison**
```powershell
$msg = "Compare IT sector exposure for CLT-001 vs CLT-002. Check policy limits."

$body = @{ message = $msg; client_name = "Portfolio Manager" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" -Method Post -ContentType "application/json" -Body $body
$result.answer
```

**✅ Expected:** Allocation comparison + policy excerpt + recommendations

**Tools Used:** `portfolio_lookup`, `policy_retriever`, `market_data_search`

---

### **Test 3: Concentration Policy Check**
```powershell
$msg = @"
Client CLT-003 wants to increase Adani position. 
Check current allocation, policy limits for Aggressive profile.
Is this permissible?
"@

$body = @{ message = $msg; client_name = "Amit Choudhury" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" -Method Post -ContentType "application/json" -Body $body
$result.answer
```

**✅ Expected:** Current position % + policy limit (with PDF citation) + verdict (PERMISSIBLE/NOT PERMISSIBLE)

**Tools Used:** `portfolio_lookup`, `policy_retriever`, `calculate_metrics`

---

### **Test 4: Market Intelligence & Sector Outlook**
```powershell
$msg = @"
Client CLT-005 has heavy Telecom (32%) and Auto (28%) exposure.
Search for latest RBI updates and sector outlook.
Recommend portfolio actions.
"@

$body = @{ message = $msg; client_name = "Karan Malhotra" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" -Method Post -ContentType "application/json" -Body $body
$result.answer
```

**✅ Expected:** Current exposure + latest market news + risk/opportunity analysis + rebalancing recommendation

**Tools Used:** `portfolio_lookup`, `web_search`, `market_data_search`

---

## Troubleshooting

### Problem: "Agent not initialized"

**Diagnosis:**
```powershell
$diag = Invoke-RestMethod -Uri "http://127.0.0.1:8000/diagnostic" -Method Get
$diag.recommendations
```

This lists exactly what's missing.

**Common Fixes:**

1. **Missing API Keys**
   ```powershell
   # Check .env exists and has keys
   cat ".env"
   
   # Or set as environment variables
   $env:OPENAI_API_KEY = "sk-..."
   $env:TAVILY_API_KEY = "tvly-..."
   ```

2. **Missing LangChain**
   ```powershell
   pip list | grep langchain
   # If missing, install:
   pip install langchain langchain-openai langchain-community langchain-tavily
   ```

3. **Empty Database**
   ```powershell
   # Check data
   sqlite3 "data/meridian_wealth.db" "SELECT COUNT(*) FROM clients;"
   
   # If 0, seed from Lab_4.1 or create test data
   ```

4. **No Policy PDFs**
   ```powershell
   ls "data/policy_document/"
   # If empty, extract policy_documents.zip from notebook
   ```

---

### Problem: Port 8000 Already in Use

```powershell
# Find & kill process
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force

# Start fresh
uvicorn app:app --host 127.0.0.1 --port 8000
```

---

### Problem: Response is Generic Scaffold

This means the ReAct agent failed to initialize. The UI will now show a helpful error message:

```
⚠️ Agent not initialized.

To enable live agent responses:
1. Set API Keys in .env
2. Add Policy PDFs to data/policy_document/
3. Seed Database with test data
4. Install LangChain: pip install langchain ...
5. Restart server
```

---

## Expected Behavior After Setup

| Check | Before Setup | After Setup |
|-------|---------|------------|
| `/health` | 200 OK | 200 OK |
| `/agentinfo` | Returns metadata | Returns metadata |
| `/diagnostic` | Shows missing items | Status: "✅ Ready" |
| Chat response | Scaffold text | Real agent analysis |
| Tools called | None | portfolio_lookup, policy_retriever, web_search, etc. |
| DB data | 0 clients | 50+ clients |
| PDFs | Not found | 5 PDFs loaded into FAISS |

---

## Success Checklist

✅ API keys configured in `.env`
✅ LangChain packages installed
✅ Database populated (> 0 clients)
✅ Policy PDFs in `data/policy_document/`
✅ `/diagnostic` endpoint shows green checkmarks
✅ Chat responds with structured analysis (not scaffold)
✅ Tools are called and logged
✅ Policy citations include document name + page number

Once all checked, you have a **production-grade ReAct agent** running! 🚀
