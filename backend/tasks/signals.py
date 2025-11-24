"""
Celery tasks for generating trading signals.

These tasks analyze indicators and price patterns to generate trading signals.
"""

from celery import Task
import logging
from datetime import datetime, timezone, timedelta

from backend.tasks import celery_app
from backend.db import init_db, session_scope
from backend.models import Asset, Indicator, Signal, SignalType, SignalStrength
from backend.config import get_config

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
def compute_signals(self, asset_id=None):
    """
    Generate trading signals based on technical indicators.
    
    Args:
        asset_id: Specific asset ID to generate signals for (optional)
        
    Returns:
        Dictionary with results
    """
    try:
        logger.info(f"Starting signal generation task (asset_id={asset_id})")
        
        results = {
            'processed_assets': 0,
            'signals_created': 0,
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
            
            logger.info(f"Processing {len(assets)} assets for signal generation")
            
            for asset in assets:
                try:
                    # Get latest indicators for the asset
                    recent_date = datetime.now(timezone.utc) - timedelta(days=2)
                    indicators = session.query(Indicator).filter(
                        Indicator.asset_id == asset.id,
                        Indicator.ts >= recent_date
                    ).order_by(Indicator.ts.desc()).all()
                    
                    if not indicators:
                        logger.warning(f"No recent indicators found for {asset.symbol}")
                        continue
                    
                    # Group indicators by type
                    indicator_map = {}
                    for ind in indicators:
                        if ind.name not in indicator_map:
                            indicator_map[ind.name] = ind
                    
                    # Extract key indicators
                    rsi = indicator_map.get('RSI_14')
                    sma_20 = indicator_map.get('SMA_20')
                    sma_50 = indicator_map.get('SMA_50')
                    macd = indicator_map.get('MACD_12_26_9')
                    
                    # Generate signal based on simple strategy
                    signal_type = None
                    strength = SignalStrength.MODERATE
                    confidence = 50.0
                    rationale_parts = []
                    indicators_used = []
                    
                    # Strategy: Simple RSI + Moving Average Crossover
                    buy_signals = 0
                    sell_signals = 0
                    
                    # RSI analysis
                    if rsi and rsi.value:
                        indicators_used.append('RSI_14')
                        rsi_value = float(rsi.value)
                        if rsi_value < 30:
                            buy_signals += 1
                            rationale_parts.append(f"RSI oversold ({rsi_value:.1f})")
                        elif rsi_value > 70:
                            sell_signals += 1
                            rationale_parts.append(f"RSI overbought ({rsi_value:.1f})")
                    
                    # Moving average crossover
                    if sma_20 and sma_50 and sma_20.value and sma_50.value:
                        indicators_used.extend(['SMA_20', 'SMA_50'])
                        sma_20_val = float(sma_20.value)
                        sma_50_val = float(sma_50.value)
                        
                        if sma_20_val > sma_50_val:
                            buy_signals += 1
                            rationale_parts.append("SMA 20 above SMA 50 (bullish trend)")
                        elif sma_20_val < sma_50_val:
                            sell_signals += 1
                            rationale_parts.append("SMA 20 below SMA 50 (bearish trend)")
                    
                    # MACD analysis
                    if macd and macd.value and macd.value2:
                        indicators_used.append('MACD_12_26_9')
                        macd_line = float(macd.value)
                        signal_line = float(macd.value2)
                        
                        if macd_line > signal_line and macd_line > 0:
                            buy_signals += 1
                            rationale_parts.append("MACD bullish crossover")
                        elif macd_line < signal_line and macd_line < 0:
                            sell_signals += 1
                            rationale_parts.append("MACD bearish crossover")
                    
                    # Determine overall signal
                    if buy_signals > sell_signals:
                        if buy_signals >= 3:
                            signal_type = SignalType.STRONG_BUY
                            strength = SignalStrength.STRONG
                            confidence = 75.0
                        else:
                            signal_type = SignalType.BUY
                            strength = SignalStrength.MODERATE
                            confidence = 60.0
                    elif sell_signals > buy_signals:
                        if sell_signals >= 3:
                            signal_type = SignalType.STRONG_SELL
                            strength = SignalStrength.STRONG
                            confidence = 75.0
                        else:
                            signal_type = SignalType.SELL
                            strength = SignalStrength.MODERATE
                            confidence = 60.0
                    else:
                        signal_type = SignalType.HOLD
                        strength = SignalStrength.WEAK
                        confidence = 50.0
                        rationale_parts.append("Mixed signals")
                    
                    # Create signal if we have meaningful indicators
                    if indicators_used and signal_type:
                        # Mark previous signals as inactive
                        prev_signals = session.query(Signal).filter(
                            Signal.asset_id == asset.id,
                            Signal.is_active == 'true'
                        ).all()
                        for prev_signal in prev_signals:
                            prev_signal.is_active = 'false'
                        
                        # Get the latest timestamp from indicators
                        latest_ts = max(ind.ts for ind in indicators)
                        
                        # Create new signal
                        signal = Signal(
                            asset_id=asset.id,
                            ts=latest_ts,
                            signal_type=signal_type,
                            strength=strength,
                            confidence=confidence,
                            strategy='RSI_MA_MACD_Combined',
                            rationale='; '.join(rationale_parts) if rationale_parts else 'No clear signals',
                            indicators_used=indicators_used,
                            timeframe='1d',
                            is_active='true'
                        )
                        
                        session.add(signal)
                        results['signals_created'] += 1
                        logger.info(f"Generated {signal_type.value} signal for {asset.symbol}")
                    
                    results['processed_assets'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {asset.symbol}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            session.commit()
        
        logger.info(f"Signal generation complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Signal generation task failed: {str(e)}")
        return {'error': str(e)}


@celery_app.task(base=DatabaseTask)
def compute_signals_for_asset(asset_id):
    """
    Generate signals for a specific asset.
    
    Args:
        asset_id: Asset ID
        
    Returns:
        Task result
    """
    return compute_signals(asset_id=asset_id)


@celery_app.task(base=DatabaseTask)
def deactivate_expired_signals():
    """
    Deactivate signals that have expired.
    
    Returns:
        Dictionary with count of deactivated signals
    """
    try:
        logger.info("Starting expired signal deactivation task")
        
        with session_scope() as session:
            now = datetime.now(timezone.utc)
            expired_signals = session.query(Signal).filter(
                Signal.is_active == 'true',
                Signal.expires_at.isnot(None),
                Signal.expires_at <= now
            ).all()
            
            count = 0
            for signal in expired_signals:
                signal.is_active = 'false'
                count += 1
            
            session.commit()
            
            logger.info(f"Deactivated {count} expired signals")
            return {'deactivated_signals': count}
        
    except Exception as e:
        logger.error(f"Expired signal deactivation task failed: {str(e)}")
        return {'error': str(e)}
