from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import time
from datetime import datetime, timedelta
import yfinance as yf

# Gold price cache
gold_price_cache = None
gold_price_last_updated = None

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database model
class APIKey(BaseModel):
    key: str
    is_active: bool
    created_at: float
    last_used:  float
    usage_count: int

# Database setup
def get_db_connection():
    conn = sqlite3.connect('api_keys.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at REAL,
            last_used REAL,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

@app.get("/api-keys", response_model=List[APIKey])
async def get_all_keys():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys")
    keys = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return keys

@app.post("/api-keys/{key}/toggle")
async def toggle_key_status(key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE api_keys SET is_active = NOT is_active WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    return {"message": f"Key {key} status toggled"}

@app.get("/api-keys/stats")
async def get_key_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total, SUM(usage_count) as usage FROM api_keys")
    stats = cursor.fetchone()
    conn.close()
    return {
        "total_keys": stats["total"],
        "total_usage": stats["usage"] or 0
    }

@app.post("/api-keys/{key}/log")
async def log_key_usage(key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE api_keys SET last_used = ?, usage_count = usage_count + 1 WHERE key = ?",
        (time.time(), key)
    )
    conn.commit()
    conn.close()
    return {"message": "Usage logged"}

@app.post("/api-keys")
async def create_key(key_data: APIKey):
    if not key_data.key or len(key_data.key) < 32:
        raise HTTPException(status_code=400, detail="API key must be at least 32 characters")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO api_keys (key, is_active, created_at, last_used, usage_count) VALUES (?, ?, ?, ?, ?)",
            (key_data.key, key_data.is_active, time.time(), 0, 0)
        )
        conn.commit()
        return key_data
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="API key already exists")
    finally:
        conn.close()

@app.delete("/api-keys/{key}")
async def delete_key(key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_keys WHERE key = ?", (key,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="API key not found")
    conn.commit()
    conn.close()
    return {"message": f"Key {key} deleted"}

async def fetch_live_gold_price():
    """Fetch current gold price using yfinance"""
    try:
        gold_data = yf.download('GC=F', period='1d')
        if not gold_data.empty:
            current_price = gold_data['Close'].iloc[-1]
            return current_price
        return None
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return None

@app.get("/gold")
async def get_gold_data(api_key: str = Header(...)):
    global gold_price_cache, gold_price_last_updated
    
    # Validate API key
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys WHERE key = ? AND is_active = 1", (api_key,))
    key = cursor.fetchone()
    conn.close()
    
    if not key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Log key usage
    await log_key_usage(api_key)
    
    # Check if cache is expired (older than 1 minute)
    if (gold_price_last_updated is None or 
        (datetime.now() - gold_price_last_updated) > timedelta(minutes=1)):
        # Fetch fresh price
        gold_price = await fetch_live_gold_price()
        if gold_price is not None:
            gold_price_cache = gold_price
            gold_price_last_updated = datetime.now()
    
    if gold_price_cache is None:
        raise HTTPException(status_code=503, detail="Unable to fetch gold price")
    
    return {
        "gold_price": gold_price_cache,
        "currency": "USD",
        "last_updated": gold_price_last_updated.timestamp(),
        "unit": "per troy ounce",
        "source": "live market data"
    }
