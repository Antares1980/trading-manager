# API Documentation

Complete REST API documentation for the Trading Manager application.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Authentication Endpoints

### POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_admin": false
  }
}
```

### POST /api/auth/login

Authenticate and receive access tokens.

**Request Body:**
```json
{
  "username": "demo",
  "password": "demo123"
}
```

**Response (200):**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "username": "demo",
    "email": "demo@trading-manager.com"
  }
}
```

### GET /api/auth/verify

Verify token validity (requires authentication).

**Response (200):**
```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "username": "demo",
    "email": "demo@trading-manager.com"
  }
}
```

### POST /api/auth/refresh

Refresh access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### GET /api/auth/me

Get current user information (requires authentication).

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "username": "demo",
    "email": "demo@trading-manager.com",
    "full_name": "Demo User",
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
    "last_login": "2024-01-01T12:00:00+00:00"
  }
}
```

## Watchlist Endpoints

### GET /api/watchlists/

Get all watchlists for the current user (requires authentication).

**Response (200):**
```json
{
  "watchlists": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "name": "Tech Favorites",
      "description": "My favorite technology stocks",
      "color": "#3b82f6",
      "icon": "laptop",
      "is_default": "true",
      "items": [...],
      "item_count": 5
    }
  ],
  "count": 2
}
```

### GET /api/watchlists/<watchlist_id>

Get a specific watchlist (requires authentication).

**Response (200):**
```json
{
  "watchlist": {
    "id": "uuid",
    "name": "Tech Favorites",
    "items": [...]
  }
}
```

### POST /api/watchlists/

Create a new watchlist (requires authentication).

**Request Body:**
```json
{
  "name": "My Watchlist",
  "description": "Description",
  "color": "#10b981",
  "icon": "star"
}
```

### PUT /api/watchlists/<watchlist_id>

Update a watchlist (requires authentication).

### DELETE /api/watchlists/<watchlist_id>

Delete a watchlist (requires authentication).

### POST /api/watchlists/<watchlist_id>/items

Add an asset to a watchlist (requires authentication).

**Request Body:**
```json
{
  "asset_id": "uuid",
  "notes": "Tracking this stock",
  "price_alert_high": "200.00",
  "price_alert_low": "150.00"
}
```

### DELETE /api/watchlists/<watchlist_id>/items/<item_id>

Remove an asset from a watchlist (requires authentication).

## Asset Endpoints

### GET /api/assets/

Get all assets with optional filtering.

**Query Parameters:**
- `asset_type`: Filter by type (stock, etf, crypto, forex, commodity)
- `search`: Search by symbol or name
- `limit`: Max results (default: 100)
- `offset`: Pagination offset (default: 0)

**Response (200):**
```json
{
  "assets": [
    {
      "id": "uuid",
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "asset_type": "stock",
      "exchange": "NASDAQ",
      "currency": "USD",
      "sector": "Technology",
      "industry": "Consumer Electronics"
    }
  ],
  "count": 10,
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

### GET /api/assets/<asset_id>

Get a specific asset by ID or symbol.

### POST /api/assets/

Create a new asset (requires authentication).

**Request Body:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "asset_type": "stock",
  "exchange": "NASDAQ",
  "currency": "USD",
  "sector": "Technology",
  "industry": "Consumer Electronics"
}
```

### PUT /api/assets/<asset_id>

Update an asset (requires authentication).

## Candle Endpoints

### GET /api/candles/

Get candle data with filtering.

**Query Parameters (Required):**
- `asset_id`: Asset UUID

**Optional Parameters:**
- `interval`: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M) [default: 1d]
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `limit`: Max results (default: 1000)

**Response (200):**
```json
{
  "candles": [
    {
      "id": 1,
      "asset_id": "uuid",
      "ts": "2024-01-01T00:00:00+00:00",
      "interval": "1d",
      "open": "150.00",
      "high": "155.00",
      "low": "149.00",
      "close": "154.00",
      "volume": "5000000"
    }
  ],
  "count": 365,
  "asset": {...}
}
```

### GET /api/candles/<candle_id>

Get a specific candle by ID.

### POST /api/candles/

Create a new candle entry (requires authentication).

### GET /api/candles/latest

Get the latest candle for each asset.

**Query Parameters:**
- `interval`: Candle interval (default: 1d)
- `asset_ids`: Comma-separated list of asset IDs

## Indicator Endpoints

### GET /api/indicators/

Get indicators with filtering.

**Query Parameters (Required):**
- `asset_id`: Asset UUID

**Optional Parameters:**
- `indicator_type`: Filter by type (sma, ema, rsi, macd, bbands, atr, obv)
- `name`: Filter by indicator name
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `limit`: Max results (default: 500)

**Response (200):**
```json
{
  "indicators": [
    {
      "id": 1,
      "asset_id": "uuid",
      "ts": "2024-01-01T00:00:00+00:00",
      "indicator_type": "rsi",
      "name": "RSI_14",
      "value": "45.50",
      "parameters": {"period": 14},
      "timeframe": "1d"
    }
  ],
  "count": 100,
  "asset": {...}
}
```

### GET /api/indicators/<indicator_id>

Get a specific indicator by ID.

### POST /api/indicators/

Create a new indicator entry (requires authentication).

### GET /api/indicators/types

Get all available indicator types.

## Signal Endpoints

### GET /api/signals/

Get signals with filtering.

**Query Parameters:**
- `asset_id`: Filter by asset ID
- `signal_type`: Filter by type (buy, sell, hold, strong_buy, strong_sell)
- `is_active`: Filter by active status ('true' or 'false')
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `limit`: Max results (default: 100)

**Response (200):**
```json
{
  "signals": [
    {
      "id": 1,
      "asset_id": "uuid",
      "ts": "2024-01-01T00:00:00+00:00",
      "signal_type": "buy",
      "strength": "moderate",
      "confidence": 65.0,
      "price": "150.00",
      "strategy": "RSI_MA_MACD_Combined",
      "rationale": "RSI oversold (28.5); SMA 20 above SMA 50",
      "indicators_used": ["RSI_14", "SMA_20", "SMA_50"],
      "timeframe": "1d",
      "is_active": "true"
    }
  ],
  "count": 10
}
```

### GET /api/signals/<signal_id>

Get a specific signal by ID.

### POST /api/signals/

Create a new signal (requires authentication).

### PUT /api/signals/<signal_id>

Update a signal (requires authentication).

### GET /api/signals/latest

Get the latest active signal for each asset.

**Query Parameters:**
- `asset_ids`: Comma-separated list of asset IDs

### GET /api/signals/types

Get all available signal types and strengths.

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "error": "Validation error message"
}
```

**401 Unauthorized:**
```json
{
  "error": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "error": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

## Rate Limiting

Currently no rate limiting is implemented. In production, consider adding rate limiting to prevent abuse.

## CORS

CORS is enabled for all origins in development mode. Configure appropriately for production.
