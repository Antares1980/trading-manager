"""
Dashboard API endpoints.

Provides dashboard summary data including watchlist summaries and market indices.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging

from backend.db import session_scope
from backend.models import User, Watchlist, WatchlistItem, Asset, Candle

dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)


def calculate_percentage_change(current_price, previous_price):
    """Calculate percentage change between two prices."""
    if previous_price is None or previous_price == 0:
        return None
    return float((current_price - previous_price) / previous_price * 100)


def get_price_at_date(session, asset_id, target_date, interval='1d'):
    """Get the closing price of an asset at or before a target date."""
    candle = session.query(Candle).filter(
        Candle.asset_id == asset_id,
        Candle.interval == interval,
        Candle.ts <= target_date
    ).order_by(Candle.ts.desc()).first()
    
    if candle:
        return float(candle.close)
    return None


def get_moving_average(session, asset_id, days, interval='1d'):
    """Calculate moving average for an asset."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days * 2)  # Get extra data for calculation
    
    candles = session.query(Candle).filter(
        Candle.asset_id == asset_id,
        Candle.interval == interval,
        Candle.ts >= start_date
    ).order_by(Candle.ts.desc()).limit(days).all()
    
    if len(candles) < days:
        return None
    
    prices = [float(c.close) for c in candles[:days]]
    return sum(prices) / len(prices)


def get_sparkline_data(session, asset_id, days=30, interval='1d'):
    """Get sparkline data (closing prices) for the last N days."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    candles = session.query(Candle).filter(
        Candle.asset_id == asset_id,
        Candle.interval == interval,
        Candle.ts >= start_date
    ).order_by(Candle.ts.asc()).all()
    
    return [float(c.close) for c in candles]


@dashboard_bp.route('/watchlist-summary', methods=['GET'])
@jwt_required()
def get_watchlist_summary():
    """
    Get watchlist summary with asset data and percentage changes.
    
    Returns:
        JSON with:
        - assets: List of assets with symbol, name, price, and percentage changes
        - watchlist_index: Overall normalized index of the watchlist
        - watchlist_info: Basic watchlist information
    """
    try:
        user_id = get_jwt_identity()
        now = datetime.now(timezone.utc)
        
        with session_scope() as session:
            # Get user's default watchlist
            watchlist = session.query(Watchlist).filter_by(
                user_id=user_id,
                is_default='true'
            ).first()
            
            # If no default watchlist, get the first one
            if not watchlist:
                watchlist = session.query(Watchlist).filter_by(
                    user_id=user_id
                ).first()
            
            # If still no watchlist, return empty response
            if not watchlist:
                return jsonify({
                    'success': True,
                    'assets': [],
                    'watchlist_index': None,
                    'watchlist_info': None,
                    'message': 'No watchlist found. Create a watchlist to see your dashboard.'
                }), 200
            
            # Get watchlist items with their assets
            items = session.query(WatchlistItem).filter_by(
                watchlist_id=watchlist.id
            ).order_by(WatchlistItem.position).all()
            
            if not items:
                return jsonify({
                    'success': True,
                    'assets': [],
                    'watchlist_index': None,
                    'watchlist_info': {
                        'id': watchlist.id,
                        'name': watchlist.name,
                        'description': watchlist.description,
                        'item_count': 0
                    },
                    'message': 'Watchlist is empty. Add assets to see your dashboard.'
                }), 200
            
            # Calculate date references
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(days=7)
            one_month_ago = now - timedelta(days=30)
            one_year_ago = now - timedelta(days=365)
            
            # Process each asset
            assets_data = []
            normalized_values = []
            
            for item in items:
                asset = item.asset
                if not asset:
                    continue
                
                # Get latest price
                latest_candle = session.query(Candle).filter(
                    Candle.asset_id == asset.id,
                    Candle.interval == '1d'
                ).order_by(Candle.ts.desc()).first()
                
                if not latest_candle:
                    # No candle data available
                    assets_data.append({
                        'symbol': asset.symbol,
                        'name': asset.name,
                        'asset_type': asset.asset_type,
                        'last_price': None,
                        'change_1d': None,
                        'change_1w': None,
                        'change_1m': None,
                        'change_1y': None,
                        'sparkline': [],
                        'data_status': 'no_data'
                    })
                    continue
                
                current_price = float(latest_candle.close)
                
                # Get historical prices
                price_1d = get_price_at_date(session, asset.id, one_day_ago)
                price_1w = get_price_at_date(session, asset.id, one_week_ago)
                price_1m = get_price_at_date(session, asset.id, one_month_ago)
                price_1y = get_price_at_date(session, asset.id, one_year_ago)
                
                # Calculate percentage changes
                change_1d = calculate_percentage_change(current_price, price_1d)
                change_1w = calculate_percentage_change(current_price, price_1w)
                change_1m = calculate_percentage_change(current_price, price_1m)
                change_1y = calculate_percentage_change(current_price, price_1y)
                
                # Get sparkline data
                sparkline = get_sparkline_data(session, asset.id)
                
                # Calculate 200-day moving average for index normalization
                ma_200 = get_moving_average(session, asset.id, 200)
                if ma_200 and ma_200 > 0:
                    normalized_value = current_price / ma_200
                    normalized_values.append(normalized_value)
                
                assets_data.append({
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'asset_type': asset.asset_type,
                    'sector': asset.sector,
                    'industry': asset.industry,
                    'last_price': round(current_price, 2),
                    'last_updated': latest_candle.ts.isoformat() if latest_candle.ts else None,
                    'change_1d': round(change_1d, 2) if change_1d is not None else None,
                    'change_1w': round(change_1w, 2) if change_1w is not None else None,
                    'change_1m': round(change_1m, 2) if change_1m is not None else None,
                    'change_1y': round(change_1y, 2) if change_1y is not None else None,
                    'sparkline': sparkline,
                    'data_status': 'ok'
                })
            
            # Calculate watchlist index (average of normalized values)
            watchlist_index = None
            if normalized_values:
                watchlist_index = round(sum(normalized_values) / len(normalized_values) * 100, 2)
            
            return jsonify({
                'success': True,
                'assets': assets_data,
                'watchlist_index': watchlist_index,
                'watchlist_info': {
                    'id': watchlist.id,
                    'name': watchlist.name,
                    'description': watchlist.description,
                    'item_count': len(assets_data)
                },
                'generated_at': now.isoformat()
            }), 200
    
    except Exception as e:
        logger.error(f"Error getting watchlist summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve watchlist summary',
            'message': str(e)
        }), 500


@dashboard_bp.route('/quick-stats', methods=['GET'])
@jwt_required()
def get_quick_stats():
    """
    Get quick statistics for dashboard overview.
    
    Returns:
        JSON with quick stats like top gainers, losers, and market summary.
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            # Get user's watchlist count
            watchlist_count = session.query(Watchlist).filter_by(
                user_id=user_id
            ).count()
            
            # Get total tracked assets
            asset_count = session.query(WatchlistItem).join(
                Watchlist
            ).filter(
                Watchlist.user_id == user_id
            ).count()
            
            return jsonify({
                'success': True,
                'stats': {
                    'watchlist_count': watchlist_count,
                    'asset_count': asset_count,
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
            }), 200
    
    except Exception as e:
        logger.error(f"Error getting quick stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve quick stats'
        }), 500
