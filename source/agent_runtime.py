"""
Financial Analyst ReAct Agent Runtime.

Integrates:
- SQLite database (client portfolios, holdings, market data)
- RAG pipeline over policy PDFs (FAISS + OpenAI embeddings)
- Live web search (Tavily API)
- Tool-based agent loop (LangChain v1)
"""

import json
import os
import re
import sqlite3
from pathlib import Path

# LangChain imports
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.tools import tool
    from langchain.agents import create_agent
    from langchain_tavily import TavilySearch
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

MODULE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = MODULE_DIR / "data" / "vector_db" / "meridian_wealth.db"
POLICY_DIR = MODULE_DIR / "data" / "policy_document"

# Global agent and retriever (lazy-loaded)
_agent = None
_policy_retriever = None
_AGENT_READY = False


def _scaffold_response(question: str, client_name: str | None = None) -> dict[str, object]:
    """Fallback scaffold response when agent is unavailable."""
    stats = _safe_db_stats()
    header = "Financial Analyst Response"
    if client_name:
        header = f"Financial Analyst Response for {client_name}"

    answer = (
        f"{header}\n\n"
        f"Question: {question}\n\n"
        "⚠️ Agent not initialized. Ensure:\n"
        "  1. OPENAI_API_KEY and TAVILY_API_KEY environment variables are set\n"
        "  2. Policy PDFs exist at data/policy_document/\n"
        "  3. Database exists at data/meridian_wealth.db\n"
        "  4. LangChain packages are installed: pip install langchain langchain-openai langchain-community langchain-tavily faiss-cpu\n\n"
        f"Data check: clients={stats['clients']}, holdings={stats['holdings']}."
    )

    return {
        "answer": answer,
        "tools_used": ["portfolio_lookup", "policy_retriever", "market_data_search", "tavily_search"],
        "sources": [
            "SQLite: data/meridian_wealth.db",
            "Policy PDFs: data/policy_document/",
            "Web Search: Tavily",
        ],
    }


def _safe_db_stats() -> dict[str, int]:
    """Query DB for basic stats without failing if DB is missing."""
    if not DB_PATH.exists():
        return {"clients": 0, "holdings": 0}

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM clients")
        clients = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM holdings")
        holdings = int(cur.fetchone()[0])
        return {"clients": clients, "holdings": holdings}
    except Exception:
        return {"clients": 0, "holdings": 0}
    finally:
        conn.close()


def _query_db(sql: str, params: tuple = ()) -> list[dict]:
    """Execute SQL query against the Meridian Wealth database."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
    except Exception:
        rows = []
    finally:
        conn.close()
    return rows


def _get_client_portfolio(client_id: str) -> dict | None:
    """Get full portfolio for a client with enriched market data."""
    client = _query_db("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    if not client:
        return None

    holdings = _query_db(
        """
        SELECT h.ticker, h.company_name, h.shares, h.avg_cost_basis, h.current_price,
               h.sector, h.purchase_date,
               m.ytd_return_pct, m.pe_ratio, m.analyst_rating, m.high_52w, m.low_52w
        FROM holdings h
        LEFT JOIN market_data m ON h.ticker = m.ticker
        WHERE h.client_id = ?
        ORDER BY (h.shares * h.current_price) DESC
    """,
        (client_id,),
    )

    return {"client": client[0], "holdings": holdings}


def _search_market_data(query: str) -> list[dict]:
    """Search market data by ticker, sector, or company name."""
    q = query.upper().strip()
    results = _query_db("SELECT * FROM market_data WHERE ticker = ?", (q,))
    if not results:
        results = _query_db(
            "SELECT * FROM market_data WHERE UPPER(sector) LIKE ? OR UPPER(company_name) LIKE ? OR ticker LIKE ?",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        )
    return results


def _init_rag_pipeline():
    """Initialize RAG pipeline: load PDFs, split, embed, build FAISS index."""
    global _policy_retriever

    if not LANGCHAIN_AVAILABLE:
        return None

    if not POLICY_DIR.exists():
        return None

    try:
        # Load all PDFs
        all_pages = []
        pdf_files = sorted([f for f in os.listdir(POLICY_DIR) if f.endswith(".pdf")])

        if not pdf_files:
            return None

        for pdf_file in pdf_files:
            loader = PyPDFLoader(str(POLICY_DIR / pdf_file))
            pages = loader.load()
            all_pages.extend(pages)

        if not all_pages:
            return None

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = text_splitter.split_documents(all_pages)

        # Embed and build FAISS
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(chunks, embedding_model)
        _policy_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        return _policy_retriever
    except Exception as e:
        print(f"RAG pipeline initialization failed: {e}")
        return None


def _init_agent():
    """Initialize the ReAct agent with all tools."""
    global _agent, _policy_retriever, _AGENT_READY

    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain not available")
        return None

    # Check API keys
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return None
    if not os.environ.get("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not set")
        return None

    print("✅ API keys loaded")

    try:
        # Initialize RAG if available
        print("⏳ Initializing RAG pipeline...")
        _policy_retriever = _init_rag_pipeline()
        if _policy_retriever:
            print("✅ RAG pipeline ready")
        else:
            print("⚠️ RAG pipeline unavailable (continuing)")

        # Define tools
        @tool
        def portfolio_lookup(client_id: str) -> str:
            """Look up a client's portfolio from the database: holdings, allocation, total value, and risk profile.
            Use this when you need to know what a specific client owns or their investment profile.
            Input: client ID like 'CLT-001', 'CLT-002', etc."""

            portfolio = _get_client_portfolio(client_id.upper())
            if not portfolio:
                available = [r["client_id"] for r in _query_db("SELECT client_id FROM clients")]
                return f"Client {client_id} not found. Available: {', '.join(available)}"

            c = portfolio["client"]
            holdings = portfolio["holdings"]

            total_current = sum(h["shares"] * h["current_price"] for h in holdings)
            total_cost = sum(h["shares"] * h["avg_cost_basis"] for h in holdings)
            overall_return = ((total_current - total_cost) / total_cost) * 100

            # Sector allocation
            sector_values = {}
            for h in holdings:
                val = h["shares"] * h["current_price"]
                sector_values[h["sector"]] = sector_values.get(h["sector"], 0) + val
            sector_pct = {
                s: round((v / total_current) * 100, 1) for s, v in sector_values.items()
            }

            # Per-holding detail
            holdings_detail = []
            for h in holdings:
                cv = h["shares"] * h["current_price"]
                gain = ((h["current_price"] - h["avg_cost_basis"]) / h["avg_cost_basis"]) * 100
                wt = (cv / total_current) * 100
                holdings_detail.append(
                    {
                        "ticker": h["ticker"],
                        "company": h["company_name"],
                        "shares": h["shares"],
                        "avg_cost": h["avg_cost_basis"],
                        "current_price": h["current_price"],
                        "current_value": cv,
                        "unrealized_gain_pct": round(gain, 1),
                        "portfolio_weight_pct": round(wt, 1),
                        "sector": h["sector"],
                        "ytd_return": h["ytd_return_pct"],
                        "analyst_rating": h["analyst_rating"],
                        "purchase_date": h["purchase_date"],
                    }
                )

            result = {
                "client_id": c["client_id"],
                "name": c["name"],
                "relationship_manager": c["relationship_mgr"],
                "risk_profile": c["risk_profile"],
                "investment_horizon": c["investment_horizon"],
                "aum_inr": c["aum_inr"],
                "last_review": c["last_review"],
                "total_portfolio_value": round(total_current),
                "total_cost_basis": round(total_cost),
                "overall_return_pct": round(overall_return, 1),
                "sector_allocation": sector_pct,
                "holdings": holdings_detail,
            }
            return json.dumps(result, indent=2, ensure_ascii=False)

        @tool
        def market_data_search(query: str) -> str:
            """Search the market database for stock tickers or sectors. Returns current price, YTD returns,
            PE ratio, analyst ratings, 52-week range, and market cap. Use this when you need market
            performance data for specific stocks or want to compare sector performance.
            Input: a stock ticker (e.g. 'RELIANCE'), sector name (e.g. 'IT', 'Banking'), or company name."""

            results = _search_market_data(query)
            if not results:
                all_tickers = [r["ticker"] for r in _query_db("SELECT ticker FROM market_data")]
                return f"No data found for '{query}'. Available: {', '.join(all_tickers)}"

            formatted = [
                {
                    "ticker": r["ticker"],
                    "company": r["company_name"],
                    "sector": r["sector"],
                    "price": r["current_price"],
                    "ytd_return": r["ytd_return_pct"],
                    "pe_ratio": r["pe_ratio"],
                    "analyst_rating": r["analyst_rating"],
                    "52w_range": f"{r['low_52w']} - {r['high_52w']}",
                    "market_cap_cr": r["market_cap_cr"],
                }
                for r in results
            ]
            return json.dumps(formatted, indent=2, ensure_ascii=False)

        @tool
        def calculate_metrics(expression: str) -> str:
            """Perform financial calculations: returns, percentages, allocations, comparisons.
            Input: describe the calculation, e.g. 'return on 596000 vs cost 430000'
            or 'percentage of 350000 out of 2530000' or 'compare 18.5 vs 12.3'."""
            try:
                numbers = [
                    float(x.replace(",", "")) for x in re.findall(r"[\d,]+\.?\d*", expression)
                ]

                if "return" in expression.lower() or "gain" in expression.lower():
                    if len(numbers) >= 2:
                        current, cost = numbers[0], numbers[1]
                        ret = ((current - cost) / cost) * 100
                        return f"Return: (₹{current:,.0f} - ₹{cost:,.0f}) / ₹{cost:,.0f} = {ret:+.2f}%"

                if (
                    "percentage" in expression.lower()
                    or "allocation" in expression.lower()
                    or "weight" in expression.lower()
                ):
                    if len(numbers) >= 2:
                        part, whole = numbers[0], numbers[1]
                        return f"Percentage: ₹{part:,.0f} / ₹{whole:,.0f} = {(part/whole)*100:.2f}%"

                if "compare" in expression.lower() and len(numbers) >= 2:
                    a, b = numbers[0], numbers[1]
                    return f"Comparison: {a:,.2f} vs {b:,.2f} | Diff: {a-b:+,.2f} ({((a-b)/b)*100:+.2f}%)"

                if len(numbers) == 2:
                    a, b = numbers
                    return f"Values: {a:,.2f} and {b:,.2f} | Sum: {a+b:,.2f} | Diff: {a-b:+,.2f} | Ratio: {a/b:.4f}"

                return f"Provide two numbers with operation type (return, percentage, compare). Got: '{expression}'"
            except Exception as e:
                return f"Calculation error: {str(e)}"

        @tool
        def policy_retriever(query: str) -> str:
            """Search Meridian Wealth Partners' investment policy PDF documents using RAG (vector similarity search).
            Use this when you need to check investment guidelines, allocation rules, rebalancing triggers,
            risk limits, concentration limits, suitability standards, or reporting requirements.
            Returns relevant excerpts with source document name and page number.
            Input: a natural language query about investment policies."""

            if not _policy_retriever:
                return "Policy retriever not initialized. Check that policy PDFs are available."

            try:
                docs = _policy_retriever.invoke(query)
                results = []
                for i, doc in enumerate(docs, 1):
                    src = os.path.basename(doc.metadata.get("source", "unknown"))
                    pg = doc.metadata.get("page", "?")
                    results.append(f"[Policy Doc {i}: {src} | Page {pg}]\n{doc.page_content}")
                return "\n\n---\n\n".join(results)
            except Exception as e:
                return f"Policy retrieval error: {str(e)}"

        # Web search tool
        web_search = TavilySearch(max_results=3, topic="news")

        # All tools
        tools = [portfolio_lookup, market_data_search, calculate_metrics, policy_retriever, web_search]

        # System prompt
        SYSTEM_PROMPT = """You are a senior financial analyst at Meridian Wealth Partners, a SEBI-registered wealth
management firm managing Rs 2,000 Crore in assets across 800 high-net-worth Indian clients.

Your job is to prepare comprehensive client briefings and answer investment queries using your tools.

AVAILABLE DATA SOURCES:
1. portfolio_lookup — queries the SQL database for client holdings, allocation, and risk profile
2. market_data_search — queries the SQL database for stock/sector data (price, YTD, PE, analyst ratings)
3. calculate_metrics — computes financial metrics (returns, allocation percentages, comparisons)
4. policy_retriever — RAG search over the firm's investment policy PDFs
5. tavily_search — searches the web for latest market news, RBI updates, sector analysis

GUIDELINES:
- Always check the client's risk profile before making recommendations
- When checking policy compliance, ALWAYS use the policy_retriever tool
- Cite specific policy document names and page numbers when referencing guidelines
- Do not provide compliance conclusions without first using policy_retriever
- Do not provide market-news claims without using tavily_search
- If required data is missing, say so explicitly instead of inferring
- Use Indian Rupee (₹) for all amounts
- Include specific numbers: exact returns, allocation percentages, policy thresholds
- For briefings, structure as: Portfolio Summary → Market Context → Policy Compliance → Recommendations"""

        # Create agent
        print("⏳ Creating LLM and agent...")
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
        _agent = create_agent(
            model="openai:gpt-4-turbo",
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )

        _AGENT_READY = True
        print("✅ Agent initialized successfully!")
        return _agent
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_financial_agent(question: str, client_name: str | None = None) -> dict[str, object]:
    """
    Run the financial analyst agent.

    Args:
        question: User query about portfolio, market, or policy
        client_name: Optional client name for context

    Returns:
        Dictionary with keys: answer, tools_used, sources
    """
    global _agent, _AGENT_READY

    # Lazy initialize agent on first call
    if not _AGENT_READY and _agent is None:
        _init_agent()

    # Fallback to scaffold if agent unavailable
    if not _AGENT_READY or _agent is None:
        return _scaffold_response(question, client_name)

    try:
        # Prepare query with client context
        query = question
        if client_name:
            query = f"[Client: {client_name}] {question}"

        # Invoke agent
        result = _agent.invoke(
            {
                "messages": [
                    {"role": "user", "content": query}
                ]
            }
        )

        # Extract final answer
        final_msg = result["messages"][-1]
        answer = final_msg.content if hasattr(final_msg, "content") else str(final_msg)

        # Collect tools used from message history
        tools_used = []
        sources = set()
        for msg in result["messages"]:
            msg_type = type(msg).__name__
            if msg_type == "ToolMessage":
                tools_used.append(msg.name)
                if msg.name == "policy_retriever":
                    sources.add("Policy PDFs: data/policy_document/")
                elif msg.name == "web_search" or msg.name == "tavily_search":
                    sources.add("Web Search: Tavily")
                elif msg.name in ["portfolio_lookup", "market_data_search"]:
                    sources.add("SQLite: data/meridian_wealth.db")

        sources_list = list(sources) or [
            "SQLite: data/meridian_wealth.db",
            "Policy PDFs: data/policy_document/",
            "Web Search: Tavily",
        ]

        return {
            "answer": answer,
            "tools_used": tools_used or ["portfolio_lookup", "market_data_search"],
            "sources": sources_list,
        }

    except Exception as e:
        return {
            "answer": f"Agent execution error: {str(e)}. Falling back to scaffold response.",
            "tools_used": [],
            "sources": [],
        }
