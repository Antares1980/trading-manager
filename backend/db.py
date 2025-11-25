"""
Database initialization and session management.

Provides SQLAlchemy engine, session factory, and TimescaleDB helpers.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Global variables for engine and session
_engine = None
_session_factory = None


def init_db(database_uri, echo=False):
    """
    Initialize the database engine and session factory.
    
    Args:
        database_uri: SQLAlchemy database URI
        echo: Whether to echo SQL statements (for debugging)
    """
    global _engine, _session_factory
    
    # Configure engine options based on database type
    engine_options = {
        'echo': echo,
        'pool_pre_ping': True,  # Verify connections before using
    }
    
    # Only add pool settings for non-SQLite databases
    if not database_uri.startswith('sqlite'):
        engine_options['pool_size'] = 10
        engine_options['max_overflow'] = 20
    
    _engine = create_engine(database_uri, **engine_options)
    
    _session_factory = scoped_session(
        sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False
        )
    )
    
    logger.info(f"Database initialized: {database_uri.split('@')[-1]}")  # Log without credentials
    
    return _engine


def get_engine():
    """Get the SQLAlchemy engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session():
    """Get a new database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    
    Usage:
        with session_scope() as session:
            session.add(obj)
            # Automatically commits on success, rolls back on exception
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables():
    """Create all tables defined in models."""
    Base.metadata.create_all(bind=get_engine())
    logger.info("All tables created")


def drop_all_tables():
    """Drop all tables (use with caution!)."""
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All tables dropped")


def enable_timescaledb_extension():
    """
    Enable TimescaleDB extension in the database.
    
    Must be run with superuser privileges.
    """
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
        conn.commit()
    logger.info("TimescaleDB extension enabled")


def create_hypertable(table_name, time_column='ts', chunk_time_interval='7 days'):
    """
    Convert a regular PostgreSQL table to a TimescaleDB hypertable.
    
    Args:
        table_name: Name of the table to convert
        time_column: Name of the time column to partition on
        chunk_time_interval: Time interval for chunks (e.g., '7 days', '1 month')
    """
    engine = get_engine()
    
    # Check if already a hypertable
    check_query = text("""
        SELECT EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables 
            WHERE hypertable_name = :table_name
        );
    """)
    
    with engine.connect() as conn:
        result = conn.execute(check_query, {'table_name': table_name}).scalar()
        
        if result:
            logger.info(f"Table '{table_name}' is already a hypertable")
            return
        
        # Create hypertable
        create_query = text(f"""
            SELECT create_hypertable(
                '{table_name}',
                '{time_column}',
                chunk_time_interval => INTERVAL '{chunk_time_interval}',
                if_not_exists => TRUE
            );
        """)
        
        conn.execute(create_query)
        conn.commit()
        
    logger.info(f"Hypertable created: {table_name} (chunk_interval={chunk_time_interval})")


def set_compression_policy(table_name, compress_after='30 days'):
    """
    Set up automatic compression for old data in a hypertable.
    
    Args:
        table_name: Name of the hypertable
        compress_after: Age after which to compress chunks (e.g., '30 days', '3 months')
    """
    engine = get_engine()
    
    with engine.connect() as conn:
        # Enable compression
        conn.execute(text(f"""
            ALTER TABLE {table_name} SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'asset_id'
            );
        """))
        
        # Add compression policy
        conn.execute(text(f"""
            SELECT add_compression_policy(
                '{table_name}',
                INTERVAL '{compress_after}',
                if_not_exists => TRUE
            );
        """))
        
        conn.commit()
    
    logger.info(f"Compression policy set for {table_name} (compress_after={compress_after})")


def set_retention_policy(table_name, retain_for='1 year'):
    """
    Set up automatic data retention policy for a hypertable.
    
    Args:
        table_name: Name of the hypertable
        retain_for: How long to retain data (e.g., '1 year', '6 months')
    """
    engine = get_engine()
    
    with engine.connect() as conn:
        conn.execute(text(f"""
            SELECT add_retention_policy(
                '{table_name}',
                INTERVAL '{retain_for}',
                if_not_exists => TRUE
            );
        """))
        conn.commit()
    
    logger.info(f"Retention policy set for {table_name} (retain_for={retain_for})")


def close_db():
    """Close database connections."""
    global _session_factory
    if _session_factory:
        _session_factory.remove()
        logger.info("Database connections closed")
