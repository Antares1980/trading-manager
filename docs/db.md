# TimescaleDB Database Setup and Management

This document describes the TimescaleDB database setup, schema, and common operations for the Trading Manager application.

## Overview

The Trading Manager uses TimescaleDB, a PostgreSQL extension optimized for time-series data. TimescaleDB provides:

- **Hypertables**: Automatic partitioning of time-series data into chunks
- **Compression**: Efficient storage of historical data
- **Continuous Aggregates**: Pre-computed aggregations for fast queries
- **Retention Policies**: Automatic data lifecycle management

## Database Schema

### User-Facing Tables (UUID Primary Keys)

#### users
- **Primary Key**: UUID
- **Purpose**: Store user account information
- **Key Fields**: username, email, password_hash, is_active, is_admin
- **Timestamps**: created_at, updated_at, last_login (UTC)

#### assets
- **Primary Key**: UUID
- **Purpose**: Store tradeable securities information
- **Key Fields**: symbol, name, asset_type (stock/etf/crypto/forex/commodity), exchange, sector, industry
- **Timestamps**: created_at, updated_at (UTC)

#### watchlists
- **Primary Key**: UUID
- **Purpose**: Store user's curated asset collections
- **Key Fields**: user_id (FK), name, description, color, icon, is_default
- **Timestamps**: created_at, updated_at (UTC)

#### watchlist_items
- **Primary Key**: UUID
- **Purpose**: Many-to-many relationship between watchlists and assets
- **Key Fields**: watchlist_id (FK), asset_id (FK), position, notes, price_alert_high, price_alert_low
- **Constraints**: Unique (watchlist_id, asset_id)
- **Timestamps**: created_at, updated_at (UTC)

### Time-Series Tables (Bigserial Primary Keys)

#### candles (Hypertable)
- **Primary Key**: Bigserial
- **Partitioned By**: ts (timestamp)
- **Chunk Interval**: 7 days
- **Purpose**: Store OHLCV (candlestick) data
- **Key Fields**: asset_id (FK), ts, interval (1m/5m/15m/30m/1h/4h/1d/1w/1M), open, high, low, close, volume, trades, vwap
- **Indexes**: (asset_id, ts, interval), (ts, asset_id)
- **Timestamp**: ts, created_at (UTC)

#### indicators
- **Primary Key**: Bigserial
- **Purpose**: Store computed technical indicators
- **Key Fields**: asset_id (FK), ts, indicator_type (sma/ema/rsi/macd/bbands/atr/obv/stoch/adx/cci), name, value, value2, value3, parameters (JSON), timeframe
- **Indexes**: (asset_id, indicator_type, ts), (asset_id, name, ts)
- **Timestamp**: ts, computed_at (UTC)

#### signals
- **Primary Key**: Bigserial
- **Purpose**: Store trading signals
- **Key Fields**: asset_id (FK), ts, signal_type (buy/sell/hold/strong_buy/strong_sell), strength, confidence, price, target_price, stop_loss, strategy, rationale, indicators_used (JSON), timeframe, is_active
- **Indexes**: (asset_id, ts), (asset_id, signal_type, ts), (is_active, ts)
- **Timestamps**: ts, generated_at, expires_at (UTC)

## Local Setup

### Using Docker (Recommended)

The docker-compose.yml includes a TimescaleDB service:

```bash
# Start TimescaleDB
docker-compose up timescaledb -d

# Check if TimescaleDB is ready
docker-compose exec timescaledb pg_isready -U trading_user

# Connect with psql
docker-compose exec timescaledb psql -U trading_user -d trading_manager
```

### Manual Installation

#### On macOS:
```bash
brew install timescaledb
timescaledb-tune --quiet --yes
brew services start postgresql
psql postgres -c "CREATE EXTENSION timescaledb;"
```

#### On Ubuntu/Debian:
```bash
sudo apt install postgresql-14 postgresql-client-14
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt update
sudo apt install timescaledb-2-postgresql-14
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql
sudo -u postgres psql -c "CREATE EXTENSION timescaledb;"
```

### Create Database and User

```sql
-- Create user and database
CREATE USER trading_user WITH PASSWORD 'trading_password';
CREATE DATABASE trading_manager OWNER trading_user;

-- Connect to database
\c trading_manager

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trading_manager TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
```

## Running Migrations

### Initialize Alembic (already done)

```bash
# Generate a new migration
alembic revision -m "migration description"

# Apply all migrations
alembic upgrade head

# Revert last migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Apply Initial Migration

```bash
# Run from project root
alembic upgrade head
```

This will:
1. Enable TimescaleDB extension
2. Create all enum types
3. Create all tables
4. Create indexes
5. Convert the `candles` table to a hypertable

## Hypertable Management

### Verify Hypertable Status

```sql
-- List all hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Check chunk information
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'candles'
ORDER BY range_start DESC;

-- Get hypertable stats
SELECT * FROM timescaledb_information.hypertable_stats
WHERE hypertable_name = 'candles';
```

### Compression Policy

Set up automatic compression for old data:

```sql
-- Enable compression
ALTER TABLE candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id'
);

-- Add compression policy (compress data older than 30 days)
SELECT add_compression_policy('candles', INTERVAL '30 days');

-- Check compression status
SELECT * FROM timescaledb_information.compression_settings
WHERE hypertable_name = 'candles';

-- Manually compress a chunk
SELECT compress_chunk(chunk_name)
FROM timescaledb_information.chunks
WHERE hypertable_name = 'candles' AND NOT is_compressed;
```

### Retention Policy

Automatically drop old data:

```sql
-- Add retention policy (keep only 1 year of data)
SELECT add_retention_policy('candles', INTERVAL '1 year');

-- Remove retention policy
SELECT remove_retention_policy('candles');

-- Check retention policies
SELECT * FROM timescaledb_information.jobs
WHERE proc_name LIKE '%retention%';
```

## Common Queries

### Get Latest Candles for an Asset

```sql
SELECT ts, open, high, low, close, volume
FROM candles
WHERE asset_id = 'your-asset-uuid-here'
  AND interval = '1d'
ORDER BY ts DESC
LIMIT 30;
```

### Get Latest Indicators

```sql
SELECT 
    a.symbol,
    i.name,
    i.value,
    i.ts
FROM indicators i
JOIN assets a ON a.id = i.asset_id
WHERE i.ts >= NOW() - INTERVAL '7 days'
ORDER BY a.symbol, i.ts DESC;
```

### Get Active Signals

```sql
SELECT 
    a.symbol,
    s.signal_type,
    s.strength,
    s.confidence,
    s.rationale,
    s.ts
FROM signals s
JOIN assets a ON a.id = s.asset_id
WHERE s.is_active = 'true'
ORDER BY s.ts DESC;
```

### Get Latest Signal Per Asset

```sql
WITH ranked_signals AS (
    SELECT 
        s.*,
        a.symbol,
        ROW_NUMBER() OVER (PARTITION BY s.asset_id ORDER BY s.ts DESC) as rn
    FROM signals s
    JOIN assets a ON a.id = s.asset_id
    WHERE s.is_active = 'true'
)
SELECT 
    symbol,
    signal_type,
    strength,
    confidence,
    rationale,
    ts
FROM ranked_signals
WHERE rn = 1
ORDER BY ts DESC;
```

### Price Statistics by Asset

```sql
SELECT 
    a.symbol,
    COUNT(*) as candle_count,
    MIN(c.ts) as first_date,
    MAX(c.ts) as last_date,
    MIN(c.low) as all_time_low,
    MAX(c.high) as all_time_high,
    AVG(c.close) as avg_price
FROM candles c
JOIN assets a ON a.id = c.asset_id
WHERE c.interval = '1d'
GROUP BY a.symbol
ORDER BY a.symbol;
```

### Recent Price Changes

```sql
WITH latest_prices AS (
    SELECT DISTINCT ON (asset_id)
        asset_id,
        close as current_price,
        ts as current_date
    FROM candles
    WHERE interval = '1d'
    ORDER BY asset_id, ts DESC
),
previous_prices AS (
    SELECT DISTINCT ON (c.asset_id)
        c.asset_id,
        c.close as previous_price
    FROM candles c
    JOIN latest_prices lp ON lp.asset_id = c.asset_id
    WHERE c.interval = '1d'
        AND c.ts < lp.current_date
    ORDER BY c.asset_id, c.ts DESC
)
SELECT 
    a.symbol,
    lp.current_price,
    pp.previous_price,
    ROUND(((lp.current_price - pp.previous_price) / pp.previous_price * 100)::numeric, 2) as pct_change
FROM latest_prices lp
JOIN previous_prices pp ON pp.asset_id = lp.asset_id
JOIN assets a ON a.id = lp.asset_id
ORDER BY pct_change DESC;
```

## Backup and Restore

### Using pg_dump

```bash
# Full backup
docker-compose exec timescaledb pg_dump -U trading_user -d trading_manager \
    -F c -f /tmp/backup.dump

# Copy from container
docker cp trading-timescaledb:/tmp/backup.dump ./backup.dump

# Restore
docker cp ./backup.dump trading-timescaledb:/tmp/backup.dump
docker-compose exec timescaledb pg_restore -U trading_user -d trading_manager \
    -F c /tmp/backup.dump
```

### Using TimescaleDB-specific Backup

```bash
# Create base backup
docker-compose exec timescaledb pg_basebackup -U trading_user \
    -D /tmp/backup -F tar -z -P

# For continuous archiving, configure WAL archiving in postgresql.conf
```

### Backup Only Schema

```bash
docker-compose exec timescaledb pg_dump -U trading_user -d trading_manager \
    --schema-only -f /tmp/schema.sql
```

### Backup Only Data

```bash
docker-compose exec timescaledb pg_dump -U trading_user -d trading_manager \
    --data-only -f /tmp/data.sql
```

## Performance Tuning

### Recommended PostgreSQL Settings

Add to `postgresql.conf` or set via Docker environment:

```ini
# Memory settings
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB

# TimescaleDB settings
timescaledb.max_background_workers = 8
max_worker_processes = 16
max_parallel_workers = 8
max_parallel_workers_per_gather = 4

# Write-ahead log
wal_buffers = 16MB
checkpoint_completion_target = 0.9
```

### Analyze Tables

```sql
-- Update statistics for query planner
ANALYZE candles;
ANALYZE indicators;
ANALYZE signals;

-- Or analyze all tables
ANALYZE;
```

### Monitor Performance

```sql
-- Check slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Managed Services

### Timescale Cloud

1. Create account at https://www.timescale.com/
2. Create a new service
3. Copy the connection string
4. Update your `.env` file:
   ```
   DATABASE_URL=postgres://user:password@host.timescaledb.io:port/database?sslmode=require
   ```

### AWS RDS with TimescaleDB

TimescaleDB is not available as a managed service on AWS RDS. Use Timescale Cloud or self-hosted on EC2.

### Self-Hosted on DigitalOcean

1. Create a Droplet with PostgreSQL
2. Follow manual installation instructions above
3. Configure firewall to allow connections from your backend servers
4. Use SSL for connections in production

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql "postgresql://trading_user:trading_password@localhost:5432/trading_manager"

# Check if TimescaleDB extension is loaded
SELECT * FROM pg_extension WHERE extname = 'timescaledb';
```

### Hypertable Not Working

```sql
-- Check if table is a hypertable
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'candles';

-- If not, convert it
SELECT create_hypertable('candles', 'ts', chunk_time_interval => INTERVAL '7 days');
```

### Migration Issues

```bash
# Reset to a specific revision
alembic downgrade <revision>

# Stamp database at specific revision (without running migrations)
alembic stamp <revision>

# Show SQL without executing
alembic upgrade head --sql
```
