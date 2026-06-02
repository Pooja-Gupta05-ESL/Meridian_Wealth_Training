# Meridian Wealth Financial Analyst - Implementation Guide

## Purpose
This guide helps developers understand how to work with, extend, and maintain the Financial Analyst Agent codebase.

## Table of Contents
1. [Code Organization](#code-organization)
2. [Design Patterns](#design-patterns)
3. [Adding New Tools](#adding-new-tools)
4. [Extending the Database](#extending-the-database)
5. [Customizing the Agent](#customizing-the-agent)
6. [Testing Guidelines](#testing-guidelines)
7. [Debugging](#debugging)
8. [Performance Optimization](#performance-optimization)

---

## Code Organization

### Directory Structure & Module Responsibilities

```
financial_analyst_app/
│
├── app.py
│   ├── Purpose: FastAPI entry point, HTTP routing
│   ├── Responsibilities:
│   │   ├─ Define API endpoints
│   │   ├─ Handle CORS middleware
│   │   ├─ Lazy-load agent on first request
│   │   ├─ Validate requests with Pydantic
│   │   ├─ Format responses
│   │   └─ Serve static frontend files
│   └─ Key Functions:
│       ├─ _get_agent() - Lazy initialization
│       ├─ main_chat() - POST /main/chat endpoint
│       ├─ health() - GET /health endpoint
│       ├─ diagnostic() - System diagnostics
│       └─ agent_info() - Agent metadata
│
├── source/agent_runtime.py
│   ├── Purpose: Core agent logic and tool definitions
│   ├── Responsibilities:
│   │   ├─ RAG pipeline initialization
│   │   ├─ Agent creation and execution
│   │   ├─ Tool implementation
│   │   ├─ Response formatting
│   │   └─ Error handling
│   └─ Key Functions:
│       ├─ _init_rag_pipeline() - Load policy PDFs, build FAISS index
│       ├─ _init_agent() - Create LLM and agent
│       ├─ run_financial_agent() - Main entry point
│       ├─ @tool portfolio_lookup() - Client portfolio query
│       ├─ @tool market_data_search() - Stock search
│       ├─ @tool policy_retriever() - RAG search
│       └─ @tool web_search() - Tavily integration
│
├── seed_db.py
│   ├── Purpose: Database initialization and seeding
│   ├── Creates: clients, holdings, market_data tables
│   └── Usage: python seed_db.py (run once)
│
├── run_tests.py
│   ├── Purpose: Execute test suite for Lab 6.4
│   ├── Tests: 5 comprehensive test cases
│   └── Usage: python run_tests.py
│
├── test_agent.py
│   ├── Purpose: Quick agent functionality test
│   └── Usage: python test_agent.py (30-90s)
│
└── source/
    ├── __init__.py
    ├── databasequery.py         # Optional: Database helpers
    ├── rag_pipeline.py          # Optional: RAG utilities
    └── schemas.py               # Pydantic models
```

---

## Design Patterns

### 1. Lazy Initialization Pattern

**Location**: `app.py`, `agent_runtime.py`

**Purpose**: Defer expensive initialization (RAG indexing, LLM setup) until first use.

**Implementation**:
```python
# Global state
_agent = None
_policy_retriever = None
_AGENT_READY = False

def _get_agent():
    """Lazy-load agent on first request."""
    global _agent, _AGENT_READY
    if _agent is None and not _AGENT_READY:
        _init_rag_pipeline()
        _init_agent()
    return _agent

# Usage in endpoint
agent = _get_agent()
result = agent(question=message)
```

**Benefits**:
- Faster server startup
- Only initialize if used
- Error handling before first request
- Testable initialization

---

### 2. Tool Decorator Pattern

**Location**: `source/agent_runtime.py`

**Purpose**: Define tools that LLM can invoke with structured I/O.

**Implementation**:
```python
from langchain_core.tools import tool

@tool
def portfolio_lookup(client_id: str) -> str:
    """Look up a client's portfolio from the database.
    
    Args:
        client_id: Client identifier (e.g., 'CLT-001')
    
    Returns:
        JSON formatted portfolio information
    """
    # Validation
    if not client_id:
        return "Error: client_id required"
    
    # Execute
    portfolio = _get_client_portfolio(client_id.upper())
    if not portfolio:
        available = [r["client_id"] for r in _query_db("SELECT client_id FROM clients")]
        return f"Client {client_id} not found. Available: {', '.join(available)}"
    
    # Format response
    return json.dumps(format_portfolio(portfolio))
```

**Tool Requirements**:
1. Decorated with `@tool`
2. Type hints on parameters
3. Clear docstring with description
4. Input validation
5. Error handling
6. Structured output

---

### 3. Singleton RAG Pipeline Pattern

**Location**: `source/agent_runtime.py`

**Purpose**: Initialize RAG pipeline once and reuse across requests.

**Implementation**:
```python
# Module-level state
_policy_retriever = None

def _init_rag_pipeline():
    """Initialize once per server lifetime."""
    global _policy_retriever
    
    # Load documents
    docs = load_policy_documents()
    
    # Split and embed
    chunks = split_documents(docs)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Build index
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Store globally
    _policy_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    return _policy_retriever

def policy_retriever(query: str) -> str:
    """Use singleton retriever."""
    if _policy_retriever is None:
        return "RAG pipeline not initialized"
    
    docs = _policy_retriever.invoke(query)
    return format_results(docs)
```

**Benefits**:
- Minimal memory overhead
- Fast searches after init
- No redundant indexing
- Consistent across requests

---

### 4. ReAct Agent Loop Pattern

**Location**: `source/agent_runtime.py`

**Purpose**: Implement Reason + Act + Observe cycle.

**Flow**:
```
User Query
    ↓
Agent THINKS (reasoning step)
    ├─ Analyze question
    ├─ Identify tools needed
    └─ Plan approach
    ↓
Agent ACTS (tool selection)
    ├─ Choose tool
    ├─ Prepare inputs
    └─ Execute tool
    ↓
Agent OBSERVES (results)
    ├─ Receive tool output
    ├─ Parse results
    └─ Update context
    ↓
    ├─ More steps needed? → Back to THINK
    └─ Final answer ready? → RESPOND
    ↓
Format & Return Response
```

**Benefits**:
- Transparent reasoning
- Explainable decisions
- Better error recovery
- Debugging visibility

---

### 5. Database Query Wrapper Pattern

**Location**: `source/agent_runtime.py`

**Purpose**: Centralized database access with error handling.

**Implementation**:
```python
def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    """Execute SQL query with error handling."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

# Usage
clients = _query_db("SELECT * FROM clients WHERE client_id = ?", ("CLT-001",))
```

**Benefits**:
- Consistent error handling
- Connection lifecycle management
- Type-safe results
- Audit trail

---

## Adding New Tools

### Step 1: Define Tool Function

```python
@tool
def new_financial_analysis(param: str) -> str:
    """Detailed description of what this tool does.
    
    When to use: Specific use cases
    Input: Parameter descriptions
    Output: Expected return format
    
    Args:
        param: Parameter description
    
    Returns:
        str: Formatted analysis result
    """
    # Input validation
    if not param:
        return "Error: param is required"
    
    # Data retrieval
    data = fetch_data(param)
    if not data:
        return f"No data found for {param}"
    
    # Analysis
    result = perform_analysis(data)
    
    # Format output
    return format_result(result)
```

### Step 2: Register Tool with Agent

```python
def _init_agent():
    """Agent initialization with tools."""
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
    
    # Define tools list
    tools = [
        portfolio_lookup,
        market_data_search,
        calculate_metrics,
        policy_retriever,
        web_search,
        new_financial_analysis  # ← Add new tool here
    ]
    
    # Create agent
    system_prompt = SYSTEM_PROMPT
    _agent = create_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    
    _AGENT_READY = True
```

### Step 3: Test Tool in Isolation

```python
# In test_agent.py or interactive shell
from source.agent_runtime import new_financial_analysis

# Test direct call
result = new_financial_analysis("test input")
print(result)

# Test with agent
response = run_financial_agent(
    question="Use new tool with test input",
    client_name="Test"
)
print(response)
```

### Step 4: Add Test Cases

```python
# In run_tests.py
tests = [
    # ... existing tests ...
    {
        "name": "T6: New Financial Analysis",
        "query": "Can you provide new financial analysis for CLT-001?"
    }
]
```

---

## Extending the Database

### Adding New Table

```python
# In seed_db.py or migration script
def create_new_table():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        field1 TEXT,
        field2 REAL,
        field3 TEXT,
        created_at TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(client_id)
    )
    """)
    
    # Create indexes for query optimization
    cursor.execute("CREATE INDEX idx_new_table_client ON new_table(client_id)")
    cursor.execute("CREATE INDEX idx_new_table_field1 ON new_table(field1)")
    
    conn.commit()
```

### Adding New Column

```python
# Migration to existing table
cursor.execute("ALTER TABLE clients ADD COLUMN new_field TEXT DEFAULT 'default_value'")
conn.commit()
```

### Adding Query Helper

```python
# In agent_runtime.py
def _query_new_data(query_param: str) -> list[dict]:
    """Helper function for querying new table."""
    sql = """
    SELECT * FROM new_table 
    WHERE field1 = ? 
    ORDER BY created_at DESC
    """
    return _query_db(sql, (query_param,))
```

### Creating New Tool for New Data

```python
@tool
def analyze_new_data(client_id: str) -> str:
    """Analyze new data for a client.
    
    Args:
        client_id: Client ID to analyze
    
    Returns:
        Analysis results
    """
    data = _query_new_data(client_id)
    if not data:
        return f"No data found for {client_id}"
    
    analysis = perform_analysis(data)
    return json.dumps(analysis)
```

---

## Customizing the Agent

### Modify System Prompt

```python
# In agent_runtime.py, around line 370
SYSTEM_PROMPT = """
You are an expert financial analyst assistant for Meridian Wealth Management.

Your responsibilities:
1. Analyze client portfolios for compliance and optimization
2. Provide policy-compliant recommendations
3. Conduct market analysis
4. Identify risks and opportunities

Guidelines:
- Always cite policy documents when applicable
- Provide specific, actionable recommendations
- Acknowledge portfolio constraints
- Reference current market data

Tools available:
- portfolio_lookup: Client holdings and allocation
- market_data_search: Stock research
- policy_retriever: Company policies
- web_search: Market news
- calculate_metrics: Financial calculations

Always:
- Verify client ID exists before proceeding
- Check policy compliance
- Consider risk profile
- Provide supporting data

Output format:
- Use markdown for formatting
- Include tables for data
- Cite sources
- Provide disclaimer if needed
"""
```

### Adjust LLM Parameters

```python
# In _init_agent()
llm = ChatOpenAI(
    model="gpt-4-turbo",           # Model choice
    temperature=0.7,                # Creativity (0-1)
    max_tokens=4096,                # Output length
    request_timeout=300,            # Timeout (seconds)
    top_p=0.95,                     # Top-p sampling
    frequency_penalty=0.0,          # Repetition penalty
    presence_penalty=0.0            # Diversity penalty
)
```

**Parameter Tuning**:
| Parameter | Range | Effect |
|-----------|-------|--------|
| temperature | 0-1 | Lower = more consistent, Higher = more creative |
| max_tokens | 1-4096 | Maximum response length |
| top_p | 0-1 | Nucleus sampling (diversity) |
| frequency_penalty | 0-2 | Reduces repetition |
| presence_penalty | 0-2 | Encourages new topics |

### Change Retriever Settings

```python
# In _init_rag_pipeline()
_policy_retriever = vectorstore.as_retriever(
    search_type="similarity",      # or "mmr" (maximal marginal relevance)
    search_kwargs={
        "k": 4,                    # Number of results
        "score_threshold": 0.5     # Minimum similarity
    }
)
```

---

## Testing Guidelines

### Unit Tests

```python
# tests/test_tools.py
import pytest
from source.agent_runtime import portfolio_lookup, market_data_search

def test_portfolio_lookup_valid_client():
    """Test portfolio lookup with valid client ID."""
    result = portfolio_lookup("CLT-001")
    assert "Rajesh Mehta" in result or "CLT-001" in result
    assert isinstance(result, str)

def test_portfolio_lookup_invalid_client():
    """Test portfolio lookup with invalid client ID."""
    result = portfolio_lookup("INVALID")
    assert "not found" in result.lower() or "error" in result.lower()

def test_market_data_search():
    """Test market data search."""
    result = market_data_search("IT")
    assert len(result) > 0 or "not found" in result.lower()
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_portfolio_query():
    """Test complete portfolio lookup flow."""
    response = run_financial_agent(
        question="Show portfolio for CLT-001",
        client_name="Test"
    )
    
    assert response["answer"]
    assert "portfolio_lookup" in response["tools_used"]
    assert len(response["sources"]) > 0

def test_policy_compliance_check():
    """Test policy compliance analysis."""
    response = run_financial_agent(
        question="Check policy compliance for CLT-001",
        client_name="Test"
    )
    
    assert "policy_retriever" in response["tools_used"]
    assert response["answer"]
```

### Running Tests

```bash
# Run single test
pytest tests/test_tools.py::test_portfolio_lookup_valid_client

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=source
```

---

## Debugging

### Enable Debug Logging

```python
# In app.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In endpoints
@app.post("/main/chat")
async def main_chat(payload: MainChatRequest):
    logger.debug(f"Received query: {payload.message}")
    logger.debug(f"Client name: {payload.client_name}")
    
    try:
        agent = _get_agent()
        result = agent(question=payload.message, client_name=payload.client_name)
        logger.debug(f"Agent result: {result}")
        return AskResponse(**result)
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        raise
```

### Add Logging to Agent Runtime

```python
# In agent_runtime.py
import logging
logger = logging.getLogger(__name__)

def _init_agent():
    logger.info("Starting agent initialization...")
    
    try:
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
        logger.debug("LLM created successfully")
        
        tools = [portfolio_lookup, market_data_search, ...]
        logger.debug(f"Registered {len(tools)} tools")
        
        _agent = create_agent(llm=llm, tools=tools, system_prompt=SYSTEM_PROMPT)
        logger.info("Agent initialized successfully")
        
        return _agent
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}", exc_info=True)
        raise
```

### Interactive Debugging

```python
# In Python shell or Jupyter
from source.agent_runtime import run_financial_agent

# Test with verbose output
response = run_financial_agent(
    question="Show portfolio for CLT-001",
    client_name="Debug Test"
)

print("Answer:", response["answer"][:200])
print("Tools:", response["tools_used"])
print("Sources:", response["sources"])

# Test specific tool
from source.agent_runtime import portfolio_lookup
result = portfolio_lookup("CLT-001")
print(result)
```

### Diagnostic Endpoint

```bash
# Check system status
curl http://127.0.0.1:8000/diagnostic | jq .

# Check specific components
curl http://127.0.0.1:8000/diagnostic | jq '.database'
curl http://127.0.0.1:8000/diagnostic | jq '.api_keys'
```

---

## Performance Optimization

### 1. Database Optimization

```python
# Add indexes for frequently queried fields
cursor.execute("CREATE INDEX idx_holdings_sector ON holdings(sector)")
cursor.execute("CREATE INDEX idx_market_data_sector ON market_data(sector)")

# Use query pagination for large results
def _query_db_paginated(sql: str, params: tuple, limit: int, offset: int):
    paginated_sql = f"{sql} LIMIT ? OFFSET ?"
    return _query_db(paginated_sql, params + (limit, offset))
```

### 2. RAG Pipeline Optimization

```python
# Use MMR (Maximal Marginal Relevance) for diversity
_policy_retriever = vectorstore.as_retriever(
    search_type="mmr",  # ← Better diversity than similarity
    search_kwargs={
        "k": 4,
        "fetch_k": 20,  # Fetch more, then select best
        "lambda_mult": 0.5  # Balance relevance vs diversity
    }
)
```

### 3. LLM Caching

```python
# Cache policy retriever results
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_policy_search(query: str) -> str:
    """Cache policy search results."""
    return policy_retriever(query)

# Use in agent
result = cached_policy_search("concentration limits")
```

### 4. Connection Pooling

```python
# For production with PostgreSQL
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:password@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 5. Async Processing

```python
# For long-running queries in production
from fastapi import BackgroundTasks

@app.post("/async/chat")
async def async_chat(payload: MainChatRequest, background_tasks: BackgroundTasks):
    """Async chat processing."""
    
    task_id = str(uuid.uuid4())
    
    def process_chat():
        result = run_financial_agent(
            question=payload.message,
            client_name=payload.client_name
        )
        # Store result in cache
        cache[task_id] = result
    
    background_tasks.add_task(process_chat)
    
    return {"task_id": task_id, "status": "processing"}

@app.get("/async/result/{task_id}")
def get_result(task_id: str):
    """Retrieve async result."""
    if task_id in cache:
        return cache[task_id]
    return {"status": "processing"}
```

---

## Version Control & CI/CD

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-tool

# Make changes
# ... edit files ...

# Run tests
pytest tests/

# Commit
git add .
git commit -m "feat: add new financial analysis tool"

# Push
git push origin feature/new-tool

# Create pull request
# ... on GitHub ...
```

### Pre-commit Hooks

```python
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

---

## Code Style & Standards

### Python Style Guide

Follow PEP 8:
```python
# Good
def calculate_portfolio_value(client_id: str, date: str) -> float:
    """Calculate portfolio value for a client on a specific date."""
    portfolio = _get_client_portfolio(client_id)
    if not portfolio:
        return 0.0
    
    total = sum(h["shares"] * h["current_price"] for h in portfolio["holdings"])
    return total

# Bad
def calc_pval(cid,d):
    p=_get_client_portfolio(cid)
    if not p: return 0
    return sum(h['s']*h['cp'] for h in p['h'])
```

### Documentation Standards

```python
def tool_function(param1: str, param2: int) -> dict:
    """Short one-line description.
    
    Longer description explaining what this function does,
    when to use it, and any important considerations.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary with keys:
            - "result": The main result
            - "details": Supporting information
    
    Raises:
        ValueError: If param1 is empty
        KeyError: If data not found
    
    Example:
        >>> result = tool_function("test", 42)
        >>> print(result["result"])
    """
    pass
```

---

## Troubleshooting Common Issues

### Agent Initialization Takes Too Long
- **Cause**: Large policy PDF files
- **Solution**: Split PDFs or use incremental loading
- **Optimization**: Cache FAISS index to disk

### Memory Usage High
- **Cause**: Large embeddings or FAISS index
- **Solution**: Reduce chunk size, use fewer documents
- **Optimization**: Use Memory-mapped storage

### Queries Timing Out
- **Cause**: Complex tool chains, external API delays
- **Solution**: Implement query timeout, simplify queries
- **Optimization**: Use async/background tasks

### Database Locks
- **Cause**: Concurrent writes
- **Solution**: Use connection pooling, WAL mode
- **Optimization**: Use PostgreSQL for production

---

**Last Updated**: June 2025
**Status**: Documentation Complete ✅
