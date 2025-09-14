#!/usr/bin/env python3
"""
Stock Historical Price Fetcher CLI

Fetches daily OHLC (Open, High, Low, Close) data for stocks listed in a CSV file
using Yahoo Finance API via yfinance library.

Usage:
    python stock_fetcher.py --input input_stocks.csv --output output_prices.csv --start 2023-01-01 --end 2023-12-31

Input CSV format: A single column named 'ticker' with stock symbols (e.g., AAPL, GOOGL).
Output CSV: Date, Ticker, Open, High, Low, Close, Volume.
"""

import argparse
import pandas as pd
from yahooquery import Ticker
from datetime import datetime
import logging
import time
import os
from contextlib import redirect_stdout, redirect_stderr


def fetch_stock_data(ticker, start_date, end_date):
    """Fetch daily OHLC data for a single ticker with retry logic."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logging.debug(f"Downloading data for {ticker} from {start_date} to {end_date} (attempt {attempt + 1})")
            
            t = Ticker(ticker, asynchronous=False)
            data = t.history(start=start_date, end=end_date, interval='1d')

            logging.debug(f"Data shape: {data.shape}, columns: {list(data.columns)}")
            if isinstance(data, pd.DataFrame) and data.empty:
                logging.warning(f"No data found for {ticker}")
                return pd.DataFrame()

            # Reset index to get 'symbol' and 'date' as columns
            data = data.reset_index()
            data.rename(columns={'symbol': 'Ticker', 'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            
            logging.debug(f"Successfully fetched {len(data)} rows for {ticker}")
            return data[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying {ticker} in 10 seconds...")
                time.sleep(10)
            else:
                logging.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
                return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="Fetch historical stock prices from Yahoo Finance.", add_help=False)
    parser.add_argument('--help', action='store_true', help='Show help message')
    parser.add_argument('--input', help='Path to input CSV file with tickers (column: ticker). Required.')
    parser.add_argument('--output', help='Path to output CSV file for results. Required.')
    parser.add_argument('--start', default='2023-01-01', help='Start date in YYYY-MM-DD format (default: 2023-01-01)')
    parser.add_argument('--end', default=datetime.today().strftime('%Y-%m-%d'), help='End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Set the logging level (default: INFO)')

    # Parse known args to check for --help
    args, unknown = parser.parse_known_args()
    if args.help or not args.input or not args.output:
        if args.help:
            print(parser.format_help())
            return
        else:
            parser.error("the following arguments are required: --input, --output")

    # Now parse fully since we have required args
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Suppress verbose logging from yfinance and related libraries
    logging.getLogger('yahooquery').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.info("Starting stock data fetcher")

    # Read input CSV
    try:
        tickers_df = pd.read_csv(args.input)
        if 'ticker' not in tickers_df.columns:
            logging.error("Input CSV must have a 'ticker' column.")
            return
        tickers = tickers_df['ticker'].dropna().unique()
        logging.info(f"Loaded {len(tickers)} unique tickers from {args.input}")
    except Exception as e:
        logging.error(f"Error reading input CSV: {e}")
        return

    # Fetch data for all tickers
    all_data = []
    for ticker in tickers:
        logging.info(f"Fetching data for {ticker}...")
        data = fetch_stock_data(ticker, args.start, args.end)
        if not data.empty:
            all_data.append(data)

    if not all_data:
        logging.warning("No data fetched. Check tickers and dates.")
        return

    # Combine and save
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv(args.output, index=False)
    logging.info(f"Data saved to {args.output} with {len(combined_df)} rows")

if __name__ == "__main__":
    main()