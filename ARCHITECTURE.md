# Meridian Wealth Financial Analyst Agent - Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Agent Architecture](#agent-architecture)
4. [Database Architecture](#database-architecture)
5. [API Architecture](#api-architecture)
6. [Data Flow](#data-flow)
7. [Tool Architecture](#tool-architecture)
8. [RAG Pipeline](#rag-pipeline)
9. [Integration Points](#integration-points)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Browser (Single Page App)                              │   │
│  │  ├─ index.html (Chat Interface)                         │   │
│  │  ├─ css/chat.css (Styling)                              │   │
│  │  └─ js/chat.js (Client Logic)                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────────────────────┐
│                     API Layer (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Endpoints:                                             │   │
│  │  ├─ POST /main/chat (Main)                              │   │
│  │  ├─ GET /health (Status)                                │   │
│  │  ├─ GET /agentinfo (Metadata)                           │   │
│  │  ├─ GET /diagnostic (System)                            │   │
│  │  └─ GET / (Static Files)                                │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────┐  ┌──────▼─────┐  ┌────▼──────┐
│   Agent    │  │ Database   │  │ External  │
│  Runtime   │  │   Layer    │  │  Services │
│  (ReAct)   │  │            │  │           │
└────────────┘  └────────────┘  └───────────┘
```

---

## Component Architecture

### Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  • Single HTML page (index.html)                            │
│  • CSS styling (chat.css)                                   │
│  • JavaScript client (chat.js)                              │
│  • Status indicators (Connection, Agent, Tools)             │
└──────────────────────┬────────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼────────────────────────────────────┐
│                  APPLICATION LAYER                         │
│  • FastAPI Framework                                       │
│  • CORS Middleware                                         │
│  • Request validation (Pydantic)                           │
│  • Response models                                         │
│  • Error handling                                          │
│  Location: app.py                                          │
└──────────────────────┬────────────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────────────┐
│                  AGENT LAYER                               │
│  • Agent Runtime (LangChain)                               │
│  • Tool Registry (5 financial tools)                       │
│  • State Management (LangGraph)                            │
│  • Prompt Engineering                                      │
│  • Tool Execution Loop                                     │
│  Location: source/agent_runtime.py                         │
└─────────────────────┬──────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐
    │   Tool   │  │   RAG   │  │  LLM    │
    │ Layer    │  │ Pipeline│  │ Service │
    │          │  │         │  │         │
    └──────────┘  └─────────┘  └─────────┘
         │            │            │
    ┌────▼──────────────────────────────────┐
    │      DATA PERSISTENCE LAYER           │
    │  • SQLite Database                    │
    │  • FAISS Vector Index                 │
    │  • Policy PDFs                        │
    │  • Market Data                        │
    └────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|-----------------|------------|
| **Frontend** | User interface, message display, client interaction | HTML5, CSS3, Vanilla JS |
| **FastAPI Server** | HTTP routing, request validation, response formatting | FastAPI, Uvicorn, Pydantic |
| **Agent Runtime** | Query planning, tool orchestration, response synthesis | LangChain, LangGraph |
| **Tools** | Specialized financial operations | Python decorators |
| **RAG Pipeline** | Document indexing, semantic search, retrieval | FAISS, OpenAI Embeddings |
| **Database** | Client data, holdings, market data persistence | SQLite3 |
| **External APIs** | LLM inference, web search | OpenAI, Tavily |

---

## Agent Architecture

### ReAct Pattern Implementation

The agent follows the **ReAct (Reason + Act)** pattern from Lab 6.4:

```
┌─────────────────────────────────────────┐
│  User Query Received                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  STEP 1: REASON (Thought)               │
│  ├─ Analyze question                    │
│  ├─ Identify relevant tools             │
│  ├─ Plan execution strategy             │
│  └─ Generate LLM thought                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  STEP 2: ACTION (Tool Selection)        │
│  ├─ Choose tool(s)                      │
│  ├─ Prepare arguments                   │
│  └─ Execute tool                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  STEP 3: OBSERVATION (Tool Result)      │
│  ├─ Collect tool output                 │
│  ├─ Process results                     │
│  └─ Update context                      │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────────────┐
        │ More steps needed?  │
        └──────┬────────────┬─┘
             Yes│           │No
               │            │
         ┌─────▼┐      ┌────▼──────┐
         │REASON│      │FINAL      │
         │again │      │ANSWER     │
         └─────┬┘      └────┬──────┘
               │            │
               └──────┬─────┘
                      │
         ┌────────────▼──────────────┐
         │  Return Formatted Response│
         │  ├─ Answer                │
         │  ├─ Tools Used            │
         │  └─ Sources               │
         └───────────────────────────┘
```

### Agent Execution Flow

```python
# Pseudocode representation

def run_financial_agent(question: str, client_name: str) -> dict:
    
    # Step 1: Initialize on first call
    if not _AGENT_READY:
        _init_rag_pipeline()
        _init_agent()
    
    # Step 2: Create agent input
    system_prompt = SYSTEM_PROMPT
    tools = [portfolio_lookup, market_data_search, policy_retriever, ...]
    
    # Step 3: Invoke agent with question
    agent = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
    agent_executor = create_agent(agent, tools, system_prompt)
    
    # Step 4: Run agent loop
    messages = agent_executor.invoke({"input": question})
    
    # Step 5: Extract results
    answer = extract_final_answer(messages)
    tools_used = extract_tool_names(messages)
    sources = extract_sources(messages)
    
    # Step 6: Return formatted response
    return {
        "answer": answer,
        "tools_used": tools_used,
        "sources": sources
    }
```

### Agent State Management

```python
# Global state managed in agent_runtime.py

_agent = None                    # LLM agent instance
_policy_retriever = None         # FAISS retriever
_AGENT_READY = False            # Initialization flag

# State transitions:
# 1. _AGENT_READY = False
#    ↓
# 2. _init_rag_pipeline() called → _policy_retriever initialized
#    ↓
# 3. _init_agent() called → _agent initialized, _AGENT_READY = True
#    ↓
# 4. Ready to process queries
```

---

## Database Architecture

### Data Model - Entity Relationship Diagram

```
┌──────────────────────┐
│     CLIENTS          │
├──────────────────────┤
│ client_id (PK)      │◄─┐
│ name                 │  │
│ risk_profile         │  │ 1:N
│ investment_horizon   │  │
│ aum_inr              │  │
│ relationship_mgr     │  │
│ phone                │  │
│ email                │  │
│ city                 │  │
│ join_date            │  │
│ last_review          │  │
└──────────────────────┘  │
                          │
                   ┌──────┴─────────┐
                   │                │
            ┌──────▼─────────┐      │
            │   HOLDINGS     │      │
            ├────────────────┤      │
            │ client_id (FK) ├──────┘
            │ ticker         │
            │ company_name   │
            │ shares         │
            │ avg_cost_basis │
            │ current_price  │
            │ sector         │
            │ purchase_date  │
            └────────┬───────┘
                     │
                     │ ticker
                     │
            ┌────────▼──────────┐
            │  MARKET_DATA      │
            ├───────────────────┤
            │ ticker (PK)       │
            │ company_name      │
            │ sector            │
            │ current_price     │
            │ ytd_return_pct    │
            │ pe_ratio          │
            │ analyst_rating    │
            │ high_52w          │
            │ low_52w           │
            │ market_cap_cr     │
            └───────────────────┘
```

### Database Schema

#### Table: clients
```sql
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,          -- CLT-001, CLT-002, etc.
    name TEXT,                           -- Client full name
    risk_profile TEXT,                   -- Conservative|Moderate|Moderate-Aggressive|Aggressive
    investment_horizon TEXT,             -- Short|Medium|Long
    aum_inr REAL,                        -- Assets under management (₹)
    relationship_mgr TEXT,               -- Manager name
    phone TEXT,                          -- Contact number
    email TEXT,                          -- Email address
    city TEXT,                           -- City of residence
    join_date TEXT,                      -- YYYY-MM-DD
    last_review TEXT                     -- YYYY-MM-DD
);

-- Indexes for query optimization
CREATE INDEX idx_clients_risk ON clients(risk_profile);
CREATE INDEX idx_clients_aum ON clients(aum_inr DESC);
```

#### Table: holdings
```sql
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT,                      -- Foreign key to clients
    ticker TEXT,                         -- Stock symbol (TCS, HDFC, etc.)
    company_name TEXT,                   -- Company full name
    shares REAL,                         -- Number of shares held
    avg_cost_basis REAL,                 -- Average purchase price
    current_price REAL,                  -- Current market price
    sector TEXT,                         -- IT|Finance|Pharma|etc.
    purchase_date TEXT,                  -- YYYY-MM-DD
    ytd_return_pct REAL,                 -- Year-to-date return %
    pe_ratio REAL,                       -- Price-to-earnings ratio
    analyst_rating TEXT,                 -- Buy|Hold|Sell
    FOREIGN KEY(client_id) REFERENCES clients(client_id)
);

-- Indexes for query optimization
CREATE INDEX idx_holdings_client ON holdings(client_id);
CREATE INDEX idx_holdings_ticker ON holdings(ticker);
CREATE INDEX idx_holdings_sector ON holdings(sector);
```

#### Table: market_data
```sql
CREATE TABLE market_data (
    ticker TEXT PRIMARY KEY,             -- Stock symbol
    company_name TEXT,                   -- Company name
    sector TEXT,                         -- Industry sector
    current_price REAL,                  -- Latest trading price
    ytd_return_pct REAL,                 -- Year-to-date return %
    pe_ratio REAL,                       -- Price-to-earnings ratio
    analyst_rating TEXT,                 -- Buy|Hold|Sell
    high_52w REAL,                       -- 52-week high price
    low_52w REAL,                        -- 52-week low price
    market_cap_cr REAL                   -- Market cap in crores (₹)
);

-- Index for sector searches
CREATE INDEX idx_market_sector ON market_data(sector);
```

### Database File Location
```
data/vector_db/meridian_wealth.db    ← SINGLE SOURCE OF TRUTH
```

### Query Patterns

**Portfolio Lookup:**
```sql
SELECT * FROM clients WHERE client_id = ?;
SELECT h.*, m.ytd_return_pct, m.pe_ratio, m.analyst_rating 
FROM holdings h
LEFT JOIN market_data m ON h.ticker = m.ticker
WHERE h.client_id = ?
ORDER BY (h.shares * h.current_price) DESC;
```

**Market Data Search:**
```sql
SELECT * FROM market_data 
WHERE ticker = ? 
OR UPPER(sector) LIKE ? 
OR UPPER(company_name) LIKE ?;
```

---

## API Architecture

### Endpoint Design

#### Request/Response Models

```python
# Request Models (Pydantic)
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    client_name: str | None = None

class MainChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    client_name: str | None = None

# Response Model
class AskResponse(BaseModel):
    answer: str                          # LLM response
    tools_used: list[str]               # Tool names invoked
    sources: list[str]                  # Data sources
```

### Endpoint Specifications

#### POST /main/chat
- **Purpose**: Main chat interface endpoint
- **Input**: `MainChatRequest` (message, client_name)
- **Output**: `AskResponse` (answer, tools_used, sources)
- **Processing**:
  1. Validate input
  2. Get agent via lazy initialization
  3. Execute agent with message
  4. Extract metadata (tools, sources)
  5. Return formatted response
- **Error Handling**: 500 HTTPException on failure

```json
// Example Request
{
  "message": "Show portfolio for CLT-001",
  "client_name": "Rajesh"
}

// Example Response
{
  "answer": "CLT-001 portfolio summary...",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": ["SQLite: data/vector_db/meridian_wealth.db", "Policy PDFs: data/policy_document/"]
}
```

#### GET /health
- **Purpose**: Health check endpoint
- **Output**: `{"status": "ok"}`
- **Use Case**: Monitoring, load balancer checks

#### GET /agentinfo
- **Purpose**: Agent metadata and capabilities
- **Output**: Agent name, version, available tools
- **Use Case**: Client discovery, capabilities listing

#### GET /diagnostic
- **Purpose**: Full system diagnostics
- **Output**: API keys status, dependencies, database, PDFs, recommendations
- **Use Case**: Troubleshooting, deployment verification

### API Error Handling

```python
# HTTP Status Codes
200 OK                 # Successful request
400 Bad Request        # Invalid input (validation error)
500 Internal Server    # Agent error, API error
504 Gateway Timeout    # Agent takes too long

# Error Response Format
{
  "detail": "Error message describing what went wrong"
}
```

---

## Data Flow

### Request-Response Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  1. BROWSER                                                     │
│     User submits form with:                                     │
│     - Client Name: "CLT-001"                                    │
│     - Message: "Show portfolio for CLT-001"                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP POST
                       │ Content-Type: application/json
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. FASTAPI SERVER (app.py)                                      │
│     - Route: POST /main/chat                                     │
│     - Parse JSON payload                                         │
│     - Validate with Pydantic                                     │
│     - Call _get_agent()                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ agent(question=msg, client_name=name)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. AGENT INITIALIZATION (First call only)                       │
│     - Check if _AGENT_READY                                      │
│     - If False:                                                  │
│       ├─ Load policy PDFs from data/policy_document/             │
│       ├─ Split documents (RecursiveCharacterTextSplitter)       │
│       ├─ Generate embeddings (text-embedding-3-small)           │
│       ├─ Build FAISS index                                       │
│       ├─ Initialize ChatOpenAI LLM (gpt-4-turbo)                │
│       └─ Set _AGENT_READY = True                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ run_financial_agent(question, client_name)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. AGENT LOOP (ReAct Pattern)                                   │
│     Thought → Action → Observation → Thought... (repeat)         │
│                                                                  │
│  For "Show portfolio for CLT-001":                              │
│                                                                  │
│  Thought: "User wants portfolio info. I need portfolio_lookup"   │
│  ↓                                                               │
│  Action: portfolio_lookup(client_id="CLT-001")                   │
│  ↓                                                               │
│  Observation: Returns portfolio JSON with holdings              │
│  ├─ Client: Rajesh Mehta, Risk: Moderate-Aggressive            │
│  ├─ Holdings: [TCS, HDFC, INFY, ...]                            │
│  └─ Total Value: ₹2,500,000                                    │
│  ↓                                                               │
│  Thought: "Got portfolio. Should check policy compliance."       │
│  ↓                                                               │
│  Action: policy_retriever(query="concentration limits...")       │
│  ↓                                                               │
│  Observation: Returns policy excerpts with sources              │
│  ↓                                                               │
│  Thought: "Got all info needed. Can now provide final answer."   │
│  ↓                                                               │
│  Final Answer: "Portfolio for CLT-001 shows..."                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Extract: answer, tools_used, sources
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. RESPONSE FORMATTING (app.py)                                 │
│     - Extract final answer from LLM                              │
│     - Extract tool names from message history                    │
│     - Extract sources from tool results                          │
│     - Build AskResponse object                                   │
│     - Serialize to JSON                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP 200 OK
                       │ Content-Type: application/json
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. BROWSER                                                      │
│     - Receive JSON response                                      │
│     - Parse answer, tools, sources                               │
│     - Display answer in chat panel                               │
│     - Show tools used in metadata                                │
│     - Append message to chat history                             │
└──────────────────────────────────────────────────────────────────┘
```

### Example Data Flow: Portfolio Query

```
User Input:
"Show portfolio for CLT-001"

↓

Agent Analysis:
1. Identify task: Portfolio lookup + policy check
2. Select tools: portfolio_lookup, policy_retriever
3. Plan execution

↓

Tool Execution:
1. portfolio_lookup("CLT-001")
   ├─ Query: SELECT * FROM clients WHERE client_id = "CLT-001"
   ├─ Database: data/vector_db/meridian_wealth.db
   └─ Return: Client data + Holdings
   
2. policy_retriever("concentration limits Moderate-Aggressive")
   ├─ Embed query using text-embedding-3-small
   ├─ Search FAISS index (policy PDFs)
   └─ Return: Top-4 matching policy excerpts

↓

Response Synthesis:
- Combine results with LLM reasoning
- Format portfolio breakdown with percentages
- Include policy compliance notes
- Cite sources

↓

Final Response:
{
  "answer": "### Portfolio Summary for CLT-001...",
  "tools_used": ["portfolio_lookup", "policy_retriever"],
  "sources": [
    "SQLite: data/vector_db/meridian_wealth.db",
    "Policy PDFs: data/policy_document/"
  ]
}
```

---

## Tool Architecture

### Tool Execution Pattern

```python
@tool
def tool_name(param1: str, param2: str) -> str:
    """Tool description for LLM.
    
    Usage: Use this tool when [specific condition].
    Input: [parameter descriptions]
    Returns: [return value description]
    """
    # Execution logic
    result = perform_operation(param1, param2)
    return result
```

### Tool Registry

#### 1. portfolio_lookup
```
Purpose: Get client portfolio summary
Input: client_id (e.g., "CLT-001")
Output: JSON with:
  - Client info (name, risk_profile, AUM)
  - Holdings breakdown (ticker, shares, current value)
  - Sector allocation (percentages)
  - Total portfolio value
  - Overall return
Data Source: clients + holdings tables + market_data
Processing:
  1. Query clients table
  2. Query holdings for client_id
  3. Join with market_data for current prices
  4. Calculate metrics (allocation %, gains, etc.)
  5. Format JSON response
```

#### 2. market_data_search
```
Purpose: Search market data by ticker/sector/company
Input: query string (e.g., "IT sector" or "TCS")
Output: List of matching stocks with:
  - Ticker, Company, Sector
  - Current price, YTD return, P/E ratio
  - Analyst rating, 52-week high/low
Data Source: market_data table
Processing:
  1. Normalize query (uppercase, trim)
  2. Search ticker exact match first
  3. If no match, search sector/company LIKE
  4. Return results sorted by market cap
```

#### 3. calculate_metrics
```
Purpose: Financial calculations
Input: Mathematical expression (e.g., "100 * 1.15 / 1.12")
Output: Calculated value
Processing:
  1. Validate expression (no dangerous functions)
  2. Execute safe calculation
  3. Return result
Security: Restricted functions, timeout
```

#### 4. policy_retriever
```
Purpose: RAG search over policy documents
Input: query string (e.g., "concentration limits")
Output: Relevant policy excerpts with:
  - Matching text
  - Source document name
  - Page number
  - Relevance score
Data Source: FAISS index (policy PDFs)
Processing:
  1. Embed query using text-embedding-3-small
  2. Search FAISS index (top-4 results)
  3. Format with citations
  4. Return formatted excerpts
```

#### 5. web_search (Tavily)
```
Purpose: Live web search for market information
Input: query string (e.g., "banking sector outlook India")
Output: Search results with:
  - Title
  - URL
  - Summary
  - Source
External Service: Tavily API
Processing:
  1. Call TavilySearch API
  2. Parse results
  3. Format for LLM context
  4. Return top-3 results
```

### Tool Calling Flow

```python
# In agent loop:

# 1. Agent decides to use tool
thought = "I need to find portfolio data"
action_type = "tool"
tool_name = "portfolio_lookup"
tool_input = {"client_id": "CLT-001"}

# 2. Agent runtime invokes tool
result = portfolio_lookup(client_id="CLT-001")

# 3. Result added to context
observation = result  # JSON with portfolio

# 4. Agent continues reasoning
thought = "Got portfolio, now check policy"
action_type = "tool"
tool_name = "policy_retriever"
tool_input = {"query": "concentration limits"}

# 5. Continue loop until final answer
```

---

## RAG Pipeline

### RAG Architecture

```
┌─────────────────────────────────────────────────────────┐
│  INITIALIZATION (First Request)                         │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌────────▼──────────┐
│  Load PDFs     │          │  Text Splitting   │
│                │          │                   │
│ Source:        │          │ Chunking:         │
│ data/policy    │          │ size: 1000 chars  │
│ document/      │          │ overlap: 300      │
│ (5 files)      │          │                   │
└───────┬────────┘          └────────┬──────────┘
        │                            │
        └────────────┬───────────────┘
                     │
          ┌──────────▼──────────┐
          │ Embedding           │
          │                     │
          │ Model:              │
          │ text-embedding-3    │
          │ -small              │
          │                     │
          │ Dimensions: 1536    │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │ FAISS Indexing      │
          │                     │
          │ Index Type: IVF     │
          │ Stored in memory    │
          └──────────┬──────────┘
                     │
        ┌────────────▼────────────┐
        │  SEARCH (Runtime)       │
        │                         │
        │ 1. Embed query          │
        │ 2. Search FAISS         │
        │ 3. Return top-4 results │
        └─────────────────────────┘
```

### RAG Initialization

```python
def _init_rag_pipeline():
    """Initialize RAG pipeline with policy documents."""
    
    # Step 1: Load documents
    loaders = [PyPDFLoader(pdf_path) for pdf_path in POLICY_DIR.glob("*.pdf")]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())
    
    # Step 2: Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300
    )
    chunks = splitter.split_documents(docs)
    
    # Step 3: Generate embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Step 4: Build FAISS index
    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    
    # Step 5: Create retriever
    global _policy_retriever
    _policy_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    
    return _policy_retriever
```

### RAG Query Flow

```
User Query: "What are concentration limits?"

↓

Query Embedding:
- Input: "What are concentration limits?"
- Embed using text-embedding-3-small
- Output: 1536-dimensional vector

↓

Vector Search:
- Input: Query vector
- Search FAISS index
- Return top-4 closest chunks
- Similarity scores: [0.92, 0.88, 0.85, 0.82]

↓

Chunk Retrieval:
1. Chunk 1: "Concentration limits for Moderate-Aggressive profile...
   Source: Asset_Allocation_Policy.pdf, Page 7"
   
2. Chunk 2: "Maximum position size per holding: 15%..."
   Source: Risk_Management_Guidelines.pdf, Page 18"
   
3. Chunk 3: "Sector diversification requirements..."
   Source: Concentration_Limits_Policy.pdf, Page 3"
   
4. Chunk 4: "Review concentration quarterly..."
   Source: Risk_Management_Guidelines.pdf, Page 20"

↓

Format for LLM:
Results in context with source citations

↓

LLM Synthesis:
Generate answer using policy excerpts as context
Include citations: "According to Asset_Allocation_Policy.pdf..."
```

---

## Integration Points

### External API Integrations

#### OpenAI API
```
Service: GPT-4 Turbo (LLM)
Endpoint: api.openai.com/v1/chat/completions
Authentication: OPENAI_API_KEY
Usage:
  - Main agent reasoning
  - Embedding generation (text-embedding-3-small)
Cost: Pay per token (input + output)
```

#### Tavily Search API
```
Service: Web search for market information
Endpoint: api.tavily.com/search
Authentication: TAVILY_API_KEY
Usage:
  - Real-time market news
  - Banking sector outlook
  - Latest financial information
Configuration:
  - Max results: 3
  - Topic: "news"
Cost: Per search API call
```

### Database Interactions

```
SQLite Connection:
- File: data/vector_db/meridian_wealth.db
- Connection Pool: sqlite3 (single-threaded)
- Queries:
  - Read-only for portfolio/market data
  - Created by seed_db.py
  
Transaction Pattern:
1. Open connection
2. Execute query
3. Fetch results
4. Close connection
5. Return data
```

### File System

```
Policy Documents:
- Location: data/policy_document/
- Format: PDF files
- Usage: RAG pipeline initialization
- Files: 5 required PDFs

Database File:
- Location: data/vector_db/meridian_wealth.db
- Created by: seed_db.py
- Accessed by: agent_runtime.py

Frontend Assets:
- Location: frontend/ directory
- Served by: FastAPI StaticFiles
- Types: HTML, CSS, JS
```

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────┐
│  Developer Machine                  │
├─────────────────────────────────────┤
│ ├─ Python 3.10+ (.venv)             │
│ ├─ FastAPI / Uvicorn                │
│ ├─ LangChain + OpenAI SDK           │
│ ├─ SQLite local database            │
│ └─ FAISS index (in-memory)          │
│                                     │
│ Running:                            │
│ python -m uvicorn app:app           │
│   --host 127.0.0.1                  │
│   --port 8000                       │
│   --reload                          │
└──────────────┬──────────────────────┘
               │
         Browser on port 8000
```

### Production Deployment (Docker)

```
┌─────────────────────────────────────┐
│  Docker Container                   │
├─────────────────────────────────────┤
│ FROM python:3.11-slim               │
│                                     │
│ WORKDIR /app                        │
│ COPY requirements.txt .             │
│ RUN pip install -r requirements.txt │
│ COPY . .                            │
│                                     │
│ CMD ["gunicorn", "-w 4", ...]       │
│     "app:app",                      │
│     "--bind", "0.0.0.0:8000"]       │
└──────────────┬──────────────────────┘
               │
        Docker Registry
               │
        ┌──────▼─────────────────┐
        │  Container Orchestration│
        │  (Kubernetes/Docker     │
        │   Compose)             │
        └────────────────────────┘
```

### Environment Variables

```
Production Environment:
- OPENAI_API_KEY              # OpenAI API key
- TAVILY_API_KEY              # Tavily API key
- LOG_LEVEL                   # DEBUG|INFO|WARNING
- WORKER_COUNT                # Number of Gunicorn workers
- DATABASE_PATH               # Alternative DB location
- POLICY_DOCS_PATH            # Alternative policy dir
```

### Performance Considerations

```
Latency Profile:
- Server startup: 5-10s
- First agent init: 30-40s (RAG indexing)
- Query (no tools): 5-10s
- Query (1 tool): 15-30s
- Query (2+ tools): 30-60s
- Query (web search): 45-90s

Scaling Strategy:
- Horizontal: Multiple Gunicorn workers
- Caching: Query results (Redis optional)
- Database: Connection pooling
- FAISS: Load once, reuse across requests
```

---

## Security Architecture

### API Security
```
- CORS: Enabled for all origins (configurable)
- Input Validation: Pydantic models
- Output Encoding: JSON serialization
- Error Handling: No stack traces in production
```

### Data Security
```
- Database: SQLite (file-based, no password needed for local)
- Credentials: API keys in environment variables
- Secrets: Never logged or exposed
- HTTPS: Recommended in production
```

### Tool Execution Safety
```
- calculate_metrics: Expression validation, timeout
- web_search: API rate limits, result filtering
- portfolio_lookup: Client ID validation
- policy_retriever: Controlled PDF documents only
```

---

## Monitoring & Observability

### Logging Points
```
- Agent initialization: Key steps with timestamps
- Tool execution: Tool name, inputs, outputs
- API requests: Endpoint, status code, duration
- Errors: Full stack trace in development
- Performance: Query latency tracking
```

### Health Checks
```
/health                          # Basic connectivity
/diagnostic                      # Full system status
  - API keys loaded
  - Dependencies installed
  - Database accessible
  - Policy PDFs found
  - FAISS index status
```

---

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | HTML5, CSS3, JS | Latest | User Interface |
| **Backend** | FastAPI, Uvicorn | 0.104+, 0.24+ | API Framework |
| **Agent** | LangChain, LangGraph | 0.1+, 0.1+ | Agent Runtime |
| **LLM** | OpenAI GPT-4 Turbo | - | Language Model |
| **Embeddings** | OpenAI text-embedding-3-small | - | Vector Embeddings |
| **Vector DB** | FAISS | 1.7+ | Vector Search |
| **Database** | SQLite3 | 3.40+ | Data Persistence |
| **Search** | Tavily API | - | Web Search |
| **Validation** | Pydantic | 2.0+ | Input Validation |
| **Python** | 3.10+ | - | Runtime |

---

## Architecture Decisions & Rationale

### Single HTML Page vs Multi-page
**Decision**: Single HTML page (index.html)
**Rationale**: 
- Simpler state management
- Faster page transitions
- Reduces network requests
- Easier deployment

### FAISS vs Cloud Vector DB
**Decision**: FAISS (local, in-memory)
**Rationale**:
- No additional infrastructure
- Instant search performance
- Offline capability
- Lower operational cost

### SQLite vs PostgreSQL
**Decision**: SQLite
**Rationale**:
- Simple setup, no server required
- Suitable for read-heavy queries
- Easy deployment
- Can migrate to PostgreSQL later

### ReAct vs Chain vs Plan-Solve
**Decision**: ReAct pattern (Reason + Act)
**Rationale**:
- Transparent reasoning
- Better error recovery
- Explainable actions
- Alignment with Lab 6.4

---

## Future Extensibility

### Adding New Tools
```python
# In agent_runtime.py, add:

@tool
def new_tool(param: str) -> str:
    """New tool description for LLM."""
    # Implementation
    return result

# Then add to tools list in _init_agent()
tools = [...existing..., new_tool]
```

### Scaling Considerations
- Message queue for async processing
- Redis cache for frequently accessed data
- PostgreSQL for larger datasets
- Separate worker processes for heavy tools
- Monitoring & alerting infrastructure

---

**Last Updated**: June 2025
**Architecture Version**: 1.0.0
**Status**: Documented & Validated ✅
