from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import time
from datetime import datetime, timedelta
import yfinance as yf
import hashlib
import secrets
from passlib.context import CryptContext # For password hashing
from jose import JWTError, jwt # For JWT
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # For auth flow
from fastapi import Depends, status # For dependency injection and status codes
import traceback # Import traceback for detailed error logging

# --- Configuration ---
SECRET_KEY = secrets.token_hex(32) # Replace with a strong, persistent key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Points to the /login endpoint

# Gold price cache
gold_price_cache = None
gold_price_last_updated = None

# Silver price cache
silver_price_cache = None
silver_price_last_updated = None

# Palladium price cache
palladium_price_cache = None
palladium_price_last_updated = None

app = FastAPI()

# CORS middleware setup
# Allow the frontend origin specifically, and allow credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins (use with caution in production)
    allow_credentials=True, # Note: allow_credentials=True with allow_origins=["*"] can be problematic in some browsers/configs
    allow_methods=["*"], # Allow all standard methods
    allow_headers=["Content-Type", "Authorization"], # Explicitly allow common headers
)

# Database model
class APIKey(BaseModel):
    key: str
    is_active: bool
    created_at: float
    last_used:  float
    usage_count: int
    user_id: Optional[int] = None # Link to user

# User model
class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: str # Will store hashed password

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Database setup
def get_db_connection():
    conn = sqlite3.connect('api_keys.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at REAL,
                last_used REAL,
                usage_count INTEGER DEFAULT 0,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL
            )
        ''')
        conn.commit()
    except Exception as e:
        print("!!! ERROR DURING DB INITIALIZATION !!!")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

# --- Authentication Utilities ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (token_data.username,))
        user = cursor.fetchone()

        if user is None:
            raise credentials_exception
        # Return the user object (as a dictionary)
        return dict(user)
    except JWTError:
        raise credentials_exception
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in get_current_user !!!")
        traceback.print_exc()
        # Re-raise as a 500 error if it wasn't a standard auth error
        raise HTTPException(status_code=500, detail="Internal server error during authentication.")
    finally:
        if conn:
            conn.close()


# --- User Management ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_pw = get_password_hash(user_data.password) # Use passlib hashing
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (user_data.username, hashed_pw)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "username": user_data.username, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in register_user !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred during registration.")
    finally:
        if conn:
            conn.close()

# Login endpoint using OAuth2PasswordRequestForm for standard form data
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
        user = cursor.fetchone()

        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in login_for_access_token !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login.")
    finally:
        if conn:
            conn.close()


# Example protected endpoint to get current user info
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
     # FastAPI automatically converts the dict from get_current_user
    return current_user


# --- API Key Management (Now requires Authentication) ---

@app.get("/api-keys", response_model=List[APIKey])
async def get_user_keys(current_user: dict = Depends(get_current_user)):
    """Gets API keys belonging to the currently authenticated user."""
    conn = None # Initialize conn to None
    keys = [] # Initialize keys list outside try block
    try: # Wrap the entire function logic
        user_id = current_user["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        # Select only the columns needed for the APIKey model
        cursor.execute(
            "SELECT key, is_active, created_at, last_used, usage_count, user_id FROM api_keys WHERE user_id = ?",
            (user_id,)
        )
        fetched_rows = cursor.fetchall()

        print(f"--- Processing {len(fetched_rows)} rows for user {user_id} ---") # Log row count
        for row_num, row in enumerate(fetched_rows):
            # Inner try-except for processing each row
            try:
                row_dict = dict(row) # Convert row to dict for easier checking
                print(f"Processing row {row_num}: {row_dict}") # Log each row

                # More robust mapping with checks for None where not allowed by Pydantic model
                key_data = {
                    "key": row_dict.get("key"),
                    "is_active": bool(row_dict.get("is_active", False)), # Default to False if None/missing
                    "created_at": row_dict.get("created_at"),
                    "last_used": row_dict.get("last_used"),
                    "usage_count": row_dict.get("usage_count"),
                    "user_id": row_dict.get("user_id") # Optional in model, can be None
                }

                # Check for None in required fields before creating model
                required_fields = ["key", "created_at", "last_used", "usage_count"]
                for field in required_fields:
                     if key_data[field] is None:
                         print(f"Error: Field '{field}' is None in row {row_num} for user {user_id}. Row data: {row_dict}")
                         raise ValueError(f"Field '{field}' cannot be None.")

                # Attempt to create the Pydantic model
                keys.append(APIKey(**key_data))

            except (Exception, ValueError) as e: # Catch ValueError and other exceptions during row processing
                print(f"Error processing row #{row_num} for user {user_id}: {row_dict}")
                print(f"Instantiation/Validation error: {e}")
                # Raise 500 error to signal backend issue for this specific row
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing API key data (row {row_num}). Check server logs."
                )

        print(f"--- Successfully processed {len(keys)} keys for user {user_id} ---") # Log success
        return keys

    except Exception as e: # Catch ANY unexpected exception in the outer block
        print(f"!!! UNEXPECTED ERROR in get_user_keys for user {current_user.get('id', 'UNKNOWN')} !!!")
        traceback.print_exc() # Print detailed traceback to server console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching API keys. Check server logs."
        )
    finally:
        if conn:
            conn.close() # Ensure connection is closed

@app.post("/api-keys/{key}/toggle")
async def toggle_key_status(key: str, current_user: dict = Depends(get_current_user)):
    """Toggles the status of an API key belonging to the current user."""
    conn = None # Initialize conn to None
    try:
        user_id = current_user["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure the key belongs to the user before toggling
        cursor.execute("SELECT id FROM api_keys WHERE key = ? AND user_id = ?", (key, user_id))
        key_record = cursor.fetchone()

        if not key_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found or not owned by user")

        cursor.execute("UPDATE api_keys SET is_active = NOT is_active WHERE key = ? AND user_id = ?", (key, user_id))
        conn.commit()
        return {"message": f"Key {key} status toggled"}
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in toggle_key_status for key {key}, user {current_user.get('id', 'UNKNOWN')} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while toggling key status.")
    finally:
        if conn:
            conn.close()


@app.get("/api-keys/stats")
async def get_user_key_stats(current_user: dict = Depends(get_current_user)):
    """Gets statistics (total keys, total usage) for the authenticated user."""
    conn = None # Initialize conn to None
    try:
        user_id = current_user["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        # Calculate stats only for the current user's keys
        cursor.execute(
            "SELECT COUNT(*) as total, SUM(usage_count) as usage FROM api_keys WHERE user_id = ?",
            (user_id,)
        )
        stats = cursor.fetchone()

        # Ensure stats are returned even if the user has no keys yet
        total_keys = stats["total"] if stats and stats["total"] is not None else 0
        total_usage = stats["usage"] if stats and stats["usage"] is not None else 0

        return {
            "user_id": user_id,
            "username": current_user["username"],
            "total_keys": total_keys,
            "total_usage": total_usage
        }
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in get_user_key_stats for user {current_user.get('id', 'UNKNOWN')} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching key statistics.")
    finally:
        if conn:
            conn.close()


@app.post("/api-keys/{key}/log")
async def log_key_usage(key: str):
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET last_used = ?, usage_count = usage_count + 1 WHERE key = ?",
            (time.time(), key)
        )
        conn.commit()
        # TODO: Associate usage with the user owning the key - More complex, maybe add a separate logs table?
        return {"message": "Usage logged"}
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in log_key_usage for key {key} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while logging key usage.")
    finally:
        if conn:
            conn.close()


# Key creation doesn't need a request body now, just auth
@app.post("/api-keys", response_model=APIKey)
async def create_key(current_user: dict = Depends(get_current_user)):
    """Creates a new API key for the authenticated user."""
    conn = None # Initialize conn to None
    try: # Wrap the main logic
        user_id = current_user["id"] # Get user_id from authenticated token
        new_key = secrets.token_urlsafe(32) # Generate a secure random key
        is_active = True # Default to active
        created_at = time.time()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO api_keys (key, is_active, created_at, last_used, usage_count, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (new_key, is_active, created_at, 0, 0, user_id)
        )
        conn.commit()
        # Fetch only the necessary columns for the APIKey model
        cursor.execute(
             "SELECT key, is_active, created_at, last_used, usage_count, user_id FROM api_keys WHERE key = ?",
             (new_key,)
         )
        created_key_row = cursor.fetchone()
        if created_key_row:
              # Explicitly create dict from row before passing to Pydantic model
              key_data = {
                  "key": created_key_row["key"],
                  "is_active": bool(created_key_row["is_active"]),
                  "created_at": created_key_row["created_at"],
                  "last_used": created_key_row["last_used"],
                  "usage_count": created_key_row["usage_count"],
                  "user_id": created_key_row["user_id"]
              }
              return APIKey(**key_data)
        else:
             # This case should ideally not happen if insert was successful
             raise HTTPException(status_code=500, detail="Failed to retrieve created key")

    except sqlite3.IntegrityError:
        # Should be rare with secrets.token_urlsafe, but handle just in case
        raise HTTPException(status_code=500, detail="Failed to generate unique API key, please try again")
    except Exception as e: # Catch ANY other unexpected exception
        print(f"!!! UNEXPECTED ERROR in create_key for user {current_user.get('id', 'UNKNOWN')} !!!")
        traceback.print_exc() # Print detailed traceback to server console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the API key. Check server logs."
        )
    finally:
        # Ensure connection is closed even if errors occurred
        if conn:
             conn.close()

@app.delete("/api-keys/{key}")
async def delete_key(key: str, current_user: dict = Depends(get_current_user)):
    """Deletes an API key belonging to the current user."""
    conn = None # Initialize conn to None
    try:
        user_id = current_user["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure the key belongs to the user before deleting
        cursor.execute("DELETE FROM api_keys WHERE key = ? AND user_id = ?", (key, user_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found or not owned by user")
        conn.commit()
        return {"message": f"Key {key} deleted"}
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in delete_key for key {key}, user {current_user.get('id', 'UNKNOWN')} !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the key.")
    finally:
        if conn:
            conn.close()


async def fetch_live_gold_price():
    """Fetch current gold price using yfinance"""
    try:
        gold_data = yf.download('GC=F', period='1d')
        if not gold_data.empty:
            current_price_raw = gold_data['Close'].iloc[-1]
            current_price_float = float(current_price_raw) # Ensure it's a float
            print(f"Fetched Gold Price: {current_price_float} (Type: {type(current_price_float)})") # Log fetched value and type
            return current_price_float
        return None
    except Exception as e:
        print(f"Error fetching/processing gold price: {e}")
        return None

async def fetch_live_silver_price():
    """Fetch current silver price using yfinance"""
    try:
        silver_data = yf.download('SI=F', period='1d')
        if not silver_data.empty:
            current_price_raw = silver_data['Close'].iloc[-1]
            current_price_float = float(current_price_raw) # Ensure it's a float
            print(f"Fetched Silver Price: {current_price_float} (Type: {type(current_price_float)})") # Log fetched value and type
            return current_price_float
        return None
    except Exception as e:
        print(f"Error fetching/processing silver price: {e}")
        return None

async def fetch_live_palladium_price():
    """Fetch current palladium price using yfinance"""
    try:
        palladium_data = yf.download('PA=F', period='1d')
        if not palladium_data.empty:
            current_price_raw = palladium_data['Close'].iloc[-1]
            current_price_float = float(current_price_raw) # Ensure it's a float
            print(f"Fetched Palladium Price: {current_price_float} (Type: {type(current_price_float)})") # Log fetched value and type
            return current_price_float
        return None
    except Exception as e:
        print(f"Error fetching/processing palladium price: {e}")
        return None

# --- Gold Price Endpoint (Still uses API Key Auth) ---
# Note: This endpoint uses API Key Authentication.

@app.get("/gold")
async def get_gold_data(api_key: str = Header(...)):
    conn = None # Initialize conn to None
    try:
        global gold_price_cache, gold_price_last_updated

        # Validate API key
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if key exists and is active
        cursor.execute("SELECT id FROM api_keys WHERE key = ? AND is_active = 1", (api_key,))
        key_record = cursor.fetchone()

        if not key_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")

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
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except HTTPException as http_exc: # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in get_gold_data for key {api_key[:8]}... !!!") # Avoid logging full key
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching gold data.")
    finally:
        if conn:
            conn.close()


# --- Dashboard Prices Endpoint (Uses JWT Auth) ---
@app.get("/dashboard/prices")
async def get_dashboard_prices(current_user: dict = Depends(get_current_user)):
    """Fetches all commodity prices for the authenticated dashboard user."""
    # No API key validation or usage logging needed here, as auth is handled by JWT.
    # We rely on the caching logic within the individual price endpoints being called internally,
    # or we could implement caching directly here if preferred. For simplicity, let's call them.
    # Note: This approach might log usage multiple times if the user also uses the direct API key endpoints.
    # A more robust solution might involve separate internal fetching functions without logging.

    # We still need access to the global cache variables if we want to check them here
    global gold_price_cache, gold_price_last_updated
    global silver_price_cache, silver_price_last_updated
    global palladium_price_cache, palladium_price_last_updated

    prices = {}
    errors = {}

    # Fetch Gold
    try:
        if (gold_price_last_updated is None or
            (datetime.now() - gold_price_last_updated) > timedelta(minutes=1)):
            gold_price = await fetch_live_gold_price()
            if gold_price is not None:
                gold_price_cache = gold_price
                gold_price_last_updated = datetime.now()
        if gold_price_cache is not None:
             prices["gold"] = {
                 "price": gold_price_cache,
                 "currency": "USD",
                 "last_updated": gold_price_last_updated.timestamp(),
                 "unit": "per troy ounce",
                 "source": "live market data"
             }
        else:
            errors["gold"] = "Unable to fetch gold price"
    except Exception as e:
        print(f"Error fetching gold for dashboard: {e}")
        errors["gold"] = "Error fetching gold price"

    # Fetch Silver
    try:
        if (silver_price_last_updated is None or
            (datetime.now() - silver_price_last_updated) > timedelta(minutes=1)):
            silver_price = await fetch_live_silver_price()
            if silver_price is not None:
                silver_price_cache = silver_price
                silver_price_last_updated = datetime.now()
        if silver_price_cache is not None:
            prices["silver"] = {
                "price": silver_price_cache,
                "currency": "USD",
                "last_updated": silver_price_last_updated.timestamp(),
                "unit": "per troy ounce",
                "source": "live market data"
            }
        else:
             errors["silver"] = "Unable to fetch silver price"
    except Exception as e:
        print(f"Error fetching silver for dashboard: {e}")
        errors["silver"] = "Error fetching silver price"

    # Fetch Palladium
    try:
        if (palladium_price_last_updated is None or
            (datetime.now() - palladium_price_last_updated) > timedelta(minutes=1)):
            palladium_price = await fetch_live_palladium_price()
            if palladium_price is not None:
                palladium_price_cache = palladium_price
                palladium_price_last_updated = datetime.now()
        if palladium_price_cache is not None:
            prices["palladium"] = {
                "price": palladium_price_cache,
                "currency": "USD",
                "last_updated": palladium_price_last_updated.timestamp(),
                "unit": "per troy ounce",
                "source": "live market data"
            }
        else:
             errors["palladium"] = "Unable to fetch palladium price"
    except Exception as e:
        print(f"Error fetching palladium for dashboard: {e}")
        errors["palladium"] = "Error fetching palladium price"

    # Return fetched prices and any errors encountered
    # If no prices could be fetched at all, maybe return a 503?
    if not prices and errors:
         # Raise a 503 if all fetches failed
         first_error = list(errors.values())[0]
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to fetch any prices. Last error: {first_error}")

    return {"prices": prices, "errors": errors}


# --- Silver Price Endpoint (Uses API Key Auth) ---
@app.get("/silver")
async def get_silver_data(api_key: str = Header(...)):
    conn = None
    try:
        global silver_price_cache, silver_price_last_updated

        # Validate API key
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM api_keys WHERE key = ? AND is_active = 1", (api_key,))
        key_record = cursor.fetchone()

        if not key_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")

        # Log key usage
        await log_key_usage(api_key)

        # Check cache
        if (silver_price_last_updated is None or
            (datetime.now() - silver_price_last_updated) > timedelta(minutes=1)):
            silver_price = await fetch_live_silver_price()
            if silver_price is not None:
                silver_price_cache = silver_price
                silver_price_last_updated = datetime.now()

        if silver_price_cache is None:
            raise HTTPException(status_code=503, detail="Unable to fetch silver price")

        return {
            "silver_price": silver_price_cache,
            "currency": "USD",
            "last_updated": silver_price_last_updated.timestamp(),
            "unit": "per troy ounce",
            "source": "live market data"
        }
    except HTTPException as http_exc:
        raise http_exc
    except HTTPException as http_exc:
        raise http_exc
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in get_silver_data for key {api_key[:8]}... !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching silver data.")
    finally:
        if conn:
            conn.close()


# --- Palladium Price Endpoint (Uses API Key Auth) ---
@app.get("/palladium")
async def get_palladium_data(api_key: str = Header(...)):
    conn = None
    try:
        global palladium_price_cache, palladium_price_last_updated

        # Validate API key
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM api_keys WHERE key = ? AND is_active = 1", (api_key,))
        key_record = cursor.fetchone()

        if not key_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")

        # Log key usage
        await log_key_usage(api_key)

        # Check cache
        if (palladium_price_last_updated is None or
            (datetime.now() - palladium_price_last_updated) > timedelta(minutes=1)):
            palladium_price = await fetch_live_palladium_price()
            if palladium_price is not None:
                palladium_price_cache = palladium_price
                palladium_price_last_updated = datetime.now()

        if palladium_price_cache is None:
            raise HTTPException(status_code=503, detail="Unable to fetch palladium price")

        return {
            "palladium_price": palladium_price_cache,
            "currency": "USD",
            "last_updated": palladium_price_last_updated.timestamp(),
            "unit": "per troy ounce",
            "source": "live market data"
        }
    except HTTPException as http_exc:
        raise http_exc
    except HTTPException as http_exc:
        raise http_exc
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR in get_palladium_data for key {api_key[:8]}... !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching palladium data.")
    finally:
        if conn:
            conn.close()
