#!/usr/bin/env python3
"""
Trading Manager Flask Application with Database Integration

This module provides the Flask application factory and CLI commands.
Configuration is loaded from environment variables and .env file in development.
"""

import os
import sys
import click
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask.json.provider import DefaultJSONProvider
import math

# Import configuration
from backend.config import get_config

# Import database utilities
from backend.db import init_db, close_db, get_session, Base

# Import API blueprints
from backend.api.market_routes import market_bp
from backend.api.analysis_routes import analysis_bp
from backend.api.auth_routes import auth_bp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that handles NaN and infinity values."""
    
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        return super().default(obj)


def create_app(config_name=None):
    """
    Application factory for creating Flask app instance.
    
    Args:
        config_name: Configuration name ('development', 'production', 'test')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Flask application instance
    """
    # Load .env file in development
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file")
    
    # Create Flask app
    app = Flask(__name__,
                static_folder='../frontend/static',
                template_folder='../frontend/templates')
    
    # Set custom JSON provider
    app.json = CustomJSONProvider(app)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    logger.info(f"Loaded configuration: {config.__name__}")
    
    # Initialize database
    init_db(app.config['SQLALCHEMY_DATABASE_URI'], app.config['SQLALCHEMY_ECHO'])
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Enable CORS for development
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Try to register new blueprints (may not exist yet)
    try:
        from backend.api.watchlist_routes import watchlist_bp
        app.register_blueprint(watchlist_bp, url_prefix='/api/watchlists')
    except ImportError:
        logger.warning("Watchlist routes not found, skipping")
    
    try:
        from backend.api.asset_routes import asset_bp
        app.register_blueprint(asset_bp, url_prefix='/api/assets')
    except ImportError:
        logger.warning("Asset routes not found, skipping")
    
    try:
        from backend.api.candle_routes import candle_bp
        app.register_blueprint(candle_bp, url_prefix='/api/candles')
    except ImportError:
        logger.warning("Candle routes not found, skipping")
    
    try:
        from backend.api.indicator_routes import indicator_bp
        app.register_blueprint(indicator_bp, url_prefix='/api/indicators')
    except ImportError:
        logger.warning("Indicator routes not found, skipping")
    
    try:
        from backend.api.signal_routes import signal_bp
        app.register_blueprint(signal_bp, url_prefix='/api/signals')
    except ImportError:
        logger.warning("Signal routes not found, skipping")
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint that verifies database connectivity."""
        try:
            session = get_session()
            session.execute('SELECT 1')
            session.close()
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 503
    
    # Serve frontend
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    # Cleanup on shutdown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database session on app context teardown."""
        try:
            close_db()
        except Exception:
            pass
    
    # CLI commands
    @app.cli.command('db-init')
    def db_init_command():
        """Initialize the database (create all tables)."""
        from backend.db import create_all_tables
        click.echo('Initializing database...')
        create_all_tables()
        click.echo('Database initialized.')
    
    @app.cli.command('db-seed')
    @click.option('--force', is_flag=True, help='Force seed even if data exists')
    def db_seed_command(force):
        """Seed the database with demo data."""
        try:
            from backend.seed.seed import seed_database
            click.echo('Seeding database with demo data...')
            seed_database(force=force)
            click.echo('Database seeded successfully.')
        except ImportError:
            click.echo('Error: Seed module not found.', err=True)
            sys.exit(1)
    
    return app


if __name__ == '__main__':
    # Create and run the app
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Trading Manager on http://localhost:{port}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    
    app.run(host='0.0.0.0', port=port)
