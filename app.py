"""
Professional Flask Web Application for Smart Money Concepts Analysis
Advanced trading decision support system for Binance cryptocurrencies
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime
import threading
from typing import Dict, List, Optional

from smc_analyzer import SmartMoneyConcepts, TradingSignal, SignalStrength
from binance_fetcher import BinanceDataFetcher


app = Flask(__name__)
app.config['SECRET_KEY'] = 'smc-trading-analyzer-2024'

# Initialize components
data_fetcher = BinanceDataFetcher()
smc_analyzer = SmartMoneyConcepts(lookback_period=100)

# Cache for analysis results
analysis_cache = {}
cache_lock = threading.Lock()


def analyze_symbol(symbol: str, timeframe: str = '1h') -> Dict:
    """
    Perform comprehensive SMC analysis on a symbol
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe
        
    Returns:
        Dictionary containing analysis results
    """
    # Fetch data
    df = data_fetcher.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
    
    if df.empty:
        return {'error': f'No data available for {symbol}'}
    
    # Run SMC analysis
    signal = smc_analyzer.generate_trading_signal(symbol, df, timeframe)
    
    # Get additional analysis components
    pivots = smc_analyzer.detect_pivot_points(df)
    fvgs = smc_analyzer.detect_fair_value_gaps(df)
    order_blocks = smc_analyzer.detect_order_blocks(df)
    triangle = smc_analyzer.detect_triangle_pattern(df)
    liquidity_pools = smc_analyzer.detect_liquidity_pools(df, pivots)
    equilibrium, premium, discount = smc_analyzer.calculate_premium_discount_zones(df)
    
    # Create price chart with SMC elements
    fig = create_smc_chart(df, signal, fvgs, order_blocks, triangle, premium, discount)
    
    # Prepare result
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': datetime.now().isoformat(),
        'current_price': float(df['close'].iloc[-1]),
        'price_change_24h': float((df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20] * 100) if len(df) > 20 else 0,
        'signal': signal_to_dict(signal) if signal else None,
        'order_blocks': [ob.__dict__ for ob in order_blocks[:5]],
        'fvgs': [fvg.__dict__ for fvg in fvgs[:5]],
        'triangle': triangle.__dict__ if triangle else None,
        'liquidity_pools': [lp.__dict__ for lp in liquidity_pools],
        'premium_discount': {
            'equilibrium': equilibrium,
            'premium': premium,
            'discount': discount
        },
        'chart_json': json.dumps(fig, cls=PlotlyJSONEncoder),
        'market_data': {
            'high_24h': float(df['high'].iloc[-20:].max()) if len(df) > 20 else float(df['high'].iloc[-1]),
            'low_24h': float(df['low'].iloc[-20:].min()) if len(df) > 20 else float(df['low'].iloc[-1]),
            'volume': float(df['volume'].iloc[-1])
        }
    }
    
    return result


def signal_to_dict(signal: TradingSignal) -> Dict:
    """Convert TradingSignal to dictionary for JSON serialization"""
    if not signal:
        return None
    
    return {
        'symbol': signal.symbol,
        'signal_type': signal.signal_type,
        'entry_price': signal.entry_price,
        'stop_loss': signal.stop_loss,
        'take_profit_1': signal.take_profit_1,
        'take_profit_2': signal.take_profit_2,
        'take_profit_3': signal.take_profit_3,
        'risk_reward_ratio': signal.risk_reward_ratio,
        'confidence_score': signal.confidence_score,
        'strength': signal.strength.value,
        'confluences': signal.confluences,
        'reasoning': signal.reasoning,
        'timestamp': signal.timestamp
    }


def create_smc_chart(
    df: pd.DataFrame,
    signal: Optional[TradingSignal],
    fvgs: List,
    order_blocks: List,
    triangle: Optional,
    premium: float,
    discount: float
) -> go.Figure:
    """
    Create interactive Plotly chart with SMC elements
    
    Args:
        df: OHLCV DataFrame
        signal: Trading signal (optional)
        fvgs: List of Fair Value Gaps
        order_blocks: List of Order Blocks
        triangle: Triangle pattern (optional)
        premium: Premium zone threshold
        discount: Discount zone threshold
        
    Returns:
        Plotly Figure object
    """
    # Create candlestick chart
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
        increasing_line_color='#089981',
        decreasing_line_color='#F23645'
    ))
    
    # Add Premium/Discount zones
    fig.add_hrect(
        y0=discount, y1=premium,
        fillcolor="rgba(255, 165, 0, 0.1)",
        line_width=0,
        annotation_text="Equilibrium Zone",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=df['low'].min(), y1=discount,
        fillcolor="rgba(0, 255, 0, 0.05)",
        line_width=0,
        annotation_text="Discount Zone (Buy Area)",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=premium, y1=df['high'].max(),
        fillcolor="rgba(255, 0, 0, 0.05)",
        line_width=0,
        annotation_text="Premium Zone (Sell Area)",
        annotation_position="right"
    )
    
    # Add Order Blocks
    for i, ob in enumerate(order_blocks[:3]):
        color = 'rgba(0, 255, 0, 0.2)' if ob.direction == 'bullish' else 'rgba(255, 0, 0, 0.2)'
        fig.add_hrect(
            y0=ob.price_start, y1=ob.price_end,
            fillcolor=color,
            line_width=1,
            line_dash="dash",
            annotation_text=f"OB {ob.direction}",
            annotation_position="right"
        )
    
    # Add Fair Value Gaps
    for i, fvg in enumerate(fvgs[:3]):
        if not fvg.filled and fvg.fill_percentage < 0.7:
            color = 'rgba(0, 255, 0, 0.15)' if fvg.direction == 'bullish' else 'rgba(255, 0, 0, 0.15)'
            fig.add_hrect(
                y0=fvg.low, y1=fvg.high,
                fillcolor=color,
                line_width=1,
                line_dash="dot",
                annotation_text=f"FVG {fvg.direction}",
                annotation_position="right"
            )
    
    # Add Triangle pattern lines
    if triangle:
        # Support line
        if triangle.support_line:
            sup_x = [df.index[int(pt[0])] for pt in triangle.support_line if int(pt[0]) < len(df)]
            sup_y = [pt[1] for pt in triangle.support_line if int(pt[0]) < len(df)]
            if len(sup_x) > 1:
                fig.add_trace(go.Scatter(
                    x=sup_x, y=sup_y,
                    mode='lines',
                    line=dict(color='green', width=2, dash='dash'),
                    name='Triangle Support',
                    showlegend=True
                ))
        
        # Resistance line
        if triangle.resistance_line:
            res_x = [df.index[int(pt[0])] for pt in triangle.resistance_line if int(pt[0]) < len(df)]
            res_y = [pt[1] for pt in triangle.resistance_line if int(pt[0]) < len(df)]
            if len(res_x) > 1:
                fig.add_trace(go.Scatter(
                    x=res_x, y=res_y,
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name='Triangle Resistance',
                    showlegend=True
                ))
    
    # Add signal markers
    if signal:
        if signal.signal_type == 'BUY':
            fig.add_trace(go.Scatter(
                x=[df.index[-1]],
                y=[signal.entry_price],
                mode='markers+text',
                marker=dict(symbol='triangle-up', size=20, color='green'),
                text=['BUY'],
                textposition='top center',
                name='Buy Signal',
                showlegend=True
            ))
        elif signal.signal_type == 'SELL':
            fig.add_trace(go.Scatter(
                x=[df.index[-1]],
                y=[signal.entry_price],
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=20, color='red'),
                text=['SELL'],
                textposition='bottom center',
                name='Sell Signal',
                showlegend=True
            ))
    
    # Update layout
    fig.update_layout(
        title=f'{signal.symbol if signal else ""} - SMC Analysis ({request.args.get("timeframe", "1h")})',
        yaxis_title='Price',
        xaxis_title='Time',
        height=700,
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    fig.update_yaxis(gridcolor='#2a2a2a')
    fig.update_xaxis(gridcolor='#2a2a2a')
    
    return fig


@app.route('/')
def index():
    """Home page - Dashboard with top opportunities"""
    return render_template('index.html')


@app.route('/analyze/<symbol>')
def analyze(symbol: str):
    """Analyze a specific symbol"""
    timeframe = request.args.get('timeframe', '1h')
    
    # Check cache
    cache_key = f"{symbol}_{timeframe}"
    with cache_lock:
        if cache_key in analysis_cache:
            cached_time, cached_result = analysis_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < 300:  # 5 min cache
                return render_template('analysis.html', result=cached_result)
    
    # Perform analysis
    result = analyze_symbol(symbol, timeframe)
    
    # Cache result
    with cache_lock:
        analysis_cache[cache_key] = (datetime.now(), result)
    
    return render_template('analysis.html', result=result)


@app.route('/api/analyze/<symbol>')
def api_analyze(symbol: str):
    """API endpoint for symbol analysis"""
    timeframe = request.args.get('timeframe', '1h')
    result = analyze_symbol(symbol, timeframe)
    return jsonify(result)


@app.route('/api/screener')
def api_screener():
    """
    API endpoint for screening all symbols
    Returns symbols with strong buy signals
    """
    timeframe = request.args.get('timeframe', '1h')
    limit = int(request.args.get('limit', 50))
    min_confidence = float(request.args.get('min_confidence', 0.5))
    
    # Get top symbols by volume
    symbols = data_fetcher.get_top_symbols_by_volume(quote_currency='USDT', top_n=limit)
    
    opportunities = []
    
    for symbol in symbols:
        try:
            result = analyze_symbol(symbol, timeframe)
            
            if 'error' not in result and result.get('signal'):
                signal = result['signal']
                
                # Filter by signal type and confidence
                if (signal['signal_type'] == 'BUY' and 
                    signal['confidence_score'] >= min_confidence):
                    
                    opportunities.append({
                        'symbol': symbol,
                        'price': result['current_price'],
                        'signal_strength': signal['strength'],
                        'confidence': signal['confidence_score'],
                        'risk_reward': signal['risk_reward_ratio'],
                        'confluences_count': len(signal['confluences']),
                        'entry': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit_1': signal['take_profit_1'],
                        'reasoning': signal['reasoning']
                    })
        except Exception as e:
            continue
    
    # Sort by confidence and risk-reward
    opportunities.sort(key=lambda x: (x['confidence'], x['risk_reward']), reverse=True)
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'timeframe': timeframe,
        'symbols_analyzed': len(symbols),
        'opportunities_found': len(opportunities),
        'opportunities': opportunities[:20]  # Return top 20
    })


@app.route('/screener')
def screener():
    """Screener page - Find best trading opportunities"""
    return render_template('screener.html')


@app.route('/api/symbols')
def api_symbols():
    """Get list of available symbols"""
    quote = request.args.get('quote', 'USDT')
    limit = int(request.args.get('limit', 100))
    
    symbols = data_fetcher.get_top_symbols_by_volume(quote_currency=quote, top_n=limit)
    
    return jsonify({'symbols': symbols})


@app.route('/search')
def search():
    """Search for symbols"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'symbols': []})
    
    matches = data_fetcher.search_symbols(query)
    
    return jsonify({'symbols': matches})


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Server error occurred"), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
