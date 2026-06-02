from pathlib import Path
import os
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Lazy import to avoid hanging
run_financial_agent = None

# Load API keys/config from .env if present
load_dotenv()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    client_name: str | None = None


class MainChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    client_name: str | None = None


class AskResponse(BaseModel):
    answer: str
    tools_used: list[str]
    sources: list[str]


app = FastAPI(title="Financial Analyst Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_agent():
    """Return the real Lab 6.4 financial agent implementation."""
    global run_financial_agent
    if run_financial_agent is None:
        try:
            from source.agent_runtime import run_financial_agent as real_agent
            run_financial_agent = real_agent
        except Exception as exc:
            error_message = str(exc)

            def startup_error_agent(question, client_name=None):
                return {
                    "answer": (
                        "Agent startup error. Unable to import source.agent_runtime.run_financial_agent. "
                        f"Details: {error_message}\n\n"
                        "Please verify dependencies in requirements.txt and restart the server."
                    ),
                    "tools_used": [],
                    "sources": [],
                }

            run_financial_agent = startup_error_agent
    return run_financial_agent


@app.get("/api/health")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
def ask_agent(payload: AskRequest) -> AskResponse:
    try:
        agent = _get_agent()
        result = agent(question=payload.question, client_name=payload.client_name)
        return AskResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/main/chat", response_model=AskResponse)
def main_chat(payload: MainChatRequest) -> AskResponse:
    try:
        agent = _get_agent()
        result = agent(question=payload.message, client_name=payload.client_name)
        return AskResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/agentinfo")
def agent_info() -> dict[str, object]:
    return {
        "name": "Financial Analyst Agent",
        "version": app.version,
        "status": "ready",
        "endpoints": {
            "health": "/health",
            "chat": "/main/chat",
            "agentinfo": "/agentinfo",
        },
        "tools": ["portfolio_lookup", "policy_retriever", "tavily_search"],
    }


@app.get("/diagnostic")
def diagnostic() -> dict[str, object]:
    """Diagnostic endpoint to troubleshoot agent initialization."""
    diagnostics = {
        "api_keys": {
            "openai": "✅ Set" if os.environ.get("OPENAI_API_KEY") else "❌ Missing",
            "tavily": "✅ Set" if os.environ.get("TAVILY_API_KEY") else "❌ Missing",
        },
        "dependencies": {},
        "database": {},
        "policy_pdfs": {},
        "recommendations": []
    }
    
    # Check LangChain packages
    langchain_packages = [
        "langchain", "langchain_openai", "langchain_community", 
        "langchain_tavily", "langchain_core", "faiss"
    ]
    for pkg in langchain_packages:
        try:
            __import__(pkg.replace("_", "-"))
            diagnostics["dependencies"][pkg] = "✅ Installed"
        except ImportError:
            diagnostics["dependencies"][pkg] = "❌ Missing"
            diagnostics["recommendations"].append(f"Install {pkg}: pip install {pkg}")
    
    # Check database
    db_path = Path(__file__).resolve().parent / "data" / "vector_db" / "meridian_wealth.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            stats = {}
            for table in ["clients", "holdings", "market_data"]:
                try:
                    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    stats[table] = count
                except:
                    stats[table] = 0
            
            diagnostics["database"] = {
                "file": f"✅ Found ({db_path.stat().st_size / 1024:.0f} KB)",
                **{f"{k}_count": v for k, v in stats.items()}
            }
            
            if stats["clients"] == 0:
                diagnostics["recommendations"].append(
                    "Database is empty. Run Lab_4.1 to seed test data."
                )
            
            conn.close()
        except Exception as e:
            diagnostics["database"]["error"] = str(e)
    else:
        diagnostics["database"]["file"] = "❌ Not found"
        diagnostics["recommendations"].append(
            f"Create database at {db_path}"
        )
    
    # Check policy PDFs
    policy_dir = Path(__file__).resolve().parent / "data" / "policy_document"
    if policy_dir.exists():
        pdfs = list(policy_dir.glob("*.pdf"))
        diagnostics["policy_pdfs"]["directory"] = f"✅ Found"
        diagnostics["policy_pdfs"]["count"] = len(pdfs)
        if pdfs:
            diagnostics["policy_pdfs"]["files"] = [p.name for p in pdfs[:5]]
        else:
            diagnostics["policy_pdfs"]["count_status"] = "⚠️ Empty"
            diagnostics["recommendations"].append(
                "Add policy PDFs: Extract policy_documents.zip from Lab_6.4 notebook"
            )
    else:
        diagnostics["policy_pdfs"]["directory"] = "⚠️ Not found (optional)"
        diagnostics["recommendations"].append(
            "Create data/policy_document/ and add PDFs for RAG pipeline"
        )
    
    # Summary
    diagnostics["status"] = "✅ Ready" if (
        os.environ.get("OPENAI_API_KEY") and 
        os.environ.get("TAVILY_API_KEY") and
        all("✅" in v for v in diagnostics["dependencies"].values()) and
        "file" in diagnostics["database"]
    ) else "⚠️ Incomplete"
    
    return diagnostics


frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
