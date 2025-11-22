#!/usr/bin/env python3
"""
Trading Manager CLI

Fetches daily OHLC (Open, High, Low, Close) data and optionally current or historical quarterly fundamentals
for stocks listed in a CSV file using Yahoo Finance API via yahooquery library.

Usage:
    python trading_manager_cli.py --input input_stocks.csv --output output_prices.csv --start 2023-01-01 --end 2023-12-31 [--fundamentals] [--quarterly-fundamentals]

Input CSV format: A single column named 'ticker' with stock symbols (e.g., AAPL, GOOGL).
Output CSV: Date, Ticker, Open, High, Low, Close, Volume[, P/E, EPS, ROE, Dividend_Yield if --fundamentals][, all quarterly fundamentals if --quarterly-fundamentals].
"""

import argparse
import pandas as pd
from yahooquery import Ticker
from datetime import datetime
import logging
import time
import os
from contextlib import redirect_stdout, redirect_stderr


def fetch_stock_data(ticker, start_date, end_date, include_fundamentals=False, include_quarterly=False):
    """Fetch daily OHLC data for a single ticker with retry logic. Optionally include current or quarterly fundamentals."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logging.debug(f"Downloading data for {ticker} from {start_date} to {end_date} (attempt {attempt + 1})")
            
            t = Ticker(ticker, asynchronous=False)
            # Adjust end_date to be inclusive by adding one day
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            start_str = start_dt.strftime('%Y-%m-%d')
            end_str = end_dt.strftime('%Y-%m-%d')
            data = t.history(start=start_str, end=end_str, interval='1d')

            logging.debug(f"Data shape: {data.shape}, columns: {list(data.columns)}")
            if isinstance(data, pd.DataFrame) and data.empty:
                logging.warning(f"No data found for {ticker}")
                return pd.DataFrame()

            # Reset index to get 'symbol' and 'date' as columns
            data = data.reset_index()
            data.rename(columns={'symbol': 'Ticker', 'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            
            # Fetch current fundamentals if requested
            if include_fundamentals:
                try:
                    logging.debug(f"Fetching current fundamentals for {ticker}")
                    key_stats = t.key_stats
                    summary_detail = t.summary_detail
                    
                    logging.debug(f"key_stats keys: {list(key_stats.keys()) if key_stats else 'None'}")
                    logging.debug(f"summary_detail keys: {list(summary_detail.keys()) if summary_detail else 'None'}")
                    
                    # Extract specific metrics (nested under ticker key)
                    ticker_key = list(key_stats.keys())[0] if key_stats else None
                    summary_key = list(summary_detail.keys())[0] if summary_detail else None
                    
                    if ticker_key and ticker_key in key_stats:
                        inner_key_stats = key_stats[ticker_key]
                        eps = inner_key_stats.get('trailingEps', None)
                        roe = inner_key_stats.get('returnOnEquity', None)  # May not be available
                    else:
                        eps = roe = None
                    
                    if summary_key and summary_key in summary_detail:
                        inner_summary = summary_detail[summary_key]
                        pe = inner_summary.get('trailingPE', None)
                        dividend_yield = inner_summary.get('dividendYield', None)
                    else:
                        pe = dividend_yield = None
                    
                    # Add as new columns (same value for all rows of this ticker)
                    data['P/E'] = pe
                    data['EPS'] = eps
                    data['ROE'] = roe
                    data['Dividend_Yield'] = dividend_yield
                    
                    logging.debug(f"Current fundamentals for {ticker}: P/E={pe}, EPS={eps}, ROE={roe}, Dividend_Yield={dividend_yield}")
                except Exception as e:
                    logging.warning(f"Failed to fetch current fundamentals for {ticker}: {e}")
                    # Add NaN columns if fetch fails
                    data['P/E'] = None
                    data['EPS'] = None
                    data['ROE'] = None
                    data['Dividend_Yield'] = None
            
            # Fetch historical quarterly fundamentals if requested
            if include_quarterly:
                try:
                    logging.debug(f"Fetching historical quarterly fundamentals for {ticker}")
                    # Get quarterly earnings (historical EPS, revenue, net income)
                    quarterly_earnings = t.income_statement(frequency='quarterly')
                    logging.debug(f"Quarterly earnings shape: {quarterly_earnings.shape if hasattr(quarterly_earnings, 'shape') else 'Not a DataFrame'}")
                    if hasattr(quarterly_earnings, 'empty') and not quarterly_earnings.empty:
                        quarterly_earnings = quarterly_earnings.reset_index()
                        logging.debug(f"Quarterly earnings after reset_index head: {quarterly_earnings.head()}")
                        logging.debug(f"Quarterly earnings columns: {quarterly_earnings.columns}")
                        quarterly_earnings.rename(columns={
                            'TotalRevenue': 'Quarterly_Revenue',
                            'BasicEPS': 'Quarterly_EPS',
                            quarterly_earnings.columns[1]: 'Quarter_Date'  # Assuming second column is date after reset_index
                        }, inplace=True)
                        # Ensure date columns are datetime
                        data['Date'] = pd.to_datetime(data['Date'])
                        quarterly_earnings['Quarter_Date'] = pd.to_datetime(quarterly_earnings['Quarter_Date'])
                        # Merge quarterly data with daily data (forward fill to align dates)
                        data = pd.merge_asof(data.sort_values('Date'), quarterly_earnings.sort_values('Quarter_Date'),
                                           left_on='Date', right_on='Quarter_Date', direction='backward')
                        data.drop(columns=['Quarter_Date'], inplace=True)
                        # Drop symbol column if present to avoid duplicate
                        if 'symbol' in data.columns:
                            data.drop(columns=['symbol'], inplace=True)
                    else:
                        logging.warning(f"No quarterly earnings data for {ticker}")
                        data['Quarterly_EPS'] = None
                        data['Quarterly_Revenue'] = None

                    # Optionally add more fundamentals (e.g., balance sheet), but keep it simple for now
                    # Example: quarterly_balance_sheet = t.quarterly_balance_sheet

                except Exception as e:
                    logging.warning(f"Failed to fetch historical quarterly fundamentals for {ticker}: {e}")
                    data['Quarterly_EPS'] = None
                    data['Quarterly_Revenue'] = None
            
            logging.debug(f"Successfully fetched {len(data)} rows for {ticker}")
            columns = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
            if include_fundamentals:
                columns.extend(['P/E', 'EPS', 'ROE', 'Dividend_Yield'])
            if include_quarterly:
                # Add all quarterly columns (already renamed key ones)
                quarterly_cols = [col for col in data.columns if col not in columns and col != 'Adj Close' and col != 'Dividends']  # Assuming quarterly cols are the new ones
                columns.extend(quarterly_cols)
            return data[columns]
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying {ticker} in 10 seconds...")
                time.sleep(10)
            else:
                logging.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
                return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="Trading Manager CLI for fetching historical prices and fundamentals.", add_help=False)
    parser.add_argument('--help', action='store_true', help='Show help message')
    parser.add_argument('--input', help='Path to input CSV file with tickers (column: ticker). Required.')
    parser.add_argument('--output', help='Path to output CSV file for results. Required.')
    parser.add_argument('--start', default='2023-01-01', help='Start date in YYYY-MM-DD format (default: 2023-01-01)')
    parser.add_argument('--end', default=datetime.today().strftime('%Y-%m-%d'), help='End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--fundamentals', action='store_true', help='Include current fundamental indicators (P/E, EPS, ROE, Dividend Yield) in the output')
    parser.add_argument('--quarterly-fundamentals', action='store_true', help='Include historical quarterly fundamentals (EPS, Revenue) merged with daily data')
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
    # Suppress verbose logging from yahooquery and related libraries
    logging.getLogger('yahooquery').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.info("Starting Trading Manager CLI")

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
        data = fetch_stock_data(ticker, args.start, args.end, args.fundamentals, args.quarterly_fundamentals)
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