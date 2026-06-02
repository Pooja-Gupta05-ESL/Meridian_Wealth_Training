# Meridian Wealth Chatbot — Test Cases

## Quick Test: Verify Server is Running

```powershell
# Test 1: Health Check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get

# Expected Response:
# {"status": "ok"}
```

---

## Test Suite 1: Basic Endpoint Tests

### Test 1.1: Health Check
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
Write-Host "Status: $($response.status)"
```
**Expected:** `status = "ok"`

---

### Test 1.2: Agent Info
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/agentinfo" -Method Get
$response | ConvertTo-Json
```
**Expected:**
```json
{
  "name": "Financial Analyst Agent",
  "version": "1.0.0",
  "tools": [
    "portfolio_lookup",
    "market_data_search", 
    "calculate_metrics",
    "policy_retriever",
    "tavily_search"
  ]
}
```

---

### Test 1.3: System Diagnostic
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/diagnostic" -Method Get
Write-Host "=== System Health ===" 
Write-Host "API Keys: $($response.api_keys | ConvertTo-Json)"
Write-Host "Database: Clients=$($response.database.clients_count), Holdings=$($response.database.holdings_count)"
Write-Host "Status: $($response.status)"
```
**Expected:**
- ✅ API keys configured
- ✅ All dependencies installed
- ✅ Database populated (> 0 clients)
- ✅ Policy PDFs available
- Status: "✅ Ready"

---

## Test Suite 2: Simple Chat Requests

### Test 2.1: Hello World
```powershell
$body = @{
    message = "Hello, what can you help me with?"
    client_name = "Test User"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "Answer: $($response.answer)"
Write-Host "Tools Used: $($response.tools_used -join ', ')"
```
**Expected:** 
- Response acknowledges it's a financial analyst chatbot
- Tools list included (even if empty)

---

### Test 2.2: Generic Portfolio Question
```powershell
$body = @{
    message = "What is a typical portfolio allocation?"
    client_name = "General"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:** General portfolio advice (no specific client data needed)

---

## Test Suite 3: Database-Dependent Tests

### Test 3.1: Portfolio Lookup (CLT-001)
```powershell
$body = @{
    message = "What is the portfolio allocation for client CLT-001?"
    client_name = "Rajesh Mehta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host $response.answer
Write-Host "Tools Used: $($response.tools_used -join ', ')"
```
**Expected:**
- Response includes portfolio details for CLT-001
- Tools used: `portfolio_lookup`
- Mentions sectors, allocations, top holdings

---

### Test 3.2: Multiple Clients Comparison
```powershell
$body = @{
    message = "Compare the investment profiles of CLT-001 and CLT-002"
    client_name = "Portfolio Manager"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:**
- Comparison of both clients' risk profiles and allocations
- Tools used: `portfolio_lookup`

---

### Test 3.3: Sector Analysis
```powershell
$body = @{
    message = "What is CLT-001's IT sector exposure? How does it compare to sector trends?"
    client_name = "Rajesh Mehta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:**
- Current IT allocation percentage
- Market data for IT stocks
- Tools used: `portfolio_lookup`, `market_data_search`

---

## Test Suite 4: Canonical Test Cases (Full Workflow)

### Test 4.1: ⭐ Client Quarterly Briefing
**Scenario:** Prepare comprehensive briefing for CLT-001 before quarterly meeting

```powershell
$message = @"
Prepare a quarterly briefing for Client CLT-001 (Rajesh Mehta).
Include:
1. Current portfolio performance and allocation
2. Market context and recent trends
3. Policy compliance check
4. Rebalancing recommendations
"@

$body = @{
    message = $message
    client_name = "Rajesh Mehta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "=== QUARTERLY BRIEFING ===" 
Write-Host $response.answer
Write-Host "`nTools Called: $($response.tools_used -join ', ')"
Write-Host "Sources: $($response.sources -join ', ')"
```

**✅ Expected Output Should Include:**
- Portfolio summary (total value, cost basis, return %)
- Sector allocation breakdown
- Top 3 holdings with performance metrics
- Market outlook with latest news/trends
- Policy compliance status
- Specific recommendations (e.g., "Reduce IT from 42% to 35%")

**Tools Should Use:**
- `portfolio_lookup` (get CLT-001 holdings)
- `market_data_search` (get current market data)
- `policy_retriever` (check policy limits)
- `tavily_search` (get latest market news)

**Success Criteria:**
- [ ] Response is 500+ words
- [ ] Includes 3+ specific numbers/metrics
- [ ] Cites policy document with page number
- [ ] Uses 3+ different tools
- [ ] Provides actionable recommendations

---

### Test 4.2: ⭐ Cross-Client Comparison & Policy Check
**Scenario:** Compare IT sector risk across clients and verify policy compliance

```powershell
$message = @"
I need to understand IT sector concentration risk across our clients.
Compare CLT-001 and CLT-002's IT sector exposure.
Check policy limits for each client's risk profile.
Which client has higher concentration risk?
"@

$body = @{
    message = $message
    client_name = "Portfolio Manager"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```

**✅ Expected Output Should Include:**
- CLT-001 IT exposure: X%
- CLT-002 IT exposure: Y%
- Risk profile of each client
- Policy limits for each profile
- Compliance verdict for each
- Recommendation on concentration risk

**Tools Should Use:**
- `portfolio_lookup` (both clients' holdings)
- `policy_retriever` (policy limits by profile)
- `calculate_metrics` (risk calculations)

**Success Criteria:**
- [ ] Clear comparison table or breakdown
- [ ] Specific percentages with calculations
- [ ] Policy citation with document name + page
- [ ] Clear compliance verdict
- [ ] Risk assessment conclusion

---

### Test 4.3: ⭐ Concentration Limit Verification
**Scenario:** Client wants to increase position; verify if it's allowed

```powershell
$message = @"
Client CLT-003 (Amit Choudhury, Aggressive profile) wants to increase 
their Adani position. Current allocation is 8%.

Check:
1. Current Adani allocation
2. Policy concentration limit for Aggressive profile
3. Is adding more to this position permissible?
4. If not, what's the maximum allowed?
"@

$body = @{
    message = $message
    client_name = "Amit Choudhury"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```

**✅ Expected Output Should Include:**
- Current Adani position: 8%
- Risk profile: Aggressive
- Policy limit: 12% (for Aggressive)
- Verdict: ✅ PERMISSIBLE (can increase to 12%)
- Safe increase amount: 4% additional allowed
- Reference: "[Investment_Policy_Framework.pdf | Page 7]"

**Tools Should Use:**
- `portfolio_lookup` (get current holdings)
- `policy_retriever` (get policy limits)
- `calculate_metrics` (compare to limits)

**Success Criteria:**
- [ ] Clear current allocation stated
- [ ] Policy limit cited with document reference
- [ ] Clear YES/NO verdict
- [ ] Math shown (current 8% + allowed 4% = 12% max)
- [ ] PDF citation includes page number

---

### Test 4.4: ⭐ Market Intelligence & Sector Outlook
**Scenario:** Client is heavily invested in Telecom/Auto; assess market outlook

```powershell
$message = @"
Client CLT-005 (Karan Malhotra) has significant exposure to:
- Telecom: 32% of portfolio
- Auto: 28% of portfolio

Please:
1. Show current holdings in these sectors
2. Search for latest market news (RBI updates, sector trends)
3. Analyze if this concentration is too high for a Moderate profile
4. Recommend portfolio actions based on market outlook
"@

$body = @{
    message = $message
    client_name = "Karan Malhotra"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```

**✅ Expected Output Should Include:**
- Current Telecom holdings: [list with %, prices]
- Current Auto holdings: [list with %, prices]
- Recent market news (last 48 hours):
  - RBI policy updates
  - Telecom sector catalysts (5G rollout, regulation)
  - Auto sector trends (EV adoption, demand)
- Risk assessment: Total Telecom + Auto = 60%
- Policy limit for Moderate profile: 8% per sector max → Concentration risk HIGH
- Recommendations:
  - Reduce Telecom to 18%
  - Reduce Auto to 15%
  - Reallocate to IT/FMCG for diversification

**Tools Should Use:**
- `portfolio_lookup` (get CLT-005 holdings)
- `tavily_search` (latest market news)
- `market_data_search` (sector YTD trends)
- `policy_retriever` (concentration policy)
- `calculate_metrics` (portfolio risk)

**Success Criteria:**
- [ ] News results show today's date / recent
- [ ] RBI/regulatory updates mentioned
- [ ] Sector YTD returns provided
- [ ] Specific allocation % for each holding
- [ ] Clear risk verdict (HIGH/MEDIUM/LOW concentration)
- [ ] 2+ actionable recommendations with target %s

---

## Test Suite 5: Error & Edge Cases

### Test 5.1: Non-Existent Client
```powershell
$body = @{
    message = "What's the portfolio for CLT-999?"
    client_name = "Unknown Client"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:** Graceful message stating "Client not found in database"

---

### Test 5.2: Vague Query
```powershell
$body = @{
    message = "Tell me about stocks"
    client_name = null
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:** Agent clarifies what client/portfolio they need info about

---

### Test 5.3: Policy Question Without Specific Client
```powershell
$body = @{
    message = "What's the maximum concentration limit for a stock?"
    client_name = null
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response.answer
```
**Expected:** General policy information (concentration limits vary by risk profile)

---

## Performance Metrics

Track these for each test:

| Metric | Expected |
|--------|----------|
| **Response Time** | < 5 seconds |
| **Tools Used** | 1-4 per query |
| **Answer Length** | 200-1000 words (typical) |
| **API Status Code** | 200 (success) |
| **Error Messages** | Clear and actionable |

---

## Passing Criteria

✅ **CHATBOT IS READY IF:**
- [x] All 5 endpoint tests pass (health, agentinfo, diagnostic, chat, briefing)
- [x] Test 4.1-4.4 return intelligent, multi-tool responses
- [x] Response times < 5 seconds
- [x] Policy citations include PDF name + page number
- [x] Database queries return correct data
- [x] Web search returns recent market news
- [x] All tools appear in response logs

❌ **CHATBOT NEEDS FIXES IF:**
- Response says "This is the FastAPI scaffold response..."
- No tools are being called
- Diagnostic shows ❌ for dependencies or API keys
- Database shows 0 clients/holdings
- Policy PDFs not found
- Web search returns no results

---

## Quick Test Script (Copy & Paste All)

```powershell
# Run all basic tests
Write-Host "=== MERIDIAN CHATBOT TEST SUITE ===" -ForegroundColor Cyan

# Test 1: Health
Write-Host "`n1. Health Check..."
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
    Write-Host "✅ Health: $($h.status)" -ForegroundColor Green
} catch { Write-Host "❌ Health check failed" -ForegroundColor Red }

# Test 2: Agent Info
Write-Host "`n2. Agent Info..."
try {
    $info = Invoke-RestMethod -Uri "http://127.0.0.1:8000/agentinfo" -Method Get
    Write-Host "✅ Agent Name: $($info.name)" -ForegroundColor Green
    Write-Host "   Tools: $($info.tools.Count) available" -ForegroundColor Green
} catch { Write-Host "❌ Agent info failed" -ForegroundColor Red }

# Test 3: Diagnostic
Write-Host "`n3. System Diagnostic..."
try {
    $diag = Invoke-RestMethod -Uri "http://127.0.0.1:8000/diagnostic" -Method Get
    Write-Host "✅ Status: $($diag.status)" -ForegroundColor Green
    Write-Host "   DB Clients: $($diag.database.clients_count)" -ForegroundColor Green
} catch { Write-Host "❌ Diagnostic failed" -ForegroundColor Red }

# Test 4: Chat
Write-Host "`n4. Chat Test..."
try {
    $body = @{ message = "Hello"; client_name = "Test" } | ConvertTo-Json
    $chat = Invoke-RestMethod -Uri "http://127.0.0.1:8000/main/chat" -Method Post -ContentType "application/json" -Body $body
    $isScaffold = $chat.answer -like "*FastAPI scaffold*"
    if ($isScaffold) {
        Write-Host "⚠️  Chat responding with scaffold (agent not initialized)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Chat responding with agent analysis" -ForegroundColor Green
    }
    Write-Host "   Tools: $($chat.tools_used.Count) called" -ForegroundColor Green
} catch { Write-Host "❌ Chat test failed" -ForegroundColor Red }

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Cyan
```

---

## Notes

- **DB-dependent tests** (Test 3, Test 4) require database to be populated with test data from Lab 6.4
- **Web search tests** require valid TAVILY_API_KEY in .env
- **Policy tests** require PDF files in `data/policy_document/`
- All tests should be run sequentially to preserve chat history context
