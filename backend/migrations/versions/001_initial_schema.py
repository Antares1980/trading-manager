"""Initial schema with TimescaleDB support

Revision ID: 001
Revises: 
Create Date: 2025-11-24 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    
    # Create enum types
    op.execute("""
        CREATE TYPE assettype AS ENUM ('stock', 'etf', 'crypto', 'forex', 'commodity');
    """)
    
    op.execute("""
        CREATE TYPE candleinterval AS ENUM ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M');
    """)
    
    op.execute("""
        CREATE TYPE indicatortype AS ENUM ('sma', 'ema', 'rsi', 'macd', 'bbands', 'atr', 'obv', 'stoch', 'adx', 'cci');
    """)
    
    op.execute("""
        CREATE TYPE signaltype AS ENUM ('buy', 'sell', 'hold', 'strong_buy', 'strong_sell');
    """)
    
    op.execute("""
        CREATE TYPE signalstrength AS ENUM ('weak', 'moderate', 'strong');
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create assets table
    op.create_table('assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('asset_type', postgresql.ENUM('stock', 'etf', 'crypto', 'forex', 'commodity', 
                                                name='assettype', create_type=False), 
                  nullable=False, server_default='stock'),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default='USD'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.String(length=10), nullable=True, server_default='true'),
        sa.Column('market_cap', sa.String(length=50), nullable=True),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assets_symbol', 'assets', ['symbol'], unique=True)
    
    # Create watchlists table
    op.create_table('watchlists',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.String(length=10), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'])
    
    # Create watchlist_items table
    op.create_table('watchlist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('watchlist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('price_alert_high', sa.String(length=20), nullable=True),
        sa.Column('price_alert_low', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('watchlist_id', 'asset_id', name='uq_watchlist_asset')
    )
    op.create_index('ix_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'])
    op.create_index('ix_watchlist_items_asset_id', 'watchlist_items', ['asset_id'])
    
    # Create candles table (will be converted to hypertable)
    op.create_table('candles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('interval', postgresql.ENUM('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M',
                                              name='candleinterval', create_type=False),
                  nullable=False, server_default='1d'),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=30, scale=8), nullable=False, server_default='0'),
        sa.Column('trades', sa.BigInteger(), nullable=True),
        sa.Column('vwap', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True, server_default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candles_asset_id', 'candles', ['asset_id'])
    op.create_index('ix_candles_ts', 'candles', ['ts'])
    op.create_index('ix_candles_asset_ts_interval', 'candles', ['asset_id', 'ts', 'interval'])
    op.create_index('ix_candles_ts_asset', 'candles', ['ts', 'asset_id'])
    
    # Convert candles to hypertable
    op.execute("""
        SELECT create_hypertable(
            'candles', 
            'ts',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)
    
    # Create indicators table
    op.create_table('indicators',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('indicator_type', postgresql.ENUM('sma', 'ema', 'rsi', 'macd', 'bbands', 'atr', 'obv', 'stoch', 'adx', 'cci',
                                                    name='indicatortype', create_type=False),
                  nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('value2', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('value3', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('timeframe', sa.String(length=10), nullable=True, server_default='1d'),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_indicators_asset_id', 'indicators', ['asset_id'])
    op.create_index('ix_indicators_ts', 'indicators', ['ts'])
    op.create_index('ix_indicators_asset_type_ts', 'indicators', ['asset_id', 'indicator_type', 'ts'])
    op.create_index('ix_indicators_asset_name_ts', 'indicators', ['asset_id', 'name', 'ts'])
    
    # Create signals table
    op.create_table('signals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('signal_type', postgresql.ENUM('buy', 'sell', 'hold', 'strong_buy', 'strong_sell',
                                                 name='signaltype', create_type=False),
                  nullable=False),
        sa.Column('strength', postgresql.ENUM('weak', 'moderate', 'strong',
                                              name='signalstrength', create_type=False),
                  nullable=True, server_default='moderate'),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('target_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('strategy', sa.String(length=100), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('indicators_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('timeframe', sa.String(length=10), nullable=True, server_default='1d'),
        sa.Column('is_active', sa.String(length=10), nullable=True, server_default='true'),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_signals_asset_id', 'signals', ['asset_id'])
    op.create_index('ix_signals_ts', 'signals', ['ts'])
    op.create_index('ix_signals_asset_ts', 'signals', ['asset_id', 'ts'])
    op.create_index('ix_signals_asset_type_ts', 'signals', ['asset_id', 'signal_type', 'ts'])
    op.create_index('ix_signals_active', 'signals', ['is_active', 'ts'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_signals_active', table_name='signals')
    op.drop_index('ix_signals_asset_type_ts', table_name='signals')
    op.drop_index('ix_signals_asset_ts', table_name='signals')
    op.drop_index('ix_signals_ts', table_name='signals')
    op.drop_index('ix_signals_asset_id', table_name='signals')
    op.drop_table('signals')
    
    op.drop_index('ix_indicators_asset_name_ts', table_name='indicators')
    op.drop_index('ix_indicators_asset_type_ts', table_name='indicators')
    op.drop_index('ix_indicators_ts', table_name='indicators')
    op.drop_index('ix_indicators_asset_id', table_name='indicators')
    op.drop_table('indicators')
    
    op.drop_index('ix_candles_ts_asset', table_name='candles')
    op.drop_index('ix_candles_asset_ts_interval', table_name='candles')
    op.drop_index('ix_candles_ts', table_name='candles')
    op.drop_index('ix_candles_asset_id', table_name='candles')
    op.drop_table('candles')
    
    op.drop_index('ix_watchlist_items_asset_id', table_name='watchlist_items')
    op.drop_index('ix_watchlist_items_watchlist_id', table_name='watchlist_items')
    op.drop_table('watchlist_items')
    
    op.drop_index('ix_watchlists_user_id', table_name='watchlists')
    op.drop_table('watchlists')
    
    op.drop_index('ix_assets_symbol', table_name='assets')
    op.drop_table('assets')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS signalstrength CASCADE;')
    op.execute('DROP TYPE IF EXISTS signaltype CASCADE;')
    op.execute('DROP TYPE IF EXISTS indicatortype CASCADE;')
    op.execute('DROP TYPE IF EXISTS candleinterval CASCADE;')
    op.execute('DROP TYPE IF EXISTS assettype CASCADE;')
    
    # Note: We don't drop the TimescaleDB extension as it might be used by other databases
