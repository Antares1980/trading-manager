// Trading Manager Frontend JavaScript

// API base URL
const API_BASE = window.location.origin;

// State management
let currentTicker = null;
let authToken = null;
let priceChart = null;
let rsiChart = null;
let macdChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupEventListeners();
    loadExampleData();
});

// Authentication
function initializeAuth() {
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        verifyToken();
    }
}

function verifyToken() {
    fetch(`${API_BASE}/api/auth/verify`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            showUserInfo(data.user);
        } else {
            logout();
        }
    })
    .catch(() => logout());
}

function showUserInfo(user) {
    document.getElementById('login-btn').style.display = 'none';
    document.getElementById('user-info').style.display = 'flex';
    document.getElementById('username').textContent = user.username;
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    document.getElementById('login-btn').style.display = 'block';
    document.getElementById('user-info').style.display = 'none';
}

// Event Listeners
function setupEventListeners() {
    // Search functionality
    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('ticker-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    // Indicator toggles
    document.getElementById('toggle-sma').addEventListener('change', updatePriceChart);
    document.getElementById('toggle-ema').addEventListener('change', updatePriceChart);
    document.getElementById('toggle-bbands').addEventListener('change', updatePriceChart);
    
    // Login modal
    document.getElementById('login-btn').addEventListener('click', showLoginModal);
    document.getElementById('logout-btn').addEventListener('click', logout);
    document.querySelector('.close').addEventListener('click', hideLoginModal);
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Click outside modal to close
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('login-modal');
        if (e.target === modal) {
            hideLoginModal();
        }
    });
}

// Login Modal
function showLoginModal() {
    document.getElementById('login-modal').style.display = 'flex';
}

function hideLoginModal() {
    document.getElementById('login-modal').style.display = 'none';
}

function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            showUserInfo(data.user);
            hideLoginModal();
        } else {
            alert(data.error || 'Login failed');
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    });
}

// Search and Load Data
function handleSearch() {
    const ticker = document.getElementById('ticker-input').value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    currentTicker = ticker;
    loadStockData(ticker);
}

function loadStockData(ticker) {
    showLoading();
    hideError();
    
    // Fetch stock info
    fetch(`${API_BASE}/api/market/stock/${ticker}/info`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayStockInfo(data);
        })
        .catch(error => {
            console.error('Error fetching stock info:', error);
        });
    
    // Fetch stock data with indicators
    const indicators = 'sma,ema,rsi,macd,bbands';
    fetch(`${API_BASE}/api/analysis/indicators/${ticker}?indicators=${indicators}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayCharts(data);
            hideLoading();
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            showError(error.message);
            hideLoading();
        });
    
    // Fetch analysis summary
    fetch(`${API_BASE}/api/analysis/summary/${ticker}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.warn('Error fetching summary:', data.error);
                return;
            }
            displaySignals(data);
        })
        .catch(error => {
            console.error('Error fetching summary:', error);
        });
}

function loadExampleData() {
    // Load example data on page load
    const exampleTicker = 'AAPL';
    document.getElementById('ticker-input').value = exampleTicker;
    loadStockData(exampleTicker);
}

// Display Functions
function displayStockInfo(info) {
    document.getElementById('stock-info').style.display = 'block';
    document.getElementById('stock-name').textContent = `${info.name} (${info.symbol})`;
    document.getElementById('current-price').textContent = `$${info.current_price?.toFixed(2) || 'N/A'}`;
    document.getElementById('volume').textContent = formatNumber(info.volume);
    document.getElementById('pe-ratio').textContent = info.pe_ratio?.toFixed(2) || 'N/A';
    document.getElementById('market-cap').textContent = formatNumber(info.market_cap);
}

function displayCharts(data) {
    const stockData = data.data;
    
    if (!stockData || stockData.length === 0) {
        showError('No data available for this ticker');
        return;
    }
    
    // Show chart sections
    document.getElementById('chart-section').style.display = 'block';
    document.getElementById('indicators-section').style.display = 'block';
    
    // Create price chart
    createPriceChart(stockData);
    
    // Create RSI chart
    createRSIChart(stockData);
    
    // Create MACD chart
    createMACDChart(stockData);
}

function createPriceChart(data) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    const dates = data.map(d => d.date);
    const prices = data.map(d => d.close);
    const sma20 = data.map(d => d.sma_20);
    const sma50 = data.map(d => d.sma_50);
    const ema20 = data.map(d => d.ema_20);
    const ema50 = data.map(d => d.ema_50);
    const bbUpper = data.map(d => d.bb_upper);
    const bbLower = data.map(d => d.bb_lower);
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Close Price',
                    data: prices,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'SMA 20',
                    data: sma20,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    fill: false,
                    hidden: !document.getElementById('toggle-sma').checked
                },
                {
                    label: 'SMA 50',
                    data: sma50,
                    borderColor: '#059669',
                    borderWidth: 2,
                    fill: false,
                    hidden: !document.getElementById('toggle-sma').checked
                },
                {
                    label: 'EMA 20',
                    data: ema20,
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    fill: false,
                    hidden: !document.getElementById('toggle-ema').checked
                },
                {
                    label: 'EMA 50',
                    data: ema50,
                    borderColor: '#d97706',
                    borderWidth: 2,
                    fill: false,
                    hidden: !document.getElementById('toggle-ema').checked
                },
                {
                    label: 'BB Upper',
                    data: bbUpper,
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    hidden: !document.getElementById('toggle-bbands').checked
                },
                {
                    label: 'BB Lower',
                    data: bbLower,
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    hidden: !document.getElementById('toggle-bbands').checked
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    display: true,
                    position: 'right'
                }
            }
        }
    });
}

function createRSIChart(data) {
    const ctx = document.getElementById('rsi-chart').getContext('2d');
    
    const dates = data.map(d => d.date);
    const rsi = data.map(d => d.rsi);
    
    // Get latest RSI value
    const latestRSI = rsi[rsi.length - 1];
    if (latestRSI) {
        document.getElementById('rsi-value').textContent = latestRSI.toFixed(2);
        
        const rsiSignal = latestRSI > 70 ? 'overbought' : latestRSI < 30 ? 'oversold' : 'neutral';
        const signalBadge = document.getElementById('rsi-signal');
        signalBadge.textContent = rsiSignal.toUpperCase();
        signalBadge.className = `signal-badge ${rsiSignal}`;
    }
    
    if (rsiChart) {
        rsiChart.destroy();
    }
    
    rsiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'RSI',
                data: rsi,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value;
                        }
                    }
                }
            }
        }
    });
}

function createMACDChart(data) {
    const ctx = document.getElementById('macd-chart').getContext('2d');
    
    const dates = data.map(d => d.date);
    const macd = data.map(d => d.macd);
    const macdSignal = data.map(d => d.macd_signal);
    const macdDiff = data.map(d => d.macd_diff);
    
    // Get latest MACD values
    const latestMACD = macd[macd.length - 1];
    const latestSignal = macdSignal[macdSignal.length - 1];
    if (latestMACD && latestSignal) {
        document.getElementById('macd-value').textContent = latestMACD.toFixed(2);
        
        const macdTrend = latestMACD > latestSignal ? 'bullish' : 'bearish';
        const signalBadge = document.getElementById('macd-signal');
        signalBadge.textContent = macdTrend.toUpperCase();
        signalBadge.className = `signal-badge ${macdTrend}`;
    }
    
    if (macdChart) {
        macdChart.destroy();
    }
    
    macdChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'MACD',
                    data: macd,
                    borderColor: '#2563eb',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'Signal',
                    data: macdSignal,
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: false
                }
            }
        }
    });
}

function displaySignals(data) {
    document.getElementById('signals-section').style.display = 'block';
    
    const signalsList = document.getElementById('signals-list');
    signalsList.innerHTML = '';
    
    if (!data.signals || data.signals.length === 0) {
        signalsList.innerHTML = '<p>No significant signals detected.</p>';
        return;
    }
    
    data.signals.forEach(signal => {
        const signalItem = document.createElement('div');
        signalItem.className = `signal-item ${signal.signal}`;
        signalItem.innerHTML = `
            <div>
                <strong>${signal.type}</strong>: ${signal.signal}
                ${signal.value ? ` (${typeof signal.value === 'number' ? signal.value.toFixed(2) : signal.value})` : ''}
            </div>
            <span class="signal-badge ${signal.signal}">${signal.signal.toUpperCase()}</span>
        `;
        signalsList.appendChild(signalItem);
    });
}

function updatePriceChart() {
    if (priceChart && currentTicker) {
        // Update dataset visibility based on toggles
        priceChart.data.datasets[1].hidden = !document.getElementById('toggle-sma').checked; // SMA 20
        priceChart.data.datasets[2].hidden = !document.getElementById('toggle-sma').checked; // SMA 50
        priceChart.data.datasets[3].hidden = !document.getElementById('toggle-ema').checked; // EMA 20
        priceChart.data.datasets[4].hidden = !document.getElementById('toggle-ema').checked; // EMA 50
        priceChart.data.datasets[5].hidden = !document.getElementById('toggle-bbands').checked; // BB Upper
        priceChart.data.datasets[6].hidden = !document.getElementById('toggle-bbands').checked; // BB Lower
        priceChart.update();
    }
}

// Utility Functions
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}

function formatNumber(num) {
    if (!num) return 'N/A';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toLocaleString();
}
