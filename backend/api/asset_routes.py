"""
Asset API endpoints.

Provides operations for managing assets (stocks, ETFs, crypto, etc.).
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import logging

from backend.db import session_scope
from backend.models import Asset

asset_bp = Blueprint('assets', __name__)
logger = logging.getLogger(__name__)

# Valid asset types
VALID_ASSET_TYPES = ['stock', 'etf', 'crypto', 'index', 'forex', 'commodity', 'bond']


@asset_bp.route('/', methods=['GET'])
def list_assets():
    """
    Get all assets with optional filtering.
    
    Query Parameters:
        asset_type: Filter by asset type (stock, etf, crypto, etc.)
        search: Search by symbol or name
        limit: Maximum number of results (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        JSON with list of assets
    """
    try:
        asset_type = request.args.get('asset_type')
        search = request.args.get('search')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        with session_scope() as session:
            query = session.query(Asset)
            
            # Apply filters
            if asset_type:
                if asset_type not in VALID_ASSET_TYPES:
                    return jsonify({'error': 'Invalid asset type'}), 400
                query = query.filter_by(asset_type=asset_type)
            
            if search:
                search_term = f'%{search}%'
                query = query.filter(
                    (Asset.symbol.ilike(search_term)) | (Asset.name.ilike(search_term))
                )
            
            # Get total count before pagination
            total = query.count()
            
            # Apply pagination
            assets = query.limit(limit).offset(offset).all()
            
            return jsonify({
                'assets': [a.to_dict(include_timestamps=False) for a in assets],
                'count': len(assets),
                'total': total,
                'limit': limit,
                'offset': offset
            }), 200
        
    except Exception as e:
        logger.error(f"List assets error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@asset_bp.route('/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """
    Get a specific asset by ID or symbol.
    
    Returns:
        JSON with asset details
    """
    try:
        with session_scope() as session:
            # Try to find by ID first, then by symbol
            asset = session.query(Asset).filter(
                (Asset.id == asset_id) | (Asset.symbol == asset_id.upper())
            ).first()
            
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            return jsonify({
                'asset': asset.to_dict(include_timestamps=True)
            }), 200
        
    except Exception as e:
        logger.error(f"Get asset error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@asset_bp.route('/', methods=['POST'])
@jwt_required()
def create_asset():
    """
    Create a new asset.
    
    Request Body:
        symbol: Asset symbol (required)
        name: Asset name (required)
        asset_type: Type of asset (stock, etf, crypto, etc.)
        exchange: Exchange name
        currency: Currency code (default: USD)
        description: Asset description
        sector: Asset sector
        industry: Asset industry
        metadata: Additional metadata as JSON
        
    Returns:
        JSON with created asset
    """
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data or 'name' not in data:
            return jsonify({'error': 'Symbol and name are required'}), 400
        
        with session_scope() as session:
            # Check if asset already exists
            if session.query(Asset).filter_by(symbol=data['symbol'].upper()).first():
                return jsonify({'error': 'Asset with this symbol already exists'}), 409
            
            # Parse asset type
            asset_type = 'stock'
            if 'asset_type' in data:
                if data['asset_type'] not in VALID_ASSET_TYPES:
                    return jsonify({'error': 'Invalid asset type'}), 400
                asset_type = data['asset_type']
            
            # Create asset
            asset = Asset(
                symbol=data['symbol'].upper(),
                name=data['name'],
                asset_type=asset_type,
                exchange=data.get('exchange'),
                currency=data.get('currency', 'USD'),
                description=data.get('description'),
                sector=data.get('sector'),
                industry=data.get('industry'),
                asset_metadata=data.get('metadata', '{}')
            )
            
            session.add(asset)
            session.commit()
            
            return jsonify({
                'message': 'Asset created successfully',
                'asset': asset.to_dict()
            }), 201
        
    except Exception as e:
        logger.error(f"Create asset error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@asset_bp.route('/<asset_id>', methods=['PUT'])
@jwt_required()
def update_asset(asset_id):
    """
    Update an asset.
    
    Request Body:
        Any asset fields to update
        
    Returns:
        JSON with updated asset
    """
    try:
        data = request.get_json()
        
        with session_scope() as session:
            asset = session.query(Asset).filter_by(id=asset_id).first()
            
            if not asset:
                return jsonify({'error': 'Asset not found'}), 404
            
            # Update fields if provided
            if 'name' in data:
                asset.name = data['name']
            if 'asset_type' in data:
                if data['asset_type'] not in VALID_ASSET_TYPES:
                    return jsonify({'error': 'Invalid asset type'}), 400
                asset.asset_type = data['asset_type']
            if 'exchange' in data:
                asset.exchange = data['exchange']
            if 'currency' in data:
                asset.currency = data['currency']
            if 'description' in data:
                asset.description = data['description']
            if 'sector' in data:
                asset.sector = data['sector']
            if 'industry' in data:
                asset.industry = data['industry']
            if 'is_active' in data:
                asset.is_active = data['is_active']
            if 'metadata' in data:
                asset.asset_metadata = data['metadata']
            
            session.commit()
            
            return jsonify({
                'message': 'Asset updated successfully',
                'asset': asset.to_dict()
            }), 200
        
    except Exception as e:
        logger.error(f"Update asset error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
