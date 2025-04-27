import yfinance as yf
from fastapi import FastAPI
from datetime import datetime
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# Database setup
def get_db():
    conn = sqlite3.connect('gold_prices.db')
    return conn

# Initialize database
conn = get_db()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        price REAL,
        currency TEXT,
        timestamp DATETIME
    )
''')
conn.commit()
conn.close()

# Symbol for Gold Spot Price
symbol = "GC=F"

def fetch_gold_price():
    try:
        gold = yf.Ticker(symbol)
        data = gold.history(period="1d", interval="1m")
        return data['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return None

def update_gold_price():
    price = fetch_gold_price()
    if price:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO prices (price, currency, timestamp) VALUES (?, ?, ?)",
            (price, "USD", datetime.utcnow())
        )
        conn.commit()
        conn.close()

# Schedule updates every minute
scheduler = BackgroundScheduler()
scheduler.add_job(update_gold_price, 'interval', minutes=1)
scheduler.start()

@app.get("/gold")
async def gold_price():
    price = fetch_gold_price()  # Get real-time price
    if not price:
        return {"error": "Failed to fetch price"}
    
    return {
        "price": price,
        "currency": "USD",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "Yahoo Finance via yfinance"
    }

@app.get("/history")
async def price_history():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT price, timestamp FROM prices ORDER BY timestamp DESC LIMIT 100")
    history = cursor.fetchall()
    conn.close()
    
    return {
        "prices": [{"price": p[0], "timestamp": p[1]} for p in history],
        "count": len(history)
    }

@app.get("/")
async def root():
    return {"message": "Gold Price API - Real-time data with 1-minute updates"}
