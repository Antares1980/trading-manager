"""
Technical analysis API endpoints.

Provides endpoints for calculating technical indicators using the 'ta' library.
"""

from flask import Blueprint, jsonify, request
from backend.utils.technical_analysis import calculate_indicators
import logging
import json
import math

analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)


def safe_jsonify(data):
    """Convert data to JSON, replacing NaN and inf with None."""
    def convert_value(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        return obj
    
    def recursive_convert(data):
        if isinstance(data, dict):
            return {k: recursive_convert(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [recursive_convert(item) for item in data]
        else:
            return convert_value(data)
    
    return jsonify(recursive_convert(data))


@analysis_bp.route('/indicators/<ticker>', methods=['GET'])
def get_technical_indicators(ticker):
    """
    Calculate technical indicators for a given ticker.
    
    Query Parameters:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        indicators: Comma-separated list of indicators (sma,ema,rsi,macd,bbands)
        
    Returns:
        JSON with calculated technical indicators
    """
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        indicators_param = request.args.get('indicators', 'sma,rsi')
        
        # Parse indicators list
        indicators = [i.strip().lower() for i in indicators_param.split(',')]
        
        result = calculate_indicators(ticker, start_date, end_date, indicators)
        
        if result is None:
            return jsonify({'error': f'Could not calculate indicators for {ticker}'}), 500
        
        return safe_jsonify(result), 200
        
    except ValueError as e:
        logger.warning(f"Invalid request for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculating indicators for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/summary/<ticker>', methods=['GET'])
def get_analysis_summary(ticker):
    """
    Get a summary of technical analysis for a ticker.
    
    Returns:
        JSON with key technical indicators and signals
    """
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Calculate common indicators
        indicators = ['sma', 'ema', 'rsi', 'macd', 'bbands']
        result = calculate_indicators(ticker, start_date, end_date, indicators)
        
        if result is None:
            return jsonify({'error': f'Could not analyze {ticker}'}), 500
        
        # Generate summary with latest values and signals
        data = result['data']
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        latest = data[-1]
        
        summary = {
            'ticker': ticker,
            'latest_close': latest.get('close'),
            'date': latest.get('date'),
            'indicators': {
                'rsi': latest.get('rsi'),
                'macd': latest.get('macd'),
                'macd_signal': latest.get('macd_signal'),
                'sma_20': latest.get('sma_20'),
                'ema_20': latest.get('ema_20'),
                'bb_upper': latest.get('bb_upper'),
                'bb_middle': latest.get('bb_middle'),
                'bb_lower': latest.get('bb_lower'),
            },
            'signals': _generate_signals(latest)
        }
        
        return safe_jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error generating summary for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _generate_signals(latest_data):
    """Generate trading signals based on technical indicators."""
    signals = []
    
    # RSI signals
    rsi = latest_data.get('rsi')
    if rsi:
        if rsi < 30:
            signals.append({'type': 'RSI', 'signal': 'oversold', 'value': rsi})
        elif rsi > 70:
            signals.append({'type': 'RSI', 'signal': 'overbought', 'value': rsi})
    
    # MACD signals
    macd = latest_data.get('macd')
    macd_signal = latest_data.get('macd_signal')
    if macd and macd_signal:
        if macd > macd_signal:
            signals.append({'type': 'MACD', 'signal': 'bullish', 'value': macd - macd_signal})
        else:
            signals.append({'type': 'MACD', 'signal': 'bearish', 'value': macd - macd_signal})
    
    # Bollinger Bands signals
    close = latest_data.get('close')
    bb_upper = latest_data.get('bb_upper')
    bb_lower = latest_data.get('bb_lower')
    if close and bb_upper and bb_lower:
        if close > bb_upper:
            signals.append({'type': 'Bollinger Bands', 'signal': 'overbought', 'value': close})
        elif close < bb_lower:
            signals.append({'type': 'Bollinger Bands', 'signal': 'oversold', 'value': close})
    
    return signals
