"""
Technical analysis utilities.

Provides functions for calculating technical indicators using the 'ta' library.
"""

import pandas as pd
import ta
from backend.utils.market_data import fetch_market_data
import logging

logger = logging.getLogger(__name__)


def calculate_indicators(ticker, start_date=None, end_date=None, indicators=None):
    """
    Calculate technical indicators for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        indicators: List of indicator names to calculate
                   (sma, ema, rsi, macd, bbands, atr, obv)
        
    Returns:
        Dict with original data and calculated indicators
    """
    if indicators is None:
        indicators = ['sma', 'rsi']
    
    try:
        # Fetch market data
        df = fetch_market_data(ticker, start_date, end_date)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {ticker}")
            return None
        
        # Convert date back to datetime for calculations
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate requested indicators
        for indicator in indicators:
            indicator = indicator.lower()
            
            if indicator == 'sma':
                _add_sma(df)
            elif indicator == 'ema':
                _add_ema(df)
            elif indicator == 'rsi':
                _add_rsi(df)
            elif indicator == 'macd':
                _add_macd(df)
            elif indicator == 'bbands':
                _add_bollinger_bands(df)
            elif indicator == 'atr':
                _add_atr(df)
            elif indicator == 'obv':
                _add_obv(df)
            else:
                logger.warning(f"Unknown indicator: {indicator}")
        
        # Convert date back to string for JSON serialization
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Replace NaN with None for JSON serialization
        df = df.where(pd.notna(df), None)
        
        result = {
            'ticker': ticker,
            'data': df.to_dict('records'),
            'indicators': indicators
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating indicators for {ticker}: {str(e)}")
        return None


def _add_sma(df, periods=[20, 50]):
    """Add Simple Moving Average indicators."""
    for period in periods:
        df[f'sma_{period}'] = ta.trend.sma_indicator(df['close'], window=period)


def _add_ema(df, periods=[20, 50]):
    """Add Exponential Moving Average indicators."""
    for period in periods:
        df[f'ema_{period}'] = ta.trend.ema_indicator(df['close'], window=period)


def _add_rsi(df, period=14):
    """Add Relative Strength Index."""
    df['rsi'] = ta.momentum.rsi(df['close'], window=period)


def _add_macd(df):
    """Add MACD (Moving Average Convergence Divergence) indicator."""
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()


def _add_bollinger_bands(df, period=20, std=2):
    """Add Bollinger Bands."""
    bollinger = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std)
    df['bb_upper'] = bollinger.bollinger_hband()
    df['bb_middle'] = bollinger.bollinger_mavg()
    df['bb_lower'] = bollinger.bollinger_lband()
    df['bb_width'] = bollinger.bollinger_wband()


def _add_atr(df, period=14):
    """Add Average True Range."""
    df['atr'] = ta.volatility.average_true_range(
        df['high'], df['low'], df['close'], window=period
    )


def _add_obv(df):
    """Add On-Balance Volume."""
    df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])


def get_trend_signal(df):
    """
    Analyze the trend based on moving averages.
    
    Returns:
        String: 'bullish', 'bearish', or 'neutral'
    """
    if df.empty or 'sma_20' not in df.columns or 'sma_50' not in df.columns:
        return 'neutral'
    
    latest = df.iloc[-1]
    
    if pd.isna(latest['sma_20']) or pd.isna(latest['sma_50']):
        return 'neutral'
    
    if latest['sma_20'] > latest['sma_50']:
        return 'bullish'
    elif latest['sma_20'] < latest['sma_50']:
        return 'bearish'
    else:
        return 'neutral'


def get_momentum_signal(df):
    """
    Analyze momentum based on RSI.
    
    Returns:
        String: 'overbought', 'oversold', or 'neutral'
    """
    if df.empty or 'rsi' not in df.columns:
        return 'neutral'
    
    latest_rsi = df.iloc[-1]['rsi']
    
    if pd.isna(latest_rsi):
        return 'neutral'
    
    if latest_rsi > 70:
        return 'overbought'
    elif latest_rsi < 30:
        return 'oversold'
    else:
        return 'neutral'
