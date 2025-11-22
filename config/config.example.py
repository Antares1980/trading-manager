"""
Example configuration file for Trading Manager.
Copy this to config.py and modify as needed.
"""

import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    
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

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
