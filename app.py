#!/usr/bin/env python3
"""
Trading Manager Flask Application

Main entry point for the trading manager web application.
Serves API endpoints for market data and technical analysis.
"""

from flask import Flask
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider
from backend.api.market_routes import market_bp
from backend.api.analysis_routes import analysis_bp
from backend.api.auth_routes import auth_bp
import os
import math


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that handles NaN and infinity values."""
    
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        return super().default(obj)

def create_app():
    """Application factory for creating Flask app instance."""
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Set custom JSON provider
    app.json = CustomJSONProvider(app)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Enable CORS for development
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    # Serve frontend
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    
    print(f"Starting Trading Manager on http://localhost:{port}")
    print(f"Debug mode: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
