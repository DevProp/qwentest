# SMC Trader - Smart Money Concepts Analyzer

A professional web application for analyzing Binance cryptocurrencies using Smart Money Concepts (SMC) trading methodology.

## Features

### Core SMC Indicators
- **Order Blocks (OB)**: Identify institutional order accumulation zones
- **Fair Value Gaps (FVG)**: Detect imbalance zones where price moved too quickly
- **Break of Structure (BOS)**: Track market structure breaks in trend direction
- **Change of Character (CHoCH)**: Identify potential trend reversals
- **Liquidity Pools**: Find areas where stop losses cluster
- **Triangle Patterns**: Auto-detect ascending, descending, and symmetrical triangles
- **Premium/Discount Zones**: Fibonacci-based optimal entry zones

### Trading Signals
The app generates comprehensive trading signals with:
- Clear entry price
- Stop loss levels
- Multiple take profit targets (TP1, TP2, TP3)
- Risk/reward ratio calculation
- Confidence score based on confluence factors
- Signal strength rating (Weak, Moderate, Strong, Very Strong)

### Web Interface
- **Dashboard**: Quick analysis and feature overview
- **Symbol Analysis**: Detailed SMC analysis with interactive charts
- **Screener**: Scan all top Binance pairs for opportunities
- **Real-time Data**: Live data from Binance API
- **Interactive Charts**: Plotly-powered candlestick charts with SMC overlays

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install flask pandas numpy plotly requests ccxt ta-lib
```

## Usage

### Start the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Access Points

1. **Home Page**: `http://localhost:5000/`
   - Quick symbol analysis
   - Feature overview
   - Educational content

2. **Symbol Analysis**: `http://localhost:5000/analyze/BTCUSDT`
   - Replace BTCUSDT with any Binance symbol
   - Optional: `?timeframe=4h` for different timeframes

3. **Screener**: `http://localhost:5000/screener`
   - Scan multiple symbols automatically
   - Filter by confidence and timeframe
   - View top opportunities

### API Endpoints

- `GET /api/analyze/<symbol>` - Get analysis data for a symbol
- `GET /api/screener` - Run automated screening
- `GET /api/symbols` - List available symbols
- `GET /api/search?q=<query>` - Search for symbols

## Project Structure

```
/workspace
├── app.py                 # Flask web application
├── smc_analyzer.py        # SMC analysis engine
├── binance_fetcher.py     # Binance data fetcher
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── analysis.html     # Symbol analysis page
│   ├── screener.html     # Screener page
│   └── error.html        # Error page
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript utilities
└── README.md             # This file
```

## Trading Strategy

The app implements a confluence-based trading approach:

1. **Wait for Price to Enter Key Zones**
   - Discount zone for buys (below 38.2% Fib)
   - Premium zone for sells (above 61.8% Fib)

2. **Look for Confluence**
   - Order Block reaction
   - Fair Value Gap fill
   - Triangle pattern breakout
   - Liquidity sweep

3. **Confirm with Structure**
   - Break of Structure (BOS)
   - Change of Character (CHoCH)

4. **Risk Management**
   - Stop loss below/above Order Block
   - Minimum 1:2 risk/reward ratio
   - Multiple take profit levels

## Important Disclaimers

⚠️ **Trading involves substantial risk**
- This tool is for educational purposes only
- Not financial advice
- Past performance does not guarantee future results
- Never invest more than you can afford to lose
- Always do your own research

## Technical Details

### SMC Detection Algorithms

**Order Blocks**: 
- Identifies last opposing candle before strong moves
- Validates with volume and move strength
- Scores based on institutional footprint

**Fair Value Gaps**:
- Detects 3-candle imbalances
- Tracks fill percentage
- Filters by minimum gap size

**Triangle Patterns**:
- Uses linear regression for trendlines
- Calculates R-squared for confidence
- Projects target prices

### Data Sources
- Real-time data from Binance via CCXT library
- Rate-limited API calls to prevent bans
- Automatic retry on failures

## Contributing

This is an educational project. Feel free to:
- Report bugs
- Suggest improvements
- Add new SMC indicators
- Improve detection algorithms

## License

MIT License - Free for educational use

## Support

For questions or issues, please review the code documentation or submit feedback.

---

**Remember**: No trading system is 100% accurate. Always use proper risk management and never trade with money you cannot afford to lose.
