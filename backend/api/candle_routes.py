"""
Candle (OHLCV) API endpoints.

Provides operations for retrieving and managing candlestick data.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone
import logging

from backend.db import session_scope
from backend.models import Candle, Asset, CandleInterval
from sqlalchemy import and_, desc

candle_bp = Blueprint('candles', __name__)
logger = logging.getLogger(__name__)


@candle_bp.route('/', methods=['GET'])
def list_candles():
    """
    Get candles with filtering options.
    
    Query Parameters:
        asset_id: Filter by asset ID (required)
        interval: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        limit: Maximum number of results (default: 1000)
        
    Returns:
        JSON with list of candles
    """
    try:
        asset_id = request.args.get('asset_id')
        if not asset_id:
            return jsonify({'error': 'asset_id is required'}), 400
        
        interval = request.args.get('interval', '1d')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        
        with session_scope() as session:
            # Verify asset exists
            asset = session.query(Asset).filter_by(id=asset_id).first()
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            # Build query
            query = session.query(Candle).filter_by(asset_id=asset_id)
            
            # Apply interval filter
            try:
                query = query.filter_by(interval=CandleInterval(interval))
            except ValueError:
                return jsonify({'error': 'Invalid interval'}), 400
            
            # Apply date filters
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Candle.ts >= start_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Candle.ts <= end_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
            
            # Order by timestamp and apply limit
            candles = query.order_by(Candle.ts.asc()).limit(limit).all()
            
            return jsonify({
                'candles': [c.to_dict(include_timestamps=False) for c in candles],
                'count': len(candles),
                'asset': asset.to_dict(include_timestamps=False)
            }), 200
        
    except Exception as e:
        logger.error(f"List candles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@candle_bp.route('/<int:candle_id>', methods=['GET'])
def get_candle(candle_id):
    """
    Get a specific candle by ID.
    
    Returns:
        JSON with candle details
    """
    try:
        with session_scope() as session:
            candle = session.query(Candle).filter_by(id=candle_id).first()
            
            if not candle:
                return jsonify({'error': 'Candle not found'}), 404
            
            return jsonify({
                'candle': candle.to_dict(include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get candle error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@candle_bp.route('/', methods=['POST'])
@jwt_required()
def create_candle():
    """
    Create a new candle entry.
    
    Request Body:
        asset_id: Asset ID (required)
        ts: Timestamp (ISO format, required)
        interval: Interval (1d, 1h, etc., default: 1d)
        open: Opening price (required)
        high: High price (required)
        low: Low price (required)
        close: Closing price (required)
        volume: Trading volume (default: 0)
        trades: Number of trades
        vwap: Volume-weighted average price
        source: Data source (default: 'manual')
        
    Returns:
        JSON with created candle
    """
    try:
        data = request.get_json()
        
        required_fields = ['asset_id', 'ts', 'open', 'high', 'low', 'close']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Required fields: asset_id, ts, open, high, low, close'}), 400
        
        with session_scope() as session:
            # Verify asset exists
            asset = session.query(Asset).filter_by(id=data['asset_id']).first()
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            # Parse timestamp
            try:
                ts = datetime.fromisoformat(data['ts'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format'}), 400
            
            # Parse interval
            interval = CandleInterval.DAY_1
            if 'interval' in data:
                try:
                    interval = CandleInterval(data['interval'])
                except ValueError:
                    return jsonify({'error': 'Invalid interval'}), 400
            
            # Create candle
            candle = Candle(
                asset_id=data['asset_id'],
                ts=ts,
                interval=interval,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data.get('volume', 0),
                trades=data.get('trades'),
                vwap=data.get('vwap'),
                source=data.get('source', 'manual')
            )
            
            session.add(candle)
            session.commit()
            
            return jsonify({
                'message': 'Candle created successfully',
                'candle': candle.to_dict()
            }), 201
        
    except Exception as e:
        logger.error(f"Create candle error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@candle_bp.route('/latest', methods=['GET'])
def get_latest_candles():
    """
    Get the latest candle for each asset.
    
    Query Parameters:
        interval: Candle interval (default: 1d)
        asset_ids: Comma-separated list of asset IDs (optional)
        
    Returns:
        JSON with latest candles
    """
    try:
        interval = request.args.get('interval', '1d')
        asset_ids_str = request.args.get('asset_ids')
        
        with session_scope() as session:
            # Parse interval
            try:
                candle_interval = CandleInterval(interval)
            except ValueError:
                return jsonify({'error': 'Invalid interval'}), 400
            
            # Build base query
            query = session.query(Candle).filter_by(interval=candle_interval)
            
            # Filter by asset IDs if provided
            if asset_ids_str:
                asset_ids = [aid.strip() for aid in asset_ids_str.split(',')]
                query = query.filter(Candle.asset_id.in_(asset_ids))
            
            # Get latest candle for each asset (simplified approach)
            # In production, use a subquery or window function for efficiency
            candles_by_asset = {}
            for candle in query.order_by(desc(Candle.ts)).all():
                if candle.asset_id not in candles_by_asset:
                    candles_by_asset[candle.asset_id] = candle
            
            candles = list(candles_by_asset.values())
            
            return jsonify({
                'candles': [c.to_dict(include_timestamps=True) for c in candles],
                'count': len(candles)
            }), 200
        
    except Exception as e:
        logger.error(f"Get latest candles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
