"""
Watchlist API endpoints.

Provides CRUD operations for user watchlists and watchlist items.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from backend.db import session_scope
from backend.models import Watchlist, WatchlistItem, Asset, User

watchlist_bp = Blueprint('watchlists', __name__)
logger = logging.getLogger(__name__)


@watchlist_bp.route('/', methods=['GET'])
@jwt_required()
def list_watchlists():
    """
    Get all watchlists for the current user.
    
    Returns:
        JSON with list of watchlists
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            watchlists = session.query(Watchlist).filter_by(user_id=user_id).all()
            
            return jsonify({
                'watchlists': [w.to_dict(include_items=True) for w in watchlists],
                'count': len(watchlists)
            }), 200
        
    except Exception as e:
        logger.error(f"List watchlists error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/<watchlist_id>', methods=['GET'])
@jwt_required()
def get_watchlist(watchlist_id):
    """
    Get a specific watchlist by ID.
    
    Returns:
        JSON with watchlist details and items
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            watchlist = session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()
            
            if not watchlist:
                return jsonify({'error': 'Watchlist not found'}), 404
            
            return jsonify({
                'watchlist': watchlist.to_dict(include_items=True, include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get watchlist error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/', methods=['POST'])
@jwt_required()
def create_watchlist():
    """
    Create a new watchlist.
    
    Request Body:
        name: Watchlist name (required)
        description: Watchlist description (optional)
        color: Color code (optional)
        icon: Icon identifier (optional)
        is_default: Whether this is the default watchlist (optional)
        
    Returns:
        JSON with created watchlist
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Watchlist name is required'}), 400
        
        with session_scope() as session:
            watchlist = Watchlist(
                user_id=user_id,
                name=data['name'],
                description=data.get('description'),
                color=data.get('color'),
                icon=data.get('icon'),
                is_default=data.get('is_default', 'false')
            )
            
            session.add(watchlist)
            session.commit()
            
            return jsonify({
                'message': 'Watchlist created successfully',
                'watchlist': watchlist.to_dict(include_items=True)
            }), 201
        
    except Exception as e:
        logger.error(f"Create watchlist error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/<watchlist_id>', methods=['PUT'])
@jwt_required()
def update_watchlist(watchlist_id):
    """
    Update a watchlist.
    
    Request Body:
        name: Watchlist name (optional)
        description: Watchlist description (optional)
        color: Color code (optional)
        icon: Icon identifier (optional)
        is_default: Whether this is the default watchlist (optional)
        
    Returns:
        JSON with updated watchlist
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        with session_scope() as session:
            watchlist = session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()
            
            if not watchlist:
                return jsonify({'error': 'Watchlist not found'}), 404
            
            # Update fields if provided
            if 'name' in data:
                watchlist.name = data['name']
            if 'description' in data:
                watchlist.description = data['description']
            if 'color' in data:
                watchlist.color = data['color']
            if 'icon' in data:
                watchlist.icon = data['icon']
            if 'is_default' in data:
                watchlist.is_default = data['is_default']
            
            session.commit()
            
            return jsonify({
                'message': 'Watchlist updated successfully',
                'watchlist': watchlist.to_dict(include_items=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Update watchlist error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/<watchlist_id>', methods=['DELETE'])
@jwt_required()
def delete_watchlist(watchlist_id):
    """
    Delete a watchlist.
    
    Returns:
        JSON with success message
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            watchlist = session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()
            
            if not watchlist:
                return jsonify({'error': 'Watchlist not found'}), 404
            
            session.delete(watchlist)
            session.commit()
            
            return jsonify({
                'message': 'Watchlist deleted successfully'
            }), 200
        
    except Exception as e:
        logger.error(f"Delete watchlist error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/<watchlist_id>/items', methods=['POST'])
@jwt_required()
def add_item_to_watchlist(watchlist_id):
    """
    Add an asset to a watchlist.
    
    Request Body:
        asset_id: Asset ID to add (required)
        notes: Custom notes (optional)
        price_alert_high: High price alert (optional)
        price_alert_low: Low price alert (optional)
        
    Returns:
        JSON with created watchlist item
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'asset_id' not in data:
            return jsonify({'error': 'Asset ID is required'}), 400
        
        with session_scope() as session:
            # Verify watchlist ownership
            watchlist = session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()
            
            if not watchlist:
                return jsonify({'error': 'Watchlist not found'}), 404
            
            # Verify asset exists
            asset = session.query(Asset).filter_by(id=data['asset_id']).first()
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            # Check if item already exists
            existing = session.query(WatchlistItem).filter_by(
                watchlist_id=watchlist_id,
                asset_id=data['asset_id']
            ).first()
            
            if existing:
                return jsonify({'error': 'Asset already in watchlist'}), 409
            
            # Get max position for ordering
            max_position = session.query(WatchlistItem).filter_by(
                watchlist_id=watchlist_id
            ).count()
            
            # Create watchlist item
            item = WatchlistItem(
                watchlist_id=watchlist_id,
                asset_id=data['asset_id'],
                position=max_position,
                notes=data.get('notes'),
                price_alert_high=data.get('price_alert_high'),
                price_alert_low=data.get('price_alert_low')
            )
            
            session.add(item)
            session.commit()
            
            return jsonify({
                'message': 'Asset added to watchlist',
                'item': item.to_dict(include_asset=True)
            }), 201
        
    except Exception as e:
        logger.error(f"Add item error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@watchlist_bp.route('/<watchlist_id>/items/<item_id>', methods=['DELETE'])
@jwt_required()
def remove_item_from_watchlist(watchlist_id, item_id):
    """
    Remove an asset from a watchlist.
    
    Returns:
        JSON with success message
    """
    try:
        user_id = get_jwt_identity()
        
        with session_scope() as session:
            # Verify watchlist ownership
            watchlist = session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()
            
            if not watchlist:
                return jsonify({'error': 'Watchlist not found'}), 404
            
            # Find and delete item
            item = session.query(WatchlistItem).filter_by(
                id=item_id,
                watchlist_id=watchlist_id
            ).first()
            
            if not item:
                return jsonify({'error': 'Item not found'}), 404
            
            session.delete(item)
            session.commit()
            
            return jsonify({
                'message': 'Item removed from watchlist'
            }), 200
        
    except Exception as e:
        logger.error(f"Remove item error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
