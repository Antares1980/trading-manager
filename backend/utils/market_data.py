"""
Market data utilities.

Provides functions for fetching stock market data from Yahoo Finance.
Falls back to mock data if Yahoo Finance is unavailable.
"""

import pandas as pd
from yahooquery import Ticker
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

# Use mock data if environment variable is set or Yahoo Finance fails
USE_MOCK_DATA = os.environ.get('USE_MOCK_DATA', 'False').lower() == 'true'


def fetch_market_data(ticker, start_date=None, end_date=None, interval='1d'):
    """
    Fetch historical market data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        end_date: End date (YYYY-MM-DD), defaults to today
        interval: Data interval (1d, 1wk, 1mo)
        
    Returns:
        DataFrame with OHLCV data
    """
    # Use mock data if enabled
    if USE_MOCK_DATA:
        from backend.utils.mock_data import generate_mock_stock_data
        logger.info(f"Using mock data for {ticker}")
        return generate_mock_stock_data(ticker, days=60)
    
    try:
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
        
        # Create Ticker object and fetch history
        t = Ticker(ticker, asynchronous=False)
        
        # Add one day to end_date to make it inclusive
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        end_str = end_dt.strftime('%Y-%m-%d')
        
        data = t.history(start=start_date, end=end_str, interval=interval)
        
        if isinstance(data, pd.DataFrame) and not data.empty:
            # Reset index to get date as a column
            data = data.reset_index()
            
            # Rename columns to lowercase for consistency
            data.rename(columns={
                'symbol': 'ticker',
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            # Select only needed columns
            columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            data = data[[col for col in columns if col in data.columns]]
            
            # Convert date to string format for JSON serialization
            if 'date' in data.columns:
                data['date'] = data['date'].dt.strftime('%Y-%m-%d')
            
            logger.info(f"Fetched {len(data)} rows for {ticker}")
            return data
        else:
            logger.warning(f"No data found for {ticker}")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        # Fallback to mock data if Yahoo Finance fails
        logger.info(f"Falling back to mock data for {ticker}")
        from backend.utils.mock_data import generate_mock_stock_data
        return generate_mock_stock_data(ticker, days=60)


def get_stock_info(ticker):
    """
    Get detailed information about a stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with stock information
    """
    # Use mock data if enabled
    if USE_MOCK_DATA:
        from backend.utils.mock_data import generate_mock_stock_info
        logger.info(f"Using mock info for {ticker}")
        return generate_mock_stock_info(ticker)
    
    try:
        logger.info(f"Fetching info for {ticker}")
        
        t = Ticker(ticker, asynchronous=False)
        
        # Get summary detail
        summary = t.summary_detail.get(ticker, {}) if hasattr(t, 'summary_detail') else {}
        
        # Get quote type for basic info
        quote_type = t.quote_type.get(ticker, {}) if hasattr(t, 'quote_type') else {}
        
        # Get price info
        price = t.price.get(ticker, {}) if hasattr(t, 'price') else {}
        
        info = {
            'symbol': ticker,
            'name': quote_type.get('longName', ticker),
            'exchange': quote_type.get('exchange', 'N/A'),
            'currency': price.get('currency', 'USD'),
            'current_price': price.get('regularMarketPrice', 0),
            'market_cap': summary.get('marketCap', 0),
            'volume': summary.get('volume', 0),
            'avg_volume': summary.get('averageVolume', 0),
            'pe_ratio': summary.get('trailingPE', 0),
            'dividend_yield': summary.get('dividendYield', 0),
        }
        
        logger.info(f"Retrieved info for {ticker}")
        return info
        
    except Exception as e:
        logger.error(f"Error fetching info for {ticker}: {str(e)}")
        # Fallback to mock data if Yahoo Finance fails
        logger.info(f"Falling back to mock info for {ticker}")
        from backend.utils.mock_data import generate_mock_stock_info
        return generate_mock_stock_info(ticker)
