# Meridian Wealth Financial Analyst Agent - API Documentation

## Base URL
```
http://127.0.0.1:8000
```

## Table of Contents
1. [Authentication](#authentication)
2. [Chat Endpoints](#chat-endpoints)
3. [Diagnostic Endpoints](#diagnostic-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## Authentication

**Current Status**: No authentication required (localhost development)

For production deployment, implement:
- API Key authentication
- JWT tokens
- OAuth 2.0

---

## Chat Endpoints

### POST /main/chat
Main endpoint for chatbot queries.

#### Request

**URL**: `POST http://127.0.0.1:8000/main/chat`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "message": "Show portfolio for CLT-001",
  "client_name": "Optional client name"
}
```

**Parameters**:
| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|------------|
| `message` | string | Yes | User query | Min: 3 chars, Max: 4000 chars |
| `client_name` | string | No | Client reference | Max: 200 chars |

#### Response

**Status Code**: 200 OK

**Body**:
```json
{
  "answer": "### Portfolio Summary for CLT-001\n\nClient: Rajesh Mehta...",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": [
    "SQLite: data/vector_db/meridian_wealth.db",
    "Policy PDFs: data/policy_document/"
  ]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Full LLM response with portfolio analysis, policy compliance, recommendations |
| `tools_used` | array[string] | Names of tools invoked during reasoning |
| `sources` | array[string] | Data sources accessed |

#### Example Request

```bash
curl -X POST http://127.0.0.1:8000/main/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show portfolio for CLT-001 with holdings breakdown",
    "client_name": "Rajesh"
  }'
```

#### Example Response

```json
{
  "answer": "### Portfolio Summary for CLT-001\n\n**Client**: Rajesh Mehta\n**Risk Profile**: Moderate-Aggressive\n**AUM**: ₹2,500,000\n\n#### Holdings Breakdown\n\n| Ticker | Company | Shares | Current Value | Portfolio % | YTD Return |\n|--------|---------|--------|---------------|-------------|------------|\n| TCS | Tata Consultancy | 50 | ₹950,000 | 38.0% | 12.5% |\n| HDFC | HDFC Bank | 100 | ₹750,000 | 30.0% | 8.2% |\n| INFY | Infosys | 75 | ₹525,000 | 21.0% | 15.3% |\n| RELIANCE | Reliance Industries | 30 | ₹275,000 | 11.0% | 5.1% |\n\n#### Sector Allocation\n- IT: 59%\n- Finance: 30%\n- Energy: 11%\n\n#### Portfolio Metrics\n- Total Current Value: ₹2,500,000\n- Total Cost Basis: ₹2,250,000\n- Unrealized Gain: ₹250,000 (+11.1%)\n- Overall YTD Return: +10.2%\n\n#### Policy Compliance\nAs per Asset_Allocation_Policy.pdf (Page 7), your Moderate-Aggressive profile allows:\n- Equities: 70% (recommended range 63-77%) ✅ Your allocation: 100% - EXCEEDS by 30%\n- Fixed Income: 20% (recommended 15-25%) ❌ Your allocation: 0%\n- Cash: 10% (recommended 5-10%) ❌ Your allocation: 0%\n\n**Recommendation**: Rebalance to comply with policy guidelines. Consider allocating 20% to fixed income and reducing equity exposure.",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": [
    "SQLite: data/vector_db/meridian_wealth.db",
    "Policy PDFs: data/policy_document/"
  ]
}
```

#### Error Response

**Status Code**: 400 Bad Request (Validation Error)
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.string.min_length"
    }
  ]
}
```

**Status Code**: 500 Internal Server Error
```json
{
  "detail": "Agent execution failed: [error details]"
}
```

---

### POST /api/ask
Alternative chat endpoint with identical functionality.

#### Request

**URL**: `POST http://127.0.0.1:8000/api/ask`

**Body**:
```json
{
  "question": "What's the latest market outlook?",
  "client_name": "Optional"
}
```

#### Response

Same as `/main/chat` endpoint.

---

## Diagnostic Endpoints

### GET /health
Health check endpoint for monitoring.

#### Request

**URL**: `GET http://127.0.0.1:8000/health`

#### Response

**Status Code**: 200 OK

```json
{
  "status": "ok"
}
```

#### Use Cases
- Load balancer health checks
- Kubernetes liveness probes
- Monitoring systems
- Uptime tracking

---

### GET /agentinfo
Get agent metadata and capabilities.

#### Request

**URL**: `GET http://127.0.0.1:8000/agentinfo`

#### Response

**Status Code**: 200 OK

```json
{
  "name": "Financial Analyst Agent",
  "version": "1.0.0",
  "status": "ready",
  "endpoints": {
    "health": "/health",
    "chat": "/main/chat",
    "agentinfo": "/agentinfo"
  },
  "tools": [
    "portfolio_lookup",
    "policy_retriever",
    "tavily_search"
  ]
}
```

#### Use Cases
- Client discovery
- Capabilities listing
- Version verification
- Tool registry

---

### GET /diagnostic
Full system diagnostics for troubleshooting.

#### Request

**URL**: `GET http://127.0.0.1:8000/diagnostic`

#### Response

**Status Code**: 200 OK

```json
{
  "api_keys": {
    "openai": "✅ Set",
    "tavily": "✅ Set"
  },
  "dependencies": {
    "langchain": "✅ Installed",
    "langchain_openai": "✅ Installed",
    "langchain_community": "✅ Installed",
    "langchain_tavily": "✅ Installed",
    "langchain_core": "✅ Installed",
    "faiss": "✅ Installed"
  },
  "database": {
    "file": "✅ Found (32 KB)",
    "clients_count": 5,
    "holdings_count": 8,
    "market_data_count": 8
  },
  "policy_pdfs": {
    "directory": "✅ Found",
    "count": 5,
    "files": [
      "Asset_Allocation_Policy.pdf",
      "Risk_Management_Guidelines.pdf",
      "Concentration_Limits_Policy.pdf",
      "Liquidity_Management_Policy.pdf",
      "ESG_Investment_Policy.pdf"
    ]
  },
  "status": "✅ Ready",
  "recommendations": []
}
```

**Diagnostic Fields**:
| Field | Meaning | Values |
|-------|---------|--------|
| `api_keys` | Environment variables | ✅ Set / ❌ Missing |
| `dependencies` | Python packages | ✅ Installed / ❌ Missing |
| `database` | SQLite status | ✅ Found / ❌ Not found, row counts |
| `policy_pdfs` | PDF directory | ✅ Found / ⚠️ Empty |
| `status` | Overall system | ✅ Ready / ⚠️ Incomplete |
| `recommendations` | Action items | Array of strings |

#### Use Cases
- Deployment verification
- Troubleshooting startup issues
- Configuration validation
- Pre-flight checks

---

### GET /
Serves the frontend HTML page.

#### Request

**URL**: `GET http://127.0.0.1:8000/`

#### Response

**Status Code**: 200 OK

**Content-Type**: `text/html`

Returns `frontend/index.html` single-page application.

---

## Data Models

### MainChatRequest

```python
class MainChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="User query message"
    )
    client_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional client reference name"
    )
```

**Example**:
```json
{
  "message": "Show portfolio for CLT-001",
  "client_name": "Rajesh Mehta"
}
```

---

### AskResponse

```python
class AskResponse(BaseModel):
    answer: str
    tools_used: List[str]
    sources: List[str]
```

**Example**:
```json
{
  "answer": "Portfolio analysis for CLT-001...",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": [
    "SQLite: data/vector_db/meridian_wealth.db",
    "Policy PDFs: data/policy_document/"
  ]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Query processed successfully |
| 400 | Bad Request | Invalid query parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Agent execution failed |
| 504 | Gateway Timeout | Query took too long |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### 1. Validation Error (400)
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.string.min_length"
    }
  ]
}
```

**Solution**: Ensure message is at least 3 characters.

#### 2. Agent Initialization Error (500)
```json
{
  "detail": "Agent startup error. Unable to import source.agent_runtime. Details: OPENAI_API_KEY not found"
}
```

**Solution**: 
- Check `.env` file has `OPENAI_API_KEY`
- Verify dependencies installed: `pip install -r requirements.txt`

#### 3. Database Error (500)
```json
{
  "detail": "Client not found in database"
}
```

**Solution**:
- Ensure `seed_db.py` has been run
- Verify database at `data/vector_db/meridian_wealth.db`

#### 4. Timeout Error (504)
```json
{
  "detail": "Request timed out after 300 seconds"
}
```

**Solution**:
- Retry the query
- Check API key usage limits (OpenAI quota)
- Simplify the query

---

## Rate Limiting

**Current Status**: No rate limiting (development mode)

### Recommended Production Settings

```
- Requests per minute: 60 (per IP)
- Requests per day: 10,000 (per API key)
- Query timeout: 300 seconds
- Database connection pool: 5 connections
```

### OpenAI API Limits

Check your OpenAI account for:
- Tokens per minute (TPM)
- Requests per minute (RPM)
- Monthly quota

### Tavily API Limits

Check Tavily account for:
- Search requests per month
- API call rate limits

---

## Examples

### Example 1: Portfolio Lookup

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/main/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show portfolio for CLT-001 with holdings breakdown and risk assessment",
    "client_name": "Rajesh"
  }'
```

**Response**:
```json
{
  "answer": "### Portfolio for CLT-001 (Rajesh Mehta)\n\nRisk Profile: Moderate-Aggressive\nTotal AUM: ₹2,500,000\n\nHoldings:\n- TCS: 50 shares @ ₹19,000 = ₹950,000 (38%)\n- HDFC: 100 shares @ ₹7,500 = ₹750,000 (30%)\n- INFY: 75 shares @ ₹7,000 = ₹525,000 (21%)\n- RELIANCE: 30 shares @ ₹9,167 = ₹275,000 (11%)\n\nRisk Assessment: Portfolio is 100% equities, exceeding policy limits for Moderate-Aggressive profile (70% recommended).",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": ["SQLite: data/vector_db/meridian_wealth.db", "Policy PDFs: data/policy_document/"]
}
```

---

### Example 2: Policy Compliance Check

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/main/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the concentration limits for CLT-001 given his Moderate-Aggressive profile?",
    "client_name": "Policy Check"
  }'
```

**Response**:
```json
{
  "answer": "Based on Asset_Allocation_Policy.pdf and Risk_Management_Guidelines.pdf:\n\nFor Moderate-Aggressive Profile:\n- Maximum per holding: 15%\n- Maximum per sector: 40%\n- Minimum equity: 60%\n- Maximum equity: 80%\n\nCLT-001 Violations:\n- IT sector: 59% (EXCEEDS 40% limit)\n- TCS position: 38% (EXCEEDS 15% limit)\n\nRecommendation: Reduce TCS to ≤15% and diversify to other sectors.",
  "tools_used": ["policy_retriever", "portfolio_lookup"],
  "sources": ["Policy PDFs: data/policy_document/"]
}
```

---

### Example 3: Market Data Search

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/main/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare IT sector stocks currently in the portfolio"
  }'
```

**Response**:
```json
{
  "answer": "IT Sector Comparison:\n\n| Stock | Price | YTD Return | P/E | Rating |\n|-------|-------|------------|-----|--------|\n| TCS | ₹19,000 | 12.5% | 22.5 | Buy |\n| INFY | ₹7,000 | 15.3% | 18.2 | Buy |\n| WIPRO | ₹380 | 8.1% | 16.8 | Hold |\n\nBest Performer: INFY (+15.3%)\nHighest P/E: TCS (22.5x)\nAnalyst Consensus: All rated Buy/Hold",
  "tools_used": ["market_data_search", "portfolio_lookup"],
  "sources": ["SQLite: data/vector_db/meridian_wealth.db"]
}
```

---

### Example 4: Web Search Integration

**Request**:
```bash
curl -X POST http://127.0.0.1:8000/main/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the latest market outlook for banking sector in India?"
  }'
```

**Response**:
```json
{
  "answer": "Latest Banking Sector Outlook:\n\nRecent Market Developments:\n1. RBI maintains repo rate at 6.5%\n2. Banking stocks up 2.3% this week\n3. NPA ratios declining across sector\n4. Credit growth steady at 15% YoY\n\nKey Risks:\n- Interest rate uncertainty\n- Regulatory changes\n- Credit quality concerns\n\nOpportunity: HDFC and ICICI showing strong earnings momentum.",
  "tools_used": ["web_search", "market_data_search"],
  "sources": ["Web Search: Tavily API", "SQLite: data/vector_db/meridian_wealth.db"]
}
```

---

### Example 5: System Diagnostics

**Request**:
```bash
curl http://127.0.0.1:8000/diagnostic
```

**Response**:
```json
{
  "api_keys": {
    "openai": "✅ Set",
    "tavily": "✅ Set"
  },
  "dependencies": {
    "langchain": "✅ Installed",
    "langchain_openai": "✅ Installed",
    "langchain_community": "✅ Installed",
    "langchain_tavily": "✅ Installed",
    "langchain_core": "✅ Installed",
    "faiss": "✅ Installed"
  },
  "database": {
    "file": "✅ Found (32 KB)",
    "clients_count": 5,
    "holdings_count": 8,
    "market_data_count": 8
  },
  "policy_pdfs": {
    "directory": "✅ Found",
    "count": 5,
    "files": [
      "Asset_Allocation_Policy.pdf",
      "Risk_Management_Guidelines.pdf",
      "Concentration_Limits_Policy.pdf",
      "Liquidity_Management_Policy.pdf",
      "ESG_Investment_Policy.pdf"
    ]
  },
  "status": "✅ Ready",
  "recommendations": []
}
```

---

## Response Time Guidelines

| Query Type | Time | Notes |
|-----------|------|-------|
| Health check | <100ms | No processing |
| Portfolio lookup (no tools) | 2-5s | Agent initialization if first call |
| Single tool query | 20-30s | +30s for first LLM call |
| Multi-tool query | 40-60s | Sequential tool execution |
| Web search query | 60-90s | +20s for external API call |
| First request ever | +30s | RAG pipeline initialization |

---

## Best Practices

### 1. Query Formulation
- Be specific: "Show portfolio for CLT-001" ✅
- Avoid vague queries: "Show portfolio" ❌
- Include relevant context: "risk profile", "sector", "date"

### 2. Error Handling in Client
```javascript
async function callAPI(message) {
  try {
    const response = await fetch('/main/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, client_name: 'Client' })
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error.detail);
      return null;
    }
    
    return await response.json();
  } catch (err) {
    console.error('Network Error:', err);
    return null;
  }
}
```

### 3. Monitoring
- Check `/health` endpoint every 30 seconds
- Check `/diagnostic` on startup
- Log query times for performance tracking
- Monitor API key usage with OpenAI dashboard

### 4. Caching
- Cache portfolio lookups for same client_id
- Cache market_data searches
- Invalidate cache on policy updates

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | June 2025 | Initial release |

---

**Last Updated**: June 2025
**API Status**: Production Ready ✅
