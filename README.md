# Trading Manager

A comprehensive trading analysis platform with Flask backend API and interactive web frontend for technical analysis of stocks. Features real-time market data fetching, technical indicator calculations, and beautiful chart visualizations.

## 🚀 Features

### Web Application
- **Interactive Dashboard**: Modern, responsive web interface for stock analysis
- **Real-time Charts**: Visualize stock prices with Chart.js integration
- **Technical Indicators**: RSI, MACD, SMA, EMA, Bollinger Bands, ATR, OBV
- **Trading Signals**: Automated signal generation based on technical analysis
- **User Authentication**: JWT-based authentication system
- **RESTful API**: Well-documented API endpoints for market data and analysis

### CLI Tool
- **Batch Processing**: Download historical OHLC data for multiple tickers
- **Fundamentals Data**: Optional P/E, EPS, ROE, dividend yield
- **Quarterly Data**: Merge quarterly income statement data
- **Flexible Output**: Export to CSV for further analysis

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)

## 🔧 Installation

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

### Docker Installation

Build and run with Docker:
```bash
docker build -t trading-manager .
docker run -p 5000:5000 trading-manager
```

Or use Docker Compose:
```bash
docker-compose up
```

## 🎯 Quick Start

### Running the Web Application

Start the Flask server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Login with demo credentials:
   - Username: `demo`, Password: `demo123`
   - OR Username: `admin`, Password: `admin123`
3. Enter a stock ticker (e.g., AAPL, GOOGL, MSFT)
4. Click "Analyze" to view charts and technical indicators
5. Toggle different indicators on the price chart

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