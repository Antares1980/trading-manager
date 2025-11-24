"""
Signal API endpoints.

Provides operations for retrieving and managing trading signals.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime
import logging

from backend.db import session_scope
from backend.models import Signal, Asset, SignalType, SignalStrength

signal_bp = Blueprint('signals', __name__)
logger = logging.getLogger(__name__)


@signal_bp.route('/', methods=['GET'])
def list_signals():
    """
    Get signals with filtering options.
    
    Query Parameters:
        asset_id: Filter by asset ID (optional)
        signal_type: Filter by signal type (buy, sell, hold, etc.)
        is_active: Filter by active status ('true' or 'false')
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        limit: Maximum number of results (default: 100)
        
    Returns:
        JSON with list of signals
    """
    try:
        asset_id = request.args.get('asset_id')
        signal_type = request.args.get('signal_type')
        is_active = request.args.get('is_active')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        with session_scope() as session:
            # Build query
            query = session.query(Signal)
            
            # Apply filters
            if asset_id:
                # Verify asset exists
                asset = session.query(Asset).filter_by(id=asset_id).first()
                if not asset:
                    return jsonify({'error': 'Asset not found'}), 404
                query = query.filter_by(asset_id=asset_id)
            
            if signal_type:
                try:
                    query = query.filter_by(signal_type=SignalType(signal_type))
                except ValueError:
                    return jsonify({'error': 'Invalid signal type'}), 400
            
            if is_active:
                query = query.filter_by(is_active=is_active)
            
            # Apply date filters
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Signal.ts >= start_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Signal.ts <= end_dt)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
            
            # Order by timestamp (descending) and apply limit
            signals = query.order_by(Signal.ts.desc()).limit(limit).all()
            
            return jsonify({
                'signals': [s.to_dict(include_timestamps=True) for s in signals],
                'count': len(signals)
            }), 200
        
    except Exception as e:
        logger.error(f"List signals error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@signal_bp.route('/<int:signal_id>', methods=['GET'])
def get_signal(signal_id):
    """
    Get a specific signal by ID.
    
    Returns:
        JSON with signal details
    """
    try:
        with session_scope() as session:
            signal = session.query(Signal).filter_by(id=signal_id).first()
            
            if not signal:
                return jsonify({'error': 'Signal not found'}), 404
            
            return jsonify({
                'signal': signal.to_dict(include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get signal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@signal_bp.route('/', methods=['POST'])
@jwt_required()
def create_signal():
    """
    Create a new signal.
    
    Request Body:
        asset_id: Asset ID (required)
        ts: Timestamp (ISO format, required)
        signal_type: Type (buy, sell, hold, etc., required)
        strength: Signal strength (weak, moderate, strong)
        confidence: Confidence score (0-100)
        price: Price at signal generation
        target_price: Suggested target price
        stop_loss: Suggested stop loss
        strategy: Strategy name
        rationale: Human-readable explanation
        indicators_used: List of indicators used
        timeframe: Timeframe (default: '1d')
        is_active: Whether signal is active (default: 'true')
        expires_at: Expiration timestamp (optional)
        
    Returns:
        JSON with created signal
    """
    try:
        data = request.get_json()
        
        required_fields = ['asset_id', 'ts', 'signal_type']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Required fields: asset_id, ts, signal_type'}), 400
        
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
            
            # Parse signal type
            try:
                signal_type = SignalType(data['signal_type'])
            except ValueError:
                return jsonify({'error': 'Invalid signal type'}), 400
            
            # Parse strength if provided
            strength = SignalStrength.MODERATE
            if 'strength' in data:
                try:
                    strength = SignalStrength(data['strength'])
                except ValueError:
                    return jsonify({'error': 'Invalid signal strength'}), 400
            
            # Parse expiration if provided
            expires_at = None
            if 'expires_at' in data:
                try:
                    expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid expires_at format'}), 400
            
            # Create signal
            signal = Signal(
                asset_id=data['asset_id'],
                ts=ts,
                signal_type=signal_type,
                strength=strength,
                confidence=data.get('confidence'),
                price=data.get('price'),
                target_price=data.get('target_price'),
                stop_loss=data.get('stop_loss'),
                strategy=data.get('strategy'),
                rationale=data.get('rationale'),
                indicators_used=data.get('indicators_used', []),
                timeframe=data.get('timeframe', '1d'),
                is_active=data.get('is_active', 'true'),
                expires_at=expires_at
            )
            
            session.add(signal)
            session.commit()
            
            return jsonify({
                'message': 'Signal created successfully',
                'signal': signal.to_dict()
            }), 201
        
    except Exception as e:
        logger.error(f"Create signal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@signal_bp.route('/<int:signal_id>', methods=['PUT'])
@jwt_required()
def update_signal(signal_id):
    """
    Update a signal (typically to mark as inactive).
    
    Request Body:
        is_active: Whether signal is active
        Any other signal fields to update
        
    Returns:
        JSON with updated signal
    """
    try:
        data = request.get_json()
        
        with session_scope() as session:
            signal = session.query(Signal).filter_by(id=signal_id).first()
            
            if not signal:
                return jsonify({'error': 'Signal not found'}), 404
            
            # Update fields if provided
            if 'is_active' in data:
                signal.is_active = data['is_active']
            if 'confidence' in data:
                signal.confidence = data['confidence']
            if 'rationale' in data:
                signal.rationale = data['rationale']
            
            session.commit()
            
            return jsonify({
                'message': 'Signal updated successfully',
                'signal': signal.to_dict()
            }), 200
        
    except Exception as e:
        logger.error(f"Update signal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@signal_bp.route('/latest', methods=['GET'])
def get_latest_signals():
    """
    Get the latest active signal for each asset.
    
    Query Parameters:
        asset_ids: Comma-separated list of asset IDs (optional)
        
    Returns:
        JSON with latest signals
    """
    try:
        asset_ids_str = request.args.get('asset_ids')
        
        with session_scope() as session:
            # Build base query for active signals
            query = session.query(Signal).filter_by(is_active='true')
            
            # Filter by asset IDs if provided
            if asset_ids_str:
                asset_ids = [aid.strip() for aid in asset_ids_str.split(',')]
                query = query.filter(Signal.asset_id.in_(asset_ids))
            
            # Get latest signal for each asset
            signals_by_asset = {}
            for signal in query.order_by(Signal.ts.desc()).all():
                if signal.asset_id not in signals_by_asset:
                    signals_by_asset[signal.asset_id] = signal
            
            signals = list(signals_by_asset.values())
            
            return jsonify({
                'signals': [s.to_dict(include_timestamps=True) for s in signals],
                'count': len(signals)
            }), 200
        
    except Exception as e:
        logger.error(f"Get latest signals error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@signal_bp.route('/types', methods=['GET'])
def list_signal_types():
    """
    Get all available signal types and strengths.
    
    Returns:
        JSON with lists of signal types and strengths
    """
    try:
        types = [{'value': t.value, 'name': t.name} for t in SignalType]
        strengths = [{'value': s.value, 'name': s.name} for s in SignalStrength]
        
        return jsonify({
            'signal_types': types,
            'signal_strengths': strengths
        }), 200
        
    except Exception as e:
        logger.error(f"List signal types error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
