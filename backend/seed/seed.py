"""
Database seeding script.

Seeds the database with demo users, watchlists, assets, and sample candle data.
"""

import logging
from datetime import datetime, timezone, timedelta
import random

from backend.db import init_db, session_scope, get_engine
from backend.models import (
    User, Asset, AssetType, Watchlist, WatchlistItem,
    Candle, CandleInterval, Indicator, IndicatorType, Signal, SignalType, SignalStrength
)
from backend.config import get_config

logger = logging.getLogger(__name__)


def seed_database(force=False):
    """
    Seed the database with demo data.
    
    Args:
        force: If True, seed even if data already exists
    """
    config = get_config()
    
    # Initialize database
    engine = init_db(config.SQLALCHEMY_DATABASE_URI, config.SQLALCHEMY_ECHO)
    
    with session_scope() as session:
        # Check if data already exists
        if not force and session.query(User).count() > 0:
            logger.info("Database already has data. Use --force to seed anyway.")
            return
        
        logger.info("Seeding database with demo data...")
        
        # Create demo users
        demo_user = User(
            username='demo',
            email='demo@trading-manager.com',
            full_name='Demo User'
        )
        demo_user.set_password('demo123')
        session.add(demo_user)
        
        admin_user = User(
            username='admin',
            email='admin@trading-manager.com',
            full_name='Admin User',
            is_admin=True
        )
        admin_user.set_password('admin123')
        session.add(admin_user)
        
        session.flush()  # Get user IDs
        logger.info(f"Created users: {demo_user.username}, {admin_user.username}")
        
        # Create demo assets
        assets_data = [
            ('AAPL', 'Apple Inc.', AssetType.STOCK, 'NASDAQ', 'Technology', 'Consumer Electronics'),
            ('GOOGL', 'Alphabet Inc.', AssetType.STOCK, 'NASDAQ', 'Technology', 'Internet Services'),
            ('MSFT', 'Microsoft Corporation', AssetType.STOCK, 'NASDAQ', 'Technology', 'Software'),
            ('AMZN', 'Amazon.com Inc.', AssetType.STOCK, 'NASDAQ', 'Consumer Cyclical', 'Internet Retail'),
            ('TSLA', 'Tesla Inc.', AssetType.STOCK, 'NASDAQ', 'Consumer Cyclical', 'Auto Manufacturers'),
            ('META', 'Meta Platforms Inc.', AssetType.STOCK, 'NASDAQ', 'Technology', 'Internet Services'),
            ('NVDA', 'NVIDIA Corporation', AssetType.STOCK, 'NASDAQ', 'Technology', 'Semiconductors'),
            ('JPM', 'JPMorgan Chase & Co.', AssetType.STOCK, 'NYSE', 'Financial', 'Banks'),
            ('V', 'Visa Inc.', AssetType.STOCK, 'NYSE', 'Financial', 'Credit Services'),
            ('WMT', 'Walmart Inc.', AssetType.STOCK, 'NYSE', 'Consumer Defensive', 'Discount Stores'),
            ('SPY', 'SPDR S&P 500 ETF Trust', AssetType.ETF, 'NYSE', None, None),
            ('BTC-USD', 'Bitcoin USD', AssetType.CRYPTO, 'CRYPTO', None, None),
        ]
        
        assets = []
        for symbol, name, asset_type, exchange, sector, industry in assets_data:
            asset = Asset(
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                exchange=exchange,
                sector=sector,
                industry=industry,
                currency='USD',
                is_active='true'
            )
            session.add(asset)
            assets.append(asset)
        
        session.flush()  # Get asset IDs
        logger.info(f"Created {len(assets)} assets")
        
        # Create watchlists for demo user
        watchlist1 = Watchlist(
            user_id=demo_user.id,
            name='Tech Favorites',
            description='My favorite technology stocks',
            color='#3b82f6',
            icon='laptop',
            is_default='true'
        )
        session.add(watchlist1)
        
        watchlist2 = Watchlist(
            user_id=demo_user.id,
            name='Market Leaders',
            description='Top market cap companies',
            color='#10b981',
            icon='trending-up'
        )
        session.add(watchlist2)
        
        session.flush()
        logger.info(f"Created watchlists: {watchlist1.name}, {watchlist2.name}")
        
        # Add items to watchlists
        tech_assets = [a for a in assets if a.symbol in ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'META']]
        for i, asset in enumerate(tech_assets):
            item = WatchlistItem(
                watchlist_id=watchlist1.id,
                asset_id=asset.id,
                position=i,
                notes=f'Tracking {asset.name}'
            )
            session.add(item)
        
        market_leaders = [a for a in assets if a.symbol in ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'SPY']]
        for i, asset in enumerate(market_leaders):
            item = WatchlistItem(
                watchlist_id=watchlist2.id,
                asset_id=asset.id,
                position=i
            )
            session.add(item)
        
        logger.info(f"Added items to watchlists")
        
        # Generate sample daily candle data for each asset (last 365 days)
        end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=365)
        
        for asset in assets:
            # Generate realistic-looking price data
            base_price = random.uniform(50, 500)
            current_price = base_price
            
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends for stocks
                if asset.asset_type in [AssetType.STOCK, AssetType.ETF]:
                    if current_date.weekday() >= 5:  # Saturday or Sunday
                        current_date += timedelta(days=1)
                        continue
                
                # Generate daily price movement
                daily_change = random.uniform(-0.05, 0.05)  # -5% to +5%
                open_price = current_price
                close_price = current_price * (1 + daily_change)
                
                # Generate high/low within reasonable range
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
                low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
                
                # Generate volume
                volume = random.uniform(1000000, 10000000)
                
                candle = Candle(
                    asset_id=asset.id,
                    ts=current_date,
                    interval=CandleInterval.DAY_1,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=round(volume, 0),
                    source='seed_data'
                )
                session.add(candle)
                
                current_price = close_price
                current_date += timedelta(days=1)
            
            logger.info(f"Generated candle data for {asset.symbol}")
        
        # Commit all changes
        session.commit()
        
        logger.info("Database seeding completed successfully!")
        logger.info(f"Demo users created - username: 'demo', password: 'demo123'")
        logger.info(f"Admin user created - username: 'admin', password: 'admin123'")
        logger.info(f"Created {len(assets)} assets with 365 days of historical data")
        logger.info(f"Run indicator and signal computation tasks to generate analysis data")


if __name__ == '__main__':
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for --force flag
    force = '--force' in sys.argv
    
    seed_database(force=force)
