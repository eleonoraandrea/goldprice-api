# Gold Price API with User Authentication and Key Management

This project provides a FastAPI backend and a React frontend for fetching real-time gold prices, secured by user authentication and API key management.

## Features

**Backend (FastAPI):**
- Fetches real-time gold prices using `yfinance`.
- User registration and login using JWT authentication.
- Secure API key generation, management (toggle status, revoke), and usage tracking per user.
- `/gold` endpoint protected by API key authentication (`api-key` header).
- SQLite database for storing user credentials and API keys.
- CORS configured for the React frontend (localhost:3000).

**Frontend (React):**
- User registration and login forms.
- Dashboard page (currently basic).
- API Key management page:
    - View existing keys with status, creation date, last used date.
    - Create new API keys.
    - Toggle key status (active/inactive).
    - Revoke keys.
    - Copy-to-clipboard buttons for usage snippets (JavaScript `fetch`, Python `requests`, `curl`).
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

**1. Backend Setup:**

   - Ensure you have Python 3 installed.
   - Create a virtual environment (recommended):
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
     ```
   - Install backend dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the backend server:
     ```bash
     # Using the script
     ./start_api.sh
     # Or directly with uvicorn
     # uvicorn api:app --reload --port 8000
     ```
     The API will be available at `http://localhost:8000`.

**2. Frontend Setup:**

   - Ensure you have Node.js and npm installed.
   - Navigate to the frontend directory:
     ```bash
     cd frontend
     ```
   - Install frontend dependencies:
     ```bash
     npm install
     ```
   - Start the frontend development server:
     ```bash
     npm start
     ```
     The frontend application will open automatically in your browser at `http://localhost:3000`.

## Usage

1.  Start both the backend and frontend servers.
2.  Open `http://localhost:3000` in your browser.
3.  Register a new user or log in with existing credentials.
4.  Navigate to the "API Keys" page.
5.  Create an API key.
6.  Use the copy buttons to get code snippets (JS, Python, Curl) for accessing the `/gold` endpoint.
7.  Example `curl` command (replace `<YOUR_API_KEY>`):
    ```bash
    curl -X GET "http://localhost:8000/gold" -H "api-key: <YOUR_API_KEY>"
    ```

## License

MIT
