# Trading Manager

A comprehensive trading analysis platform with Flask backend API, TimescaleDB for time-series data storage, Celery for background processing, and interactive web frontend for technical analysis of stocks.

## 🚀 Features

### New: Persistent Storage & Background Processing
- **TimescaleDB Integration**: Optimized time-series database for OHLCV data with automatic compression and retention
- **Background Tasks**: Celery-based async processing for technical indicators and signal generation
- **RESTful API**: Complete CRUD operations for users, watchlists, assets, candles, indicators, and signals
- **Database Migrations**: Alembic for schema versioning and management
- **Seed Data**: Demo users and 365 days of historical data for 12+ assets

### Web Application
- **Interactive Dashboard**: Modern, responsive web interface for stock analysis
- **Real-time Charts**: Visualize stock prices with Chart.js integration
- **Technical Indicators**: RSI, MACD, SMA, EMA, Bollinger Bands, ATR, OBV
- **Trading Signals**: Automated signal generation based on technical analysis
- **User Authentication**: JWT-based authentication system with bcrypt password hashing
- **Watchlists**: Create and manage custom asset watchlists with price alerts

### CLI Tool
- **Batch Processing**: Download historical OHLC data for multiple tickers
- **Fundamentals Data**: Optional P/E, EPS, ROE, dividend yield
- **Quarterly Data**: Merge quarterly income statement data
- **Flexible Output**: Export to CSV for further analysis

## 📋 Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (recommended)
- PostgreSQL/TimescaleDB (via Docker or local install)
- Redis (via Docker or local install)

## 🚀 Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Antares1980/trading-manager.git
cd trading-manager

# Copy environment file
cp .env.example .env

# Start all services (TimescaleDB, Redis, Backend, Worker, PgAdmin)
docker-compose up --build

# In a new terminal, run database migrations
docker-compose exec backend alembic upgrade head

# Seed the database with demo data
docker-compose exec backend python -m flask db-seed
```

**Access the application:**
- Web UI: http://localhost:5000
- PgAdmin: http://localhost:5050 (admin@trading-manager.com / admin123)
- API: http://localhost:5000/api

**Demo credentials:**
- Username: `demo`, Password: `demo123`
- Username: `admin`, Password: `admin123`

**What's included:**
- 12+ demo assets (AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, JPM, V, WMT, SPY, BTC-USD)
- 365 days of historical candle data per asset
- Pre-configured watchlists
- Ready-to-use PostgreSQL with TimescaleDB extension
- Celery worker for background tasks
- Redis for Celery broker and caching

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Database Setup & Queries](docs/db.md)**: TimescaleDB configuration, hypertables, SQL examples
- **[API Documentation](docs/api.md)**: Complete API endpoint reference with examples
- **[Worker Configuration](docs/worker.md)**: Celery setup, task management, monitoring
- **[Developer Guide](docs/dev.md)**: Development workflow, debugging, testing
- **[Security Best Practices](docs/security.md)**: Authentication, secrets, database security

## 🔧 Manual Installation

### Standard Installation

1. **Clone the repository**
```bash
git clone https://github.com/Antares1980/trading-manager.git
cd trading-manager
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv .venv
```

3. **Activate the virtual environment**
- On Windows PowerShell:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- On Windows CMD:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Set up services**

You'll need PostgreSQL/TimescaleDB and Redis running:

```bash
# Start services with Docker
docker-compose up timescaledb redis -d

# Or install locally (macOS)
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

6. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

7. **Run database migrations**
```bash
alembic upgrade head
```

8. **Seed demo data (optional)**
```bash
python -m flask db-seed
```

9. **Start the application**
```bash
# Flask backend
python app.py

# Celery worker (in another terminal)
celery -A backend.tasks.celery_app worker --loglevel=info
```

The application will be available at `http://localhost:5000`

## 🎯 Using the Application

### Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Login with demo credentials:
   - Username: `demo`, Password: `demo123`
   - OR Username: `admin`, Password: `admin123`
3. Create watchlists and add assets
4. View historical candle data and technical indicators
5. Analyze trading signals generated by the system

### API Usage

The application provides a complete REST API. See [API Documentation](docs/api.md) for details.

**Example: Get all assets**
```bash
curl http://localhost:5000/api/assets/
```

**Example: Get candle data**
```bash
curl "http://localhost:5000/api/candles/?asset_id=<uuid>&interval=1d&limit=30"
```

**Example: Login and get token**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

### Background Tasks

Compute indicators and signals for assets:

```python
from backend.tasks.indicators import compute_indicators
from backend.tasks.signals import compute_signals

# Compute indicators for all assets
result = compute_indicators.delay()

# Compute signals for all assets
result = compute_signals.delay()

# Check result
print(result.get(timeout=300))
```

Or via CLI (if worker is running):

```bash
# Using Python
python -c "from backend.tasks.indicators import compute_indicators; compute_indicators.delay()"
```

### API Endpoints

#### Market Data
- `GET /api/market/stock/<ticker>` - Get historical stock data
- `GET /api/market/stock/<ticker>/info` - Get stock information
- `GET /api/market/search?q=<query>` - Search for stocks

#### Technical Analysis
- `GET /api/analysis/indicators/<ticker>` - Calculate technical indicators
- `GET /api/analysis/summary/<ticker>` - Get analysis summary with signals

#### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/register` - Register new user
- `GET /api/auth/verify` - Verify JWT token

Example API request:
```bash
curl http://localhost:5000/api/market/stock/AAPL?start=2024-01-01&end=2024-12-31
```

## 📊 CLI Usage

The CLI tool (`trading_manager_cli.py`) allows batch processing of stock data.

### Basic Usage

```bash
python trading_manager_cli.py \
  --input data/example_stocks.csv \
  --output prices.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

### With Fundamentals

```bash
python trading_manager_cli.py \
  --input data/example_stocks.csv \
  --output fundamentals.csv \
  --fundamentals \
  --quarterly-fundamentals \
  --log-level DEBUG
```

### CLI Options

- `--input`: CSV file with a `ticker` column (required)
- `--output`: Output CSV filename (required)
- `--start`: Start date (YYYY-MM-DD, default: 2023-01-01)
- `--end`: End date (YYYY-MM-DD, default: today)
- `--fundamentals`: Include P/E, EPS, ROE, dividend yield
- `--quarterly-fundamentals`: Include quarterly income statement data
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## 🏗️ Project Structure

```
trading-manager/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── README.md                   # This file
├── backend/                    # Backend Python code
│   ├── api/                    # API route handlers
│   │   ├── market_routes.py   # Market data endpoints
│   │   ├── analysis_routes.py # Technical analysis endpoints
│   │   └── auth_routes.py     # Authentication endpoints
│   ├── models/                 # Data models (future expansion)
│   └── utils/                  # Utility modules
│       ├── market_data.py     # Yahoo Finance integration
│       └── technical_analysis.py # TA calculations
├── frontend/                   # Frontend files
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Application styles
│   │   └── js/
│   │       └── app.js         # Frontend JavaScript
│   └── templates/
│       └── index.html         # Main HTML template
├── config/                     # Configuration files
│   └── config.example.py      # Example configuration
├── data/                       # Data directory
│   └── example_stocks.csv     # Example ticker list
├── tests/                      # Test directory (future expansion)
├── trading_manager_cli.py     # CLI tool
├── stock_fetcher.py           # Legacy CLI (v1)
└── stock_fetcher_v2.py        # Legacy CLI (v2)
```

## 🔐 Security Notes

- Default credentials are for **development only**
- Change `SECRET_KEY` and `JWT_SECRET_KEY` in production
- User data is stored in-memory (use a database in production)
- Enable HTTPS in production environments

## 🛠️ Development

### Environment Variables

```bash
export FLASK_DEBUG=True
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
export PORT=5000
```

### Running Tests

```bash
# Tests will be added in future releases
python -m pytest tests/
```

## 📚 Technical Indicators Supported

- **SMA** (Simple Moving Average) - 20, 50 periods
- **EMA** (Exponential Moving Average) - 20, 50 periods
- **RSI** (Relative Strength Index) - 14 period
- **MACD** (Moving Average Convergence Divergence)
- **Bollinger Bands** - 20 period, 2 standard deviations
- **ATR** (Average True Range) - 14 period
- **OBV** (On-Balance Volume)

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Use a different port
export PORT=5001
python app.py
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Yahoo Finance Rate Limiting
- Add delays between requests
- Use the CLI tool with smaller batches
- Check `--log-level DEBUG` for detailed error messages

## 📝 Example Data

Example ticker list is provided in `data/example_stocks.csv`:
```csv
ticker
AAPL
GOOGL
MSFT
AMZN
TSLA
META
NVDA
JPM
V
WMT
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License & Attribution

This tool is built with:
- Flask (web framework)
- pandas (data manipulation)
- yahooquery (Yahoo Finance API)
- ta (technical analysis library)
- Chart.js (charting library)

**For educational and personal use only.** Not financial advice. Respect Yahoo Finance's terms of service when accessing their data.

## ⚠️ Disclaimer

This software is for educational purposes only. Do not use it for actual trading decisions. The authors and contributors are not responsible for any financial losses incurred from using this software.