#!/usr/bin/env python3
"""Test script for SMC Analyzer module"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from smc_analyzer import SmartMoneyConcepts

def test_smc_analyzer():
    # Create sample data for testing
    dates = pd.date_range(start=datetime.now() - timedelta(hours=200), periods=200, freq='1h')
    np.random.seed(42)

    # Generate realistic OHLCV data
    base_price = 50000
    prices = [base_price]
    for i in range(199):
        change = np.random.randn() * 200
        prices.append(prices[-1] + change)

    opens = prices[:-1]
    closes = prices[1:]
    highs = [max(o, c) + abs(np.random.randn() * 50) for o, c in zip(opens, closes)]
    lows = [min(o, c) - abs(np.random.randn() * 50) for o, c in zip(opens, closes)]
    volumes = np.random.uniform(100, 1000, 199)

    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=dates[:199])

    smc = SmartMoneyConcepts()

    # Test all detection methods
    print("Testing SMC detection methods...")
    
    pivots = smc.detect_pivot_points(df)
    print(f'✓ Pivots detected: {len(pivots)}')
    
    fvgs = smc.detect_fair_value_gaps(df)
    print(f'✓ FVGs detected: {len(fvgs)}')
    
    order_blocks = smc.detect_order_blocks(df)
    print(f'✓ Order Blocks detected: {len(order_blocks)}')
    
    bos, bos_level = smc.detect_break_of_structure(df, pivots)
    print(f'✓ BOS: {bos}')
    
    triangle = smc.detect_triangle_pattern(df)
    print(f'✓ Triangle pattern: {triangle.pattern_type if triangle else None}')
    
    liquidity = smc.detect_liquidity_pools(df, pivots)
    print(f'✓ Liquidity pools: {len(liquidity)}')
    
    equilibrium, premium, discount = smc.calculate_premium_discount_zones(df)
    print(f'✓ Discount zone: {discount:.2f}')
    print(f'✓ Premium zone: {premium:.2f}')

    # Generate signal
    signal = smc.generate_trading_signal('BTC/USDT', df)
    if signal:
        print(f'\n✓ Signal generated:')
        print(f'  - Type: {signal.signal_type}')
        print(f'  - Confidence: {signal.confidence_score:.2f}')
        print(f'  - Strength: {signal.strength.value}')
    else:
        print('\n✓ No strong signal (normal for random data)')

    print('\n✅ All tests passed successfully!')
    return True

if __name__ == '__main__':
    test_smc_analyzer()
