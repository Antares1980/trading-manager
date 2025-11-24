# Celery Worker and Beat Configuration

This document describes how to run and configure Celery workers and beat scheduler for background task processing.

## Overview

The Trading Manager uses Celery for background processing of:
- **Technical Indicators**: Computing RSI, MACD, SMA, EMA, Bollinger Bands, etc.
- **Trading Signals**: Generating buy/sell signals based on indicator analysis
- **Scheduled Tasks**: Daily computation of indicators and signals (optional)

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Flask     │      │   Celery    │      │   Celery    │
│   Backend   │─────▶│   Worker    │◀─────│    Beat     │
│             │      │             │      │  (Scheduler)│
└─────────────┘      └─────────────┘      └─────────────┘
      │                      │                     │
      │                      │                     │
      ▼                      ▼                     ▼
┌─────────────────────────────────────────────────┐
│              Redis (Broker & Backend)           │
└─────────────────────────────────────────────────┘
```

## Running Celery Locally

### Prerequisites

1. Redis must be running:
```bash
# Using Docker
docker-compose up redis -d

# Or install locally
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu
```

2. Database must be initialized:
```bash
# Run migrations
alembic upgrade head

# Seed with demo data (optional)
python -m flask db-seed
```

### Start Celery Worker

```bash
# Basic worker
celery -A backend.tasks.celery_app worker --loglevel=info

# Worker with specific queues
celery -A backend.tasks.celery_app worker --loglevel=info --queues=indicators,signals

# Worker with concurrency control
celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=4

# Worker with autoreload (for development)
celery -A backend.tasks.celery_app worker --loglevel=info --autoreload
```

### Start Celery Beat (Scheduler)

Celery Beat scheduling is **disabled by default**. To enable:

1. Set environment variable:
```bash
export CELERY_ENABLE_BEAT=true
```

2. Start beat:
```bash
celery -A backend.tasks.celery_app beat --loglevel=info
```

Or run combined worker + beat:
```bash
celery -A backend.tasks.celery_app worker --beat --loglevel=info
```

## Running with Docker

### Using Docker Compose

The docker-compose.yml includes worker and beat services:

```bash
# Start worker
docker-compose up worker -d

# View worker logs
docker-compose logs -f worker

# Enable beat (uncomment in docker-compose.yml first)
docker-compose up beat -d

# Scale workers
docker-compose up --scale worker=3
```

## Task Configuration

### Available Tasks

#### compute_indicators
Computes technical indicators for assets.

**Parameters:**
- `asset_id` (optional): Specific asset to process
- `lookback_days` (default: 100): Number of days to analyze

**Schedule:** Daily at midnight (when beat is enabled)

**Example:**
```python
from backend.tasks.indicators import compute_indicators

# Compute for all assets
result = compute_indicators.delay()

# Compute for specific asset
result = compute_indicators.delay(asset_id='uuid-here', lookback_days=50)

# Get result
print(result.get(timeout=300))
```

#### compute_signals
Generates trading signals based on indicators.

**Parameters:**
- `asset_id` (optional): Specific asset to process

**Schedule:** Daily at midnight (when beat is enabled)

**Example:**
```python
from backend.tasks.signals import compute_signals

# Generate signals for all assets
result = compute_signals.delay()

# Generate for specific asset
result = compute_signals.delay(asset_id='uuid-here')
```

#### deactivate_expired_signals
Deactivates signals that have passed their expiration time.

**Example:**
```python
from backend.tasks.signals import deactivate_expired_signals

result = deactivate_expired_signals.delay()
```

### Task Results

```python
# Check task status
from backend.tasks import celery_app

result = celery_app.AsyncResult('task-id')
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.info)   # Task result or error info

# Wait for result with timeout
try:
    output = result.get(timeout=300)  # 5 minutes
    print(output)
except TimeoutError:
    print("Task timed out")
```

## Monitoring

### Flower - Web-based Monitoring

Install and run Flower:

```bash
# Install Flower
pip install flower

# Start Flower
celery -A backend.tasks.celery_app flower --port=5555

# Access at http://localhost:5555
```

Or add to docker-compose.yml:
```yaml
flower:
  image: mher/flower
  command: celery flower --broker=redis://redis:6379/0
  ports:
    - "5555:5555"
  depends_on:
    - redis
```

### Command Line Monitoring

```bash
# List active tasks
celery -A backend.tasks.celery_app inspect active

# List scheduled tasks
celery -A backend.tasks.celery_app inspect scheduled

# List registered tasks
celery -A backend.tasks.celery_app inspect registered

# Worker statistics
celery -A backend.tasks.celery_app inspect stats

# List queues
celery -A backend.tasks.celery_app inspect active_queues
```

### Redis CLI Monitoring

```bash
# Connect to Redis
redis-cli

# List all keys
KEYS *

# Monitor commands in real-time
MONITOR

# Check queue length
LLEN celery

# View task info
GET celery-task-meta-<task-id>
```

## Task Queues

Tasks are routed to specific queues:

- **indicators**: Indicator computation tasks
- **signals**: Signal generation tasks
- **default**: All other tasks

### Start Worker for Specific Queue

```bash
celery -A backend.tasks.celery_app worker --loglevel=info --queues=indicators

celery -A backend.tasks.celery_app worker --loglevel=info --queues=signals

# Multiple queues
celery -A backend.tasks.celery_app worker --loglevel=info --queues=indicators,signals,default
```

## Performance Tuning

### Worker Configuration

```bash
# Adjust concurrency (number of worker processes)
celery -A backend.tasks.celery_app worker --concurrency=8

# Use threading instead of multiprocessing
celery -A backend.tasks.celery_app worker --pool=threads --concurrency=10

# Set task time limits
celery -A backend.tasks.celery_app worker \
    --time-limit=3600 \
    --soft-time-limit=3000
```

### Memory Management

```bash
# Restart worker after N tasks to prevent memory leaks
celery -A backend.tasks.celery_app worker --max-tasks-per-child=100

# Set memory limits (in KB)
celery -A backend.tasks.celery_app worker --max-memory-per-child=500000
```

### Prefetch Settings

```bash
# Disable prefetching (good for long-running tasks)
celery -A backend.tasks.celery_app worker --prefetch-multiplier=1

# Increase prefetching (good for short tasks)
celery -A backend.tasks.celery_app worker --prefetch-multiplier=4
```

## Troubleshooting

### Worker Won't Start

1. Check Redis connection:
```bash
redis-cli ping  # Should return PONG
```

2. Check environment variables:
```bash
echo $DATABASE_URL
echo $REDIS_URL
```

3. Verify Celery app loads:
```python
from backend.tasks import celery_app
print(celery_app.conf)
```

### Tasks Not Executing

1. Verify task is registered:
```bash
celery -A backend.tasks.celery_app inspect registered
```

2. Check active tasks:
```bash
celery -A backend.tasks.celery_app inspect active
```

3. Check for errors in worker logs

### Beat Schedule Not Working

1. Ensure `CELERY_ENABLE_BEAT=true` is set

2. Check beat is running:
```bash
ps aux | grep celery
```

3. Verify schedule configuration:
```python
from backend.tasks import celery_app
print(celery_app.conf.beat_schedule)
```

### Task Timeout

Increase time limits in worker command:
```bash
celery -A backend.tasks.celery_app worker \
    --time-limit=7200 \
    --soft-time-limit=7000
```

Or in task decorator:
```python
@celery_app.task(time_limit=3600, soft_time_limit=3000)
def long_running_task():
    pass
```

## Production Recommendations

### Systemd Service (Linux)

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Service
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/trading-manager
Environment="CELERY_BIN=/path/to/venv/bin/celery"
ExecStart=/path/to/venv/bin/celery -A backend.tasks.celery_app worker --loglevel=info --detach
ExecStop=/path/to/venv/bin/celery -A backend.tasks.celery_app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

### Supervisor (Alternative)

Install supervisor:
```bash
pip install supervisor
```

Create config `/etc/supervisor/conf.d/celery.conf`:
```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A backend.tasks.celery_app worker --loglevel=info
directory=/path/to/trading-manager
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A backend.tasks.celery_app beat --loglevel=info
directory=/path/to/trading-manager
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### Docker Production

Use separate containers for worker and beat with proper resource limits:

```yaml
worker:
  image: your-backend-image
  command: celery -A backend.tasks.celery_app worker --loglevel=info --concurrency=4
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 2G
  restart: unless-stopped
```

## Best Practices

1. **Use task retries** for transient failures:
```python
@celery_app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        # task logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

2. **Set task time limits** to prevent hanging tasks

3. **Monitor task execution time** and optimize slow tasks

4. **Use task routing** to separate different workloads

5. **Enable task result expiration** to prevent Redis bloat:
```python
CELERY_RESULT_EXPIRES = 3600  # 1 hour
```

6. **Log task progress** for long-running tasks

7. **Implement idempotency** - tasks should be safe to retry

8. **Use database transactions** properly in tasks

9. **Monitor worker health** with heartbeats

10. **Scale workers horizontally** for increased throughput
