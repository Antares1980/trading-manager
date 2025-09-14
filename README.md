# Stock Historical Price Fetcher

A Python CLI tool to fetch daily historical stock prices (OHLC: Open, High, Low, Close) for multiple stocks using Yahoo Finance.

## Setup

### 1. Create a Virtual Environment
To isolate dependencies, create a Python virtual environment:

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment
- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Prepare an input CSV file with a column named `ticker` containing stock symbols (e.g., AAPL, GOOGL).

Example input CSV (`stocks.csv`):
```
ticker
AAPL
GOOGL
MSFT
```

Run the script:
```bash
python stock_fetcher.py --input stocks.csv --output prices.csv --start 2023-01-01 --end 2023-12-31
```

- `--input`: Path to input CSV with tickers.
- `--output`: Path to output CSV for results.
- `--start`: Start date (YYYY-MM-DD, default: 2023-01-01).
- `--end`: End date (YYYY-MM-DD, default: today).

Output CSV will contain: Date, Ticker, Open, High, Low, Close, Volume.

## Notes
- Ensure Python 3.7+ is installed.
- Data is fetched from Yahoo Finance; check for rate limits or API changes.
- For issues, verify ticker symbols and date ranges.