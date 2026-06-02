import sqlite3

DB_PATH = "data/vector_db/meridian_wealth.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    name TEXT,
    risk_profile TEXT,
    investment_horizon TEXT,
    aum_inr REAL,
    relationship_mgr TEXT,
    phone TEXT,
    email TEXT,
    city TEXT,
    join_date TEXT,
    last_review TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS holdings (
    client_id TEXT,
    ticker TEXT,
    company_name TEXT,
    shares REAL,
    avg_cost_basis REAL,
    current_price REAL,
    sector TEXT,
    purchase_date TEXT,
    PRIMARY KEY (client_id, ticker)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS market_data (
    ticker TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    current_price REAL,
    ytd_return_pct REAL,
    pe_ratio REAL,
    analyst_rating TEXT,
    high_52w REAL,
    low_52w REAL,
    market_cap_cr REAL
)
""")

# Insert sample clients
clients = [
    ("CLT-001", "Rajesh Mehta", "Moderate-Aggressive", "10 years", 2500000, "Priya Sharma", "9876543210", "rajesh@email.com", "Mumbai", "2020-01-15", "2026-05-30"),
    ("CLT-002", "Amit Choudhury", "Aggressive", "15 years", 5000000, "Vikram Singh", "9876543211", "amit@email.com", "Delhi", "2019-06-20", "2026-05-25"),
    ("CLT-003", "Karan Malhotra", "Moderate", "8 years", 1800000, "Priya Sharma", "9876543212", "karan@email.com", "Bangalore", "2021-02-10", "2026-05-28"),
    ("CLT-004", "Neha Gupta", "Conservative", "5 years", 1200000, "Ajay Kumar", "9876543213", "neha@email.com", "Pune", "2022-03-15", "2026-05-20"),
    ("CLT-005", "Rohan Singh", "Moderate-Aggressive", "12 years", 3500000, "Vikram Singh", "9876543214", "rohan@email.com", "Bangalore", "2020-08-05", "2026-05-22"),
]

for client in clients:
    try:
        cursor.execute("""
            INSERT INTO clients 
            (client_id, name, risk_profile, investment_horizon, aum_inr, relationship_mgr, phone, email, city, join_date, last_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, client)
    except:
        pass

# Insert sample market data
market_data = [
    ("TCS", "Tata Consultancy Services", "IT", 3850, 22.5, 28.4, "Strong Buy", 4200, 3150, 1200),
    ("HDFC", "HDFC Bank", "Banking", 1645, 8.3, 18.5, "Buy", 1900, 1400, 950),
    ("ITC", "ITC Limited", "Diversified", 425, -2.1, 12.8, "Hold", 480, 380, 380),
    ("RELIANCE", "Reliance Industries", "Energy", 2950, 15.7, 22.1, "Buy", 3200, 2400, 1850),
    ("INFY", "Infosys", "IT", 1520, 18.9, 25.3, "Strong Buy", 1800, 1150, 720),
    ("AXISBANK", "Axis Bank", "Banking", 1120, 12.5, 15.2, "Buy", 1350, 950, 320),
    ("LT", "Larsen & Toubro", "Engineering", 2580, 11.2, 24.6, "Hold", 2850, 2100, 420),
    ("MARUTI", "Maruti Suzuki", "Auto", 8950, 5.3, 18.7, "Hold", 10200, 7800, 180),
]

for md in market_data:
    try:
        cursor.execute("""
            INSERT INTO market_data
            (ticker, company_name, sector, current_price, ytd_return_pct, pe_ratio, analyst_rating, high_52w, low_52w, market_cap_cr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, md)
    except:
        pass

# Insert sample holdings for CLT-001
holdings_clt001 = [
    ("CLT-001", "TCS", "Tata Consultancy Services", 400, 3200, 3850, "IT", "2022-01-20"),
    ("CLT-001", "HDFC", "HDFC Bank", 800, 1400, 1645, "Banking", "2021-06-15"),
    ("CLT-001", "INFY", "Infosys", 500, 1200, 1520, "IT", "2020-11-10"),
    ("CLT-001", "RELIANCE", "Reliance Industries", 300, 2400, 2950, "Energy", "2020-03-25"),
]

for holding in holdings_clt001:
    try:
        cursor.execute("""
            INSERT INTO holdings
            (client_id, ticker, company_name, shares, avg_cost_basis, current_price, sector, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, holding)
    except:
        pass

# Insert holdings for CLT-002
holdings_clt002 = [
    ("CLT-002", "TCS", "Tata Consultancy Services", 800, 3000, 3850, "IT", "2021-02-10"),
    ("CLT-002", "RELIANCE", "Reliance Industries", 600, 2300, 2950, "Energy", "2020-05-15"),
    ("CLT-002", "LT", "Larsen & Toubro", 400, 2200, 2580, "Engineering", "2021-08-20"),
    ("CLT-002", "MARUTI", "Maruti Suzuki", 200, 8500, 8950, "Auto", "2022-01-05"),
]

for holding in holdings_clt002:
    try:
        cursor.execute("""
            INSERT INTO holdings
            (client_id, ticker, company_name, shares, avg_cost_basis, current_price, sector, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, holding)
    except:
        pass

conn.commit()

# List all clients
print("✅ Database populated successfully!\n")
print("Available Clients:")
cursor.execute("SELECT client_id, name, risk_profile, aum_inr FROM clients ORDER BY client_id")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]}) - AUM: ₹{row[3]:,.0f}")

conn.close()
