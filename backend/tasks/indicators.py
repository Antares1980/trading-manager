"""
Celery tasks for computing technical indicators.

These tasks compute various technical indicators for assets using the 'ta' library.
"""

from celery import Task
import logging
from datetime import datetime, timezone, timedelta
import pandas as pd
import ta

from backend.tasks import celery_app
from backend.db import init_db, session_scope
from backend.models import Asset, Candle, Indicator, IndicatorType, CandleInterval
from backend.settings import get_config

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that ensures database is initialized."""
    
    _db_initialized = False
    
    def __call__(self, *args, **kwargs):
        if not self._db_initialized:
            config = get_config()
            init_db(config.SQLALCHEMY_DATABASE_URI, config.SQLALCHEMY_ECHO)
            DatabaseTask._db_initialized = True
        return super().__call__(*args, **kwargs)


@celery_app.task(base=DatabaseTask, bind=True)
def compute_indicators(self, asset_id=None, lookback_days=100):
    """
    Compute technical indicators for assets.
    
    Args:
        asset_id: Specific asset ID to compute indicators for (optional)
        lookback_days: Number of days to look back for data (default: 100)
        
    Returns:
        Dictionary with results
    """
    try:
        logger.info(f"Starting indicator computation task (asset_id={asset_id})")
        
        results = {
            'processed_assets': 0,
            'indicators_created': 0,
            'errors': []
        }
        
        with session_scope() as session:
            # Get assets to process
            if asset_id:
                assets = [session.query(Asset).filter_by(id=asset_id).first()]
                if not assets[0]:
                    return {'error': f'Asset {asset_id} not found'}
            else:
                assets = session.query(Asset).filter_by(is_active='true').all()
            
            logger.info(f"Processing {len(assets)} assets")
            
            for asset in assets:
                try:
                    # Get candle data for the asset
                    start_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
                    candles = session.query(Candle).filter(
                        Candle.asset_id == asset.id,
                        Candle.interval == CandleInterval.DAY_1,
                        Candle.ts >= start_date
                    ).order_by(Candle.ts.asc()).all()
                    
                    if len(candles) < 20:
                        logger.warning(f"Not enough data for {asset.symbol} (only {len(candles)} candles)")
                        continue
                    
                    # Convert to DataFrame
                    df = pd.DataFrame([{
                        'timestamp': c.ts,
                        'open': float(c.open),
                        'high': float(c.high),
                        'low': float(c.low),
                        'close': float(c.close),
                        'volume': float(c.volume)
                    } for c in candles])
                    
                    df.set_index('timestamp', inplace=True)
                    
                    # Compute indicators using ta library
                    indicators_data = []
                    
                    # SMA - Simple Moving Average
                    df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
                    df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
                    
                    # EMA - Exponential Moving Average
                    df['ema_20'] = ta.trend.ema_indicator(df['close'], window=20)
                    df['ema_50'] = ta.trend.ema_indicator(df['close'], window=50)
                    
                    # RSI - Relative Strength Index
                    df['rsi_14'] = ta.momentum.rsi(df['close'], window=14)
                    
                    # MACD - Moving Average Convergence Divergence
                    macd = ta.trend.MACD(df['close'])
                    df['macd'] = macd.macd()
                    df['macd_signal'] = macd.macd_signal()
                    df['macd_diff'] = macd.macd_diff()
                    
                    # Bollinger Bands
                    bollinger = ta.volatility.BollingerBands(df['close'])
                    df['bb_high'] = bollinger.bollinger_hband()
                    df['bb_mid'] = bollinger.bollinger_mavg()
                    df['bb_low'] = bollinger.bollinger_lband()
                    
                    # ATR - Average True Range
                    df['atr_14'] = ta.volatility.average_true_range(
                        df['high'], df['low'], df['close'], window=14
                    )
                    
                    # OBV - On-Balance Volume
                    df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
                    
                    # Store only the most recent indicators (last row)
                    latest_idx = df.index[-1]
                    latest_row = df.iloc[-1]
                    
                    # Create indicator records
                    indicator_definitions = [
                        (IndicatorType.SMA, 'SMA_20', latest_row['sma_20'], None, None, {'period': 20}),
                        (IndicatorType.SMA, 'SMA_50', latest_row['sma_50'], None, None, {'period': 50}),
                        (IndicatorType.EMA, 'EMA_20', latest_row['ema_20'], None, None, {'period': 20}),
                        (IndicatorType.EMA, 'EMA_50', latest_row['ema_50'], None, None, {'period': 50}),
                        (IndicatorType.RSI, 'RSI_14', latest_row['rsi_14'], None, None, {'period': 14}),
                        (IndicatorType.MACD, 'MACD_12_26_9', latest_row['macd'], 
                         latest_row['macd_signal'], latest_row['macd_diff'], 
                         {'fast': 12, 'slow': 26, 'signal': 9}),
                        (IndicatorType.BBANDS, 'BBANDS_20_2', latest_row['bb_mid'], 
                         latest_row['bb_high'], latest_row['bb_low'], 
                         {'period': 20, 'std': 2}),
                        (IndicatorType.ATR, 'ATR_14', latest_row['atr_14'], None, None, {'period': 14}),
                        (IndicatorType.OBV, 'OBV', latest_row['obv'], None, None, {}),
                    ]
                    
                    for ind_type, name, value, value2, value3, params in indicator_definitions:
                        if pd.notna(value):
                            indicator = Indicator(
                                asset_id=asset.id,
                                ts=latest_idx,
                                indicator_type=ind_type,
                                name=name,
                                value=float(value) if pd.notna(value) else None,
                                value2=float(value2) if pd.notna(value2) else None,
                                value3=float(value3) if pd.notna(value3) else None,
                                parameters=params,
                                timeframe='1d'
                            )
                            session.add(indicator)
                            results['indicators_created'] += 1
                    
                    results['processed_assets'] += 1
                    logger.info(f"Computed indicators for {asset.symbol}")
                    
                except Exception as e:
                    error_msg = f"Error processing {asset.symbol}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            session.commit()
        
        logger.info(f"Indicator computation complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Indicator computation task failed: {str(e)}")
        return {'error': str(e)}


@celery_app.task(base=DatabaseTask)
def compute_indicators_for_asset(asset_id, lookback_days=100):
    """
    Compute indicators for a specific asset.
    
    Args:
        asset_id: Asset ID
        lookback_days: Number of days to look back
        
    Returns:
        Task result
    """
    return compute_indicators(asset_id=asset_id, lookback_days=lookback_days)
