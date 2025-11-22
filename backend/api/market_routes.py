"""
Market data API endpoints.

Provides endpoints for fetching stock market data using Yahoo Finance.
"""

from flask import Blueprint, jsonify, request
from backend.utils.market_data import fetch_market_data, get_stock_info
import logging

market_bp = Blueprint('market', __name__)
logger = logging.getLogger(__name__)


@market_bp.route('/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    """
    Fetch historical stock data for a given ticker.
    
    Query Parameters:
        start: Start date (YYYY-MM-DD, default: 30 days ago)
        end: End date (YYYY-MM-DD, default: today)
        interval: Data interval (1d, 1wk, 1mo, default: 1d)
    
    Returns:
        JSON with stock data including OHLCV
    """
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        interval = request.args.get('interval', '1d')
        
        data = fetch_market_data(ticker, start_date, end_date, interval)
        
        if data is None or data.empty:
            return jsonify({'error': f'No data found for ticker {ticker}'}), 404
        
        # Convert DataFrame to dict for JSON response
        result = {
            'ticker': ticker,
            'data': data.to_dict('records'),
            'count': len(data)
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@market_bp.route('/stock/<ticker>/info', methods=['GET'])
def get_stock_information(ticker):
    """
    Get detailed information about a stock.
    
    Returns:
        JSON with stock info including company name, sector, etc.
    """
    try:
        info = get_stock_info(ticker)
        
        if not info:
            return jsonify({'error': f'No information found for ticker {ticker}'}), 404
        
        return jsonify(info), 200
        
    except Exception as e:
        logger.error(f"Error fetching info for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@market_bp.route('/search', methods=['GET'])
def search_stocks():
    """
    Search for stocks by symbol or name.
    
    Query Parameters:
        q: Search query
    
    Returns:
        JSON with matching stock symbols
    """
    query = request.args.get('q', '')
    
    if not query or len(query) < 1:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    # For now, return a simple list of common stocks that match
    # In production, this could use a proper stock search API
    common_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla, Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms, Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'WMT', 'name': 'Walmart Inc.'},
    ]
    
    query_upper = query.upper()
    results = [
        stock for stock in common_stocks
        if query_upper in stock['symbol'] or query_upper in stock['name'].upper()
    ]
    
    return jsonify({'results': results}), 200
