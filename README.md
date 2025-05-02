# Commodity Price API with User Authentication and Key Management

This project provides a FastAPI backend and a React frontend for fetching real-time commodity prices (Gold, Silver, Palladium), secured by user authentication and API key management.

## Features

**Backend (FastAPI):**
- Fetches real-time Gold (GC=F), Silver (SI=F), and Palladium (PA=F) prices using `yfinance`.
- Implements caching for fetched prices (1-minute expiry).
- User registration and login using JWT authentication.
- Secure API key generation, management (toggle status, revoke), and usage tracking per user.
- **API Key Authenticated Endpoints:**
    - `/gold`: Returns current gold price. Requires `api-key` header.
    - `/silver`: Returns current silver price. Requires `api-key` header.
    - `/palladium`: Returns current palladium price. Requires `api-key` header.
- **JWT Authenticated Endpoint (for Frontend Dashboard):**
    - `/dashboard/prices`: Returns all three commodity prices (gold, silver, palladium) in a single response. Requires `Authorization: Bearer <TOKEN>` header.
- SQLite database (`api_keys.db`) for storing user credentials and API keys.
- CORS configured for the React frontend (default: `http://localhost:3000`).

**Frontend (React):**
- User registration and login forms.
- Dashboard page displaying:
    - User's API key statistics (total keys, total usage).
    - Current Gold, Silver, and Palladium prices fetched via the `/dashboard/prices` endpoint.
- API Key management page:
    - View existing keys with status, creation date, last used date, usage count.
    - Create new API keys.
    - Toggle key status (active/inactive).
    - Revoke (delete) keys.
    - Copy-to-clipboard buttons for usage snippets (JavaScript `fetch`, Python `requests`, `curl`) for the API key authenticated endpoints (`/gold`, `/silver`, `/palladium`).
- Uses `axios` for API calls and React Context API for authentication state management.

## Project Structure

```
.
├── api.py                  # FastAPI backend application
├── api_keys.db             # SQLite database (created on run)
├── requirements.txt        # Backend Python dependencies
├── start_api.sh            # Simple script to run the backend
├── frontend/               # React frontend application
│   ├── public/             # Static assets
│   ├── src/                # Frontend source code
│   │   ├── components/     # Reusable React components (Navbar)
│   │   ├── context/        # AuthContext for state management
│   │   ├── pages/          # Page components (Login, Register, Dashboard, ApiKeys)
│   │   ├── App.js          # Main application component with routing
│   │   ├── index.js        # Entry point for React app
│   │   └── config.js       # API base URL configuration
│   ├── package.json        # Frontend dependencies and scripts
│   └── ...
└── README.md               # This file
```

## Setup and Running

**Prerequisites:**
- Python 3.x
- Node.js and npm (or yarn)

**1. Backend Setup:**

   - Clone the repository (if you haven't already).
   - Navigate to the project root directory.
   - Create and activate a Python virtual environment (recommended):
     ```bash
     python -m venv venv
     # On Linux/macOS:
     source venv/bin/activate
     # On Windows:
     .\venv\Scripts\activate
     ```
   - Install backend dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the backend server:
     ```bash
     # Using the provided script (runs on port 8000 with reload)
     ./start_api.sh
     ```
     Alternatively, run directly with uvicorn:
     ```bash
     uvicorn api:app --reload --port 8000
     ```
     The API will be available at `http://localhost:8000`. The database `api_keys.db` will be created automatically on the first run.

**2. Frontend Setup:**

   - Navigate to the frontend directory:
     ```bash
     cd frontend
     ```
   - Install frontend dependencies:
     ```bash
     npm install
     # or: yarn install
     ```
   - Start the frontend development server:
     ```bash
     npm start
     # or: yarn start
     ```
     The frontend application should open automatically in your browser at `http://localhost:3000`.

## Usage

**Frontend Application:**

1.  Ensure both backend and frontend servers are running.
2.  Open `http://localhost:3000` in your browser.
3.  **Register:** Create a new user account.
4.  **Login:** Log in with your credentials.
5.  **Dashboard:** View your API key usage stats and the current prices for Gold, Silver, and Palladium.
6.  **API Keys Page:**
    - Generate one or more API keys. Only active keys can be used to access the API endpoints.
    - Toggle the status of keys if needed.
    - Copy usage snippets for your applications using the buttons provided.
    - Delete keys you no longer need.

**Direct API Access (using API Key):**

- Use an **active** API key generated via the frontend.
- Send requests to the `/gold`, `/silver`, or `/palladium` endpoints with the key in the `api-key` header.

   **Example `curl` commands (replace `<YOUR_ACTIVE_API_KEY>`):**
   ```bash
   # Get Gold Price
   curl -X GET "http://localhost:8000/gold" -H "api-key: <YOUR_ACTIVE_API_KEY>"

   # Get Silver Price
   curl -X GET "http://localhost:8000/silver" -H "api-key: <YOUR_ACTIVE_API_KEY>"

   # Get Palladium Price
   curl -X GET "http://localhost:8000/palladium" -H "api-key: <YOUR_ACTIVE_API_KEY>"
   ```

   **Example Python (`requests`) snippet:**
   ```python
   import requests

   api_key = "<YOUR_ACTIVE_API_KEY>"
   base_url = "http://localhost:8000"
   headers = {"api-key": api_key}

   try:
       response = requests.get(f"{base_url}/gold", headers=headers)
       response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
       data = response.json()
       print("Gold Price Data:", data)
   except requests.exceptions.RequestException as e:
       print(f"Error fetching gold price: {e}")
       if e.response is not None:
           print(f"Response status: {e.response.status_code}")
           try:
               print(f"Response body: {e.response.json()}")
           except ValueError: # Handle cases where response body is not JSON
               print(f"Response body: {e.response.text}")

   # Repeat for /silver and /palladium as needed
   ```

## License

MIT
