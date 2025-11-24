"""
Mock data utilities for development/testing when Yahoo Finance is unavailable.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_mock_stock_data(ticker, days=30):
    """
    Generate mock stock data for testing.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of data to generate
        
    Returns:
        DataFrame with OHLCV data
    """
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate mock price data with some randomness
    base_price = 100.0  # Starting price
    np.random.seed(hash(ticker) % 2**32)  # Consistent data for same ticker
    
    prices = []
    current_price = base_price
    
    for i in range(len(dates)):
        # Random walk with trend
        change_percent = np.random.normal(0.002, 0.02)  # Mean: 0.2% daily gain, StdDev: 2%
        current_price = current_price * (1 + change_percent)
        prices.append(current_price)
    
    prices = np.array(prices)
    
    # Generate OHLC data
    data = []
    for i, date in enumerate(dates):
        price = prices[i]
        # High is up to 2% above close
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        # Low is up to 2% below close
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        # Open is between low and high
        open_price = low + (high - low) * np.random.random()
        # Volume is random between 1M and 100M
        volume = int(np.random.uniform(1_000_000, 100_000_000))
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(price, 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)


def generate_mock_stock_info(ticker):
    """
    Generate mock stock information.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with stock information
    """
    # Mock company names
    company_names = {
        'AAPL': 'Apple Inc.',
        'GOOGL': 'Alphabet Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla, Inc.',
        'META': 'Meta Platforms, Inc.',
        'NVDA': 'NVIDIA Corporation',
        'JPM': 'JPMorgan Chase & Co.',
        'V': 'Visa Inc.',
        'WMT': 'Walmart Inc.',
    }
    
    np.random.seed(hash(ticker) % 2**32)
    
    # Generate mock data
    current_price = round(np.random.uniform(50, 500), 2)
    
    return {
        'symbol': ticker,
        'name': company_names.get(ticker, f'{ticker} Corporation'),
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'current_price': current_price,
        'market_cap': int(current_price * np.random.uniform(1e9, 1e12)),
        'volume': int(np.random.uniform(1_000_000, 100_000_000)),
        'avg_volume': int(np.random.uniform(5_000_000, 50_000_000)),
        'pe_ratio': round(np.random.uniform(10, 50), 2),
        'dividend_yield': round(np.random.uniform(0, 0.05), 4),
    }
