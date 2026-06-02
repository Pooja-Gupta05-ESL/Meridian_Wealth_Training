# Financial Analyst App (FastAPI + Static Frontend)

This scaffold deploys the Lab 6.4 workflow as:
- FastAPI backend for API endpoints
- Static HTML/CSS/JavaScript frontend for the UI

## 1) Setup

```powershell
cd "d:\AI Training\Training\Module 6 - Agentic AI with LangGraph\financial_analyst_app"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill values in `.env` for `OPENAI_API_KEY` and `TAVILY_API_KEY`.

## 2) Run

```powershell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open:
- http://localhost:8000/ (main query UI)
- http://localhost:8000/briefing.html (briefing style page)
- http://localhost:8000/api/health

## 3) Integrate Lab 6.4 Agent

Update `source/agent_runtime.py` in `run_financial_agent()`.
Current scaffold includes:
- DB connectivity check using `data/meridian_wealth.db`
- deterministic fallback response for UI testing

Replace fallback logic with your notebook's `create_agent(...)` and tools wiring.
