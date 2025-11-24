"""
Indicator API endpoints.

Provides operations for retrieving and managing technical indicators.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime
import logging

from backend.db import session_scope
from backend.models import Indicator, Asset, IndicatorType

indicator_bp = Blueprint('indicators', __name__)
logger = logging.getLogger(__name__)


@indicator_bp.route('/', methods=['GET'])
def list_indicators():
    """
    Get indicators with filtering options.
    
    Query Parameters:
        asset_id: Filter by asset ID (required)
        indicator_type: Filter by indicator type (sma, ema, rsi, etc.)
        name: Filter by indicator name
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        limit: Maximum number of results (default: 500)
        
    Returns:
        JSON with list of indicators
    """
    try:
        asset_id = request.args.get('asset_id')
        if not asset_id:
            return jsonify({'error': 'asset_id is required'}), 400
        
        indicator_type = request.args.get('indicator_type')
        name = request.args.get('name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 500))
        
        with session_scope() as session:
            # Verify asset exists
            asset = session.query(Asset).filter_by(id=asset_id).first()
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            # Build query
            query = session.query(Indicator).filter_by(asset_id=asset_id)
            
            # Apply filters
            if indicator_type:
                try:
                    query = query.filter_by(indicator_type=IndicatorType(indicator_type))
                except ValueError:
                    return jsonify({'error': 'Invalid indicator type'}), 400
            
            if name:
                query = query.filter_by(name=name)
            
            # Apply date filters
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Indicator.ts >= start_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Indicator.ts <= end_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
            
            # Order by timestamp and apply limit
            indicators = query.order_by(Indicator.ts.asc()).limit(limit).all()
            
            return jsonify({
                'indicators': [i.to_dict(include_timestamps=False) for i in indicators],
                'count': len(indicators),
                'asset': asset.to_dict(include_timestamps=False)
            }), 200
        
    except Exception as e:
        logger.error(f"List indicators error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@indicator_bp.route('/<int:indicator_id>', methods=['GET'])
def get_indicator(indicator_id):
    """
    Get a specific indicator by ID.
    
    Returns:
        JSON with indicator details
    """
    try:
        with session_scope() as session:
            indicator = session.query(Indicator).filter_by(id=indicator_id).first()
            
            if not indicator:
                return jsonify({'error': 'Indicator not found'}), 404
            
            return jsonify({
                'indicator': indicator.to_dict(include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get indicator error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@indicator_bp.route('/', methods=['POST'])
@jwt_required()
def create_indicator():
    """
    Create a new indicator entry.
    
    Request Body:
        asset_id: Asset ID (required)
        ts: Timestamp (ISO format, required)
        indicator_type: Type (sma, ema, rsi, etc., required)
        name: Indicator name (required)
        value: Primary value (required)
        value2: Secondary value (optional)
        value3: Tertiary value (optional)
        parameters: Parameters as JSON (optional)
        timeframe: Timeframe (default: '1d')
        
    Returns:
        JSON with created indicator
    """
    try:
        data = request.get_json()
        
        required_fields = ['asset_id', 'ts', 'indicator_type', 'name', 'value']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Required fields: asset_id, ts, indicator_type, name, value'}), 400
        
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
            
            # Parse indicator type
            try:
                indicator_type = IndicatorType(data['indicator_type'])
            except ValueError:
                return jsonify({'error': 'Invalid indicator type'}), 400
            
            # Create indicator
            indicator = Indicator(
                asset_id=data['asset_id'],
                ts=ts,
                indicator_type=indicator_type,
                name=data['name'],
                value=data['value'],
                value2=data.get('value2'),
                value3=data.get('value3'),
                parameters=data.get('parameters', {}),
                timeframe=data.get('timeframe', '1d')
            )
            
            session.add(indicator)
            session.commit()
            
            return jsonify({
                'message': 'Indicator created successfully',
                'indicator': indicator.to_dict()
            }), 201
        
    except Exception as e:
        logger.error(f"Create indicator error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@indicator_bp.route('/types', methods=['GET'])
def list_indicator_types():
    """
    Get all available indicator types.
    
    Returns:
        JSON with list of indicator types
    """
    try:
        types = [{'value': t.value, 'name': t.name} for t in IndicatorType]
        
        return jsonify({
            'indicator_types': types,
            'count': len(types)
        }), 200
        
    except Exception as e:
        logger.error(f"List indicator types error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
