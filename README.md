# Gold Price API

A simple API to fetch real-time gold prices using Yahoo Finance API.

## Features

- Get current gold price
- Historical price data
- Automatic updates every minute

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn yfinance
   ```
3. Start the server:
   ```bash
   uvicorn api:app --reload
   ```

## API Endpoints

- `GET /` - Basic info
- `GET /gold` - Current gold price
- `GET /history` - Historical prices (last 100 records)

## License

MIT
