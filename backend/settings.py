"""
Configuration module for Trading Manager backend.

Provides configuration classes and a get_config factory function.
"""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///trading_manager.db'
    SQLALCHEMY_ECHO = False
    
    # API settings
    API_RATE_LIMIT = "100 per hour"
    
    # Data settings
    DEFAULT_START_DAYS = 30  # Default number of days to fetch
    CACHE_TIMEOUT = 300  # Cache timeout in seconds
    
    # Technical analysis defaults
    RSI_PERIOD = 14
    SMA_PERIODS = [20, 50]
    EMA_PERIODS = [20, 50]
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2
    
    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
_config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return _config_map.get(config_name, _config_map['default'])
