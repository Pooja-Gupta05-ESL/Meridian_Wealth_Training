"""
Database Query Module for Meridian Wealth Partners
Uses meridian_wealth.db (SQLite) populated from Lab 6.4 dataset
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "meridian_wealth.db"


def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def get_client_by_id(client_id: str) -> Optional[Dict[str, Any]]:
    """
    Get client details by client_id.
    
    Args:
        client_id: e.g., "CLT-001"
    
    Returns:
        Dictionary with client info or None if not found
        Keys: client_id, name, risk_profile, investment_horizon, aum_inr, 
              relationship_mgr, phone, email, city, join_date
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT * FROM clients 
        WHERE client_id = ?
        """,
        (client_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_client_portfolio(client_id: str) -> List[Dict[str, Any]]:
    """
    Get all holdings for a client with enriched market data.
    
    Args:
        client_id: e.g., "CLT-001"
    
    Returns:
        List of holdings with details:
        Keys: ticker, company_name, shares, avg_cost_basis, current_price, sector,
              ytd_return_pct, pe_ratio, analyst_rating, 52w_high, 52w_low,
              position_value, unrealized_gain, unrealized_gain_pct, position_weight_pct
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get holdings with market data enrichment
    cursor.execute(
        """
        SELECT 
            h.ticker,
            h.company_name,
            h.shares,
            h.avg_cost_basis,
            h.current_price,
            h.sector,
            m.ytd_return_pct,
            m.pe_ratio,
            m.analyst_rating,
            m."52w_high",
            m."52w_low",
            m.market_cap_cr,
            (h.shares * h.current_price) as position_value,
            (h.shares * h.current_price - h.shares * h.avg_cost_basis) as unrealized_gain,
            ROUND((h.shares * h.current_price - h.shares * h.avg_cost_basis) / (h.shares * h.avg_cost_basis) * 100, 2) as unrealized_gain_pct
        FROM holdings h
        LEFT JOIN market_data m ON h.ticker = m.ticker
        WHERE h.client_id = ?
        ORDER BY (h.shares * h.current_price) DESC
        """,
        (client_id,)
    )
    
    holdings = [dict(row) for row in cursor.fetchall()]
    
    # Calculate position weights
    total_value = sum(h.get("position_value", 0) for h in holdings)
    for holding in holdings:
        if total_value > 0:
            holding["position_weight_pct"] = round(
                (holding.get("position_value", 0) / total_value) * 100, 2
            )
        else:
            holding["position_weight_pct"] = 0
    
    conn.close()
    return holdings


def get_portfolio_summary(client_id: str) -> Optional[Dict[str, Any]]:
    """
    Get portfolio summary (total value, cost basis, overall return, allocation by sector).
    
    Args:
        client_id: e.g., "CLT-001"
    
    Returns:
        Dictionary with:
        Keys: total_portfolio_value, total_cost_basis, overall_return_inr,
              overall_return_pct, sector_allocation (dict of sector: weight_pct),
              top_3_holdings (list), unrealized_gains_by_sector
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get portfolio stats
    cursor.execute(
        """
        SELECT 
            SUM(h.shares * h.current_price) as total_portfolio_value,
            SUM(h.shares * h.avg_cost_basis) as total_cost_basis,
            SUM(h.shares * h.current_price - h.shares * h.avg_cost_basis) as overall_return_inr
        FROM holdings h
        WHERE h.client_id = ?
        """,
        (client_id,)
    )
    
    row = cursor.fetchone()
    summary = dict(row) if row else {
        "total_portfolio_value": 0,
        "total_cost_basis": 0,
        "overall_return_inr": 0
    }
    
    # Calculate overall return %
    if summary["total_cost_basis"] and summary["total_cost_basis"] > 0:
        summary["overall_return_pct"] = round(
            (summary["overall_return_inr"] / summary["total_cost_basis"]) * 100, 2
        )
    else:
        summary["overall_return_pct"] = 0
    
    # Get sector allocation
    cursor.execute(
        """
        SELECT 
            h.sector,
            SUM(h.shares * h.current_price) as sector_value
        FROM holdings h
        WHERE h.client_id = ?
        GROUP BY h.sector
        ORDER BY sector_value DESC
        """,
        (client_id,)
    )
    
    sector_data = cursor.fetchall()
    total_value = summary["total_portfolio_value"] or 1
    summary["sector_allocation"] = {
        dict(row)["sector"]: round((dict(row)["sector_value"] / total_value) * 100, 2)
        for row in sector_data
    }
    
    # Get top 3 holdings
    cursor.execute(
        """
        SELECT 
            h.ticker,
            h.company_name,
            h.sector,
            h.shares,
            h.current_price,
            (h.shares * h.current_price) as position_value
        FROM holdings h
        WHERE h.client_id = ?
        ORDER BY (h.shares * h.current_price) DESC
        LIMIT 3
        """,
        (client_id,)
    )
    
    summary["top_3_holdings"] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return summary


def search_market_data(query: str) -> List[Dict[str, Any]]:
    """
    Search market data by ticker, company_name, or sector.
    
    Args:
        query: Ticker (e.g., "RELIANCE"), company name, or sector
    
    Returns:
        List of matching market data records
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{query.upper()}%"
    
    cursor.execute(
        """
        SELECT * FROM market_data
        WHERE UPPER(ticker) LIKE ? 
           OR UPPER(company_name) LIKE ?
           OR UPPER(sector) LIKE ?
        ORDER BY market_cap_cr DESC
        """,
        (search_pattern, search_pattern, search_pattern)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_market_data_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed market data for a single ticker.
    
    Args:
        ticker: e.g., "RELIANCE"
    
    Returns:
        Dictionary with market data or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT * FROM market_data
        WHERE UPPER(ticker) = UPPER(?)
        """,
        (ticker,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_sector_allocation_comparison(*client_ids: str) -> Dict[str, Dict[str, float]]:
    """
    Compare sector allocation across multiple clients.
    
    Args:
        *client_ids: Variable number of client IDs to compare
    
    Returns:
        Dictionary mapping client_id to sector allocation dict
    """
    result = {}
    
    for client_id in client_ids:
        summary = get_portfolio_summary(client_id)
        if summary:
            result[client_id] = summary.get("sector_allocation", {})
    
    return result


def get_all_clients() -> List[Dict[str, Any]]:
    """
    Get list of all clients.
    
    Returns:
        List of client records
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clients ORDER BY client_id")
    
    clients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return clients


def get_concentration_check(client_id: str, ticker: str) -> Optional[Dict[str, Any]]:
    """
    Check current allocation percentage for a holding and get policy limits.
    
    Args:
        client_id: Client ID
        ticker: Stock ticker
    
    Returns:
        Dictionary with current_allocation_pct, policy_limit (from client's profile)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current holding value
    cursor.execute(
        """
        SELECT 
            h.shares * h.current_price as position_value
        FROM holdings h
        WHERE h.client_id = ? AND UPPER(h.ticker) = UPPER(?)
        """,
        (client_id, ticker)
    )
    
    holding_row = cursor.fetchone()
    position_value = dict(holding_row)["position_value"] if holding_row else 0
    
    # Get portfolio summary
    cursor.execute(
        """
        SELECT 
            SUM(h.shares * h.current_price) as total_value
        FROM holdings h
        WHERE h.client_id = ?
        """,
        (client_id,)
    )
    
    summary_row = cursor.fetchone()
    total_value = dict(summary_row)["total_value"] if summary_row else 1
    
    # Get client profile for policy limits
    cursor.execute(
        """
        SELECT risk_profile FROM clients WHERE client_id = ?
        """,
        (client_id,)
    )
    
    profile_row = cursor.fetchone()
    risk_profile = dict(profile_row)["risk_profile"] if profile_row else "Moderate"
    
    conn.close()
    
    # Policy limits by risk profile (from Lab 6.4 guidelines)
    policy_limits = {
        "Conservative": 5,
        "Moderate": 8,
        "Moderate-Aggressive": 10,
        "Aggressive": 12
    }
    
    current_pct = (position_value / total_value * 100) if total_value > 0 else 0
    
    return {
        "ticker": ticker,
        "current_allocation_pct": round(current_pct, 2),
        "risk_profile": risk_profile,
        "policy_limit_pct": policy_limits.get(risk_profile, 8),
        "is_compliant": current_pct <= policy_limits.get(risk_profile, 8),
        "position_value": round(position_value, 2),
        "total_portfolio_value": round(total_value, 2)
    }


def get_holdings_by_sector(client_id: str, sector: str) -> List[Dict[str, Any]]:
    """
    Get all holdings for a client in a specific sector.
    
    Args:
        client_id: Client ID
        sector: Sector name (e.g., "IT", "Banking", "Energy")
    
    Returns:
        List of holdings in that sector
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT 
            h.ticker,
            h.company_name,
            h.shares,
            h.current_price,
            h.sector,
            (h.shares * h.current_price) as position_value,
            m.ytd_return_pct,
            m.analyst_rating
        FROM holdings h
        LEFT JOIN market_data m ON h.ticker = m.ticker
        WHERE h.client_id = ? AND UPPER(h.sector) = UPPER(?)
        ORDER BY (h.shares * h.current_price) DESC
        """,
        (client_id, sector)
    )
    
    holdings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return holdings


def validate_database() -> Dict[str, Any]:
    """
    Validate database integrity and return statistics.
    
    Returns:
        Dictionary with table counts and status
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Count records in each table
    for table in ["clients", "holdings", "market_data"]:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        stats[table] = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "clients_count": stats.get("clients", 0),
        "holdings_count": stats.get("holdings", 0),
        "market_data_count": stats.get("market_data", 0),
        "database_ready": all(v > 0 for v in stats.values())
    }


if __name__ == "__main__":
    # Quick validation
    print("Database Validation:")
    stats = validate_database()
    print(f"  Clients: {stats['clients_count']}")
    print(f"  Holdings: {stats['holdings_count']}")
    print(f"  Market Data: {stats['market_data_count']}")
    print(f"  Status: {'✅ Ready' if stats['database_ready'] else '⚠️ Incomplete'}")
