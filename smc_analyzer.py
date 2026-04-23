"""
Smart Money Concepts (SMC) Analyzer for Binance
Professional Trading Decision Support System

This module implements advanced Smart Money Concepts including:
- Order Blocks (OB)
- Fair Value Gaps (FVG)
- Break of Structure (BOS)
- Change of Character (CHoCH)
- Liquidity Pools
- Ascending/Descending Triangle Patterns
- Premium/Discount Zones
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SignalStrength(Enum):
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"


class TrendDirection(Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


@dataclass
class OrderBlock:
    """Represents an Order Block zone"""
    price_start: float
    price_end: float
    timestamp: int
    direction: str  # 'bullish' or 'bearish'
    strength: float  # 0-1 score
    tested_count: int = 0


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (FVG)"""
    high: float
    low: float
    midpoint: float
    timestamp: int
    direction: str  # 'bullish' or 'bearish'
    filled: bool = False
    fill_percentage: float = 0.0


@dataclass
class StructurePoint:
    """Represents a structural point (High/Low)"""
    price: float
    timestamp: int
    point_type: str  # 'high' or 'low'
    is_significant: bool


@dataclass
class TrianglePattern:
    """Represents a triangle pattern"""
    pattern_type: str  # 'ascending', 'descending', 'symmetrical'
    breakout_direction: Optional[str]
    support_line: List[Tuple[int, float]]
    resistance_line: List[Tuple[int, float]]
    apex_price: float
    confidence: float
    target_price: Optional[float]


@dataclass
class LiquidityPool:
    """Represents a liquidity pool area"""
    price_level: float
    liquidity_type: str  # 'above_highs' or 'below_lows'
    estimated_size: float
    swept: bool = False


@dataclass
class TradingSignal:
    """Complete trading signal with all SMC confluences"""
    symbol: str
    timestamp: int
    signal_type: str  # 'BUY' or 'SELL'
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward_ratio: float
    confidence_score: float
    strength: SignalStrength
    confluences: List[str]
    order_block: Optional[OrderBlock]
    fvg: Optional[FairValueGap]
    pattern: Optional[TrianglePattern]
    reasoning: str


class SmartMoneyConcepts:
    """
    Advanced Smart Money Concepts Analyzer
    Implements institutional trading concepts for identifying high-probability setups
    """

    def __init__(self, lookback_period: int = 100):
        self.lookback_period = lookback_period
        self.min_fvg_size = 0.001  # Minimum 0.1% for FVG
        self.min_ob_strength = 0.6

    def detect_pivot_points(self, df: pd.DataFrame, pivot_strength: int = 5) -> List[StructurePoint]:
        """
        Detect significant pivot points (highs and lows)
        Uses a rolling window to identify local extrema
        """
        pivots = []
        highs = df['high'].values
        lows = df['low'].values
        timestamps = df.index.values

        for i in range(pivot_strength, len(df) - pivot_strength):
            # Check for pivot high
            if highs[i] == max(highs[i-pivot_strength:i+pivot_strength+1]):
                pivots.append(StructurePoint(
                    price=highs[i],
                    timestamp=int(timestamps[i]),
                    point_type='high',
                    is_significant=True
                ))
            # Check for pivot low
            elif lows[i] == min(lows[i-pivot_strength:i+pivot_strength+1]):
                pivots.append(StructurePoint(
                    price=lows[i],
                    timestamp=int(timestamps[i]),
                    point_type='low',
                    is_significant=True
                ))

        return pivots

    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG) - Imbalance zones where price moved too quickly
        Bullish FVG: Low of candle 3 > High of candle 1
        Bearish FVG: High of candle 3 < Low of candle 1
        """
        fvgs = []
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        timestamps = df.index.values

        for i in range(2, len(df)):
            # Bullish FVG detection
            if lows[i] > highs[i-2]:
                gap_high = lows[i]
                gap_low = highs[i-2]
                gap_size = (gap_high - gap_low) / closes[i-1]

                if gap_size >= self.min_fvg_size:
                    current_price = closes[-1]
                    fill_pct = 0.0
                    if gap_low <= current_price <= gap_high:
                        fill_pct = 1.0 - ((gap_high - current_price) / (gap_high - gap_low))

                    fvgs.append(FairValueGap(
                        high=gap_high,
                        low=gap_low,
                        midpoint=(gap_high + gap_low) / 2,
                        timestamp=int(timestamps[i]),
                        direction='bullish',
                        filled=fill_pct >= 1.0,
                        fill_percentage=fill_pct
                    ))

            # Bearish FVG detection
            if highs[i] < lows[i-2]:
                gap_low = highs[i]
                gap_high = lows[i-2]
                gap_size = (gap_high - gap_low) / closes[i-1]

                if gap_size >= self.min_fvg_size:
                    current_price = closes[-1]
                    fill_pct = 0.0
                    if gap_low <= current_price <= gap_high:
                        fill_pct = (current_price - gap_low) / (gap_high - gap_low)

                    fvgs.append(FairValueGap(
                        high=gap_high,
                        low=gap_low,
                        midpoint=(gap_high + gap_low) / 2,
                        timestamp=int(timestamps[i]),
                        direction='bearish',
                        filled=fill_pct >= 1.0,
                        fill_percentage=fill_pct
                    ))

        return fvgs[-10:]  # Return last 10 FVGs

    def detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect Order Blocks - Institutional order accumulation zones
        Bullish OB: Last bearish candle before strong bullish move
        Bearish OB: Last bullish candle before strong bearish move
        """
        order_blocks = []
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        volumes = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
        timestamps = df.index.values

        # Calculate average candle size for strength measurement
        avg_candle_size = np.mean(np.abs(closes - opens))

        for i in range(2, len(df) - 5):
            # Bullish Order Block detection
            if closes[i] < opens[i]:  # Bearish candle
                # Check for strong bullish move after
                if i + 5 < len(df):
                    bullish_move = closes[i+5] - opens[i]
                    move_strength = bullish_move / avg_candle_size if avg_candle_size > 0 else 0

                    if move_strength > 3:  # Strong move (3x average)
                        # Verify volume confirmation
                        avg_volume = np.mean(volumes[i+1:i+5]) if len(volumes[i+1:i+5]) > 0 else 1
                        volume_ratio = volumes[i] / avg_volume if avg_volume > 0 else 1

                        strength = min(1.0, (move_strength / 5) * 0.6 + (min(volume_ratio, 3) / 3) * 0.4)

                        if strength >= self.min_ob_strength:
                            order_blocks.append(OrderBlock(
                                price_start=lows[i],
                                price_end=max(opens[i], closes[i]),
                                timestamp=int(timestamps[i]),
                                direction='bullish',
                                strength=strength
                            ))

            # Bearish Order Block detection
            elif closes[i] > opens[i]:  # Bullish candle
                if i + 5 < len(df):
                    bearish_move = opens[i] - closes[i+5]
                    move_strength = abs(bearish_move) / avg_candle_size if avg_candle_size > 0 else 0

                    if move_strength > 3:
                        avg_volume = np.mean(volumes[i+1:i+5]) if len(volumes[i+1:i+5]) > 0 else 1
                        volume_ratio = volumes[i] / avg_volume if avg_volume > 0 else 1

                        strength = min(1.0, (move_strength / 5) * 0.6 + (min(volume_ratio, 3) / 3) * 0.4)

                        if strength >= self.min_ob_strength:
                            order_blocks.append(OrderBlock(
                                price_start=min(opens[i], closes[i]),
                                price_end=highs[i],
                                timestamp=int(timestamps[i]),
                                direction='bearish',
                                strength=strength
                            ))

        # Return most recent and strongest order blocks
        return sorted(order_blocks, key=lambda x: (x.timestamp, x.strength), reverse=True)[:10]

    def detect_break_of_structure(self, df: pd.DataFrame, pivots: List[StructurePoint]) -> Tuple[Optional[str], Optional[float]]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHoCH)
        BOS: Price breaks previous significant high/low in trend direction
        CHoCH: First break against the prevailing trend (potential reversal)
        """
        if len(pivots) < 4:
            return None, None

        # Sort pivots by timestamp
        sorted_pivots = sorted(pivots, key=lambda x: x.timestamp)

        # Get recent highs and lows
        recent_highs = [p for p in sorted_pivots if p.point_type == 'high'][-5:]
        recent_lows = [p for p in sorted_pivots if p.point_type == 'low'][-5:]

        if not recent_highs or not recent_lows:
            return None, None

        current_price = df['close'].iloc[-1]
        prev_significant_high = max([p.price for p in recent_highs[:-1]]) if len(recent_highs) > 1 else recent_highs[0].price
        prev_significant_low = min([p.price for p in recent_lows[:-1]]) if len(recent_lows) > 1 else recent_lows[0].price

        # Check for bullish BOS
        if current_price > prev_significant_high:
            return 'BOS_BULLISH', prev_significant_high

        # Check for bearish BOS
        if current_price < prev_significant_low:
            return 'BOS_BEARISH', prev_significant_low

        # Check for CHoCH (Change of Character)
        # Simple logic: if we break a major low after making lower highs, or vice versa
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            if recent_highs[-1].price < recent_highs[-2].price and current_price < recent_lows[-1].price:
                return 'CHoCH_BEARISH', recent_lows[-1].price
            elif recent_lows[-1].price > recent_lows[-2].price and current_price > recent_highs[-1].price:
                return 'CHoCH_BULLISH', recent_highs[-1].price

        return None, None

    def detect_triangle_pattern(self, df: pd.DataFrame) -> Optional[TrianglePattern]:
        """
        Detect Triangle Patterns (Ascending, Descending, Symmetrical)
        Uses linear regression to identify converging trendlines
        """
        if len(df) < 20:
            return None

        highs = df['high'].values
        lows = df['low'].values
        timestamps = np.arange(len(df))

        # Find local highs and lows in recent period
        window = 5
        local_highs = []
        local_lows = []

        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                local_highs.append((timestamps[i], highs[i]))
            if lows[i] == min(lows[i-window:i+window+1]):
                local_lows.append((timestamps[i], lows[i]))

        if len(local_highs) < 2 or len(local_lows) < 2:
            return None

        # Take last 3-5 points for each
        recent_highs = local_highs[-5:] if len(local_highs) >= 5 else local_highs[-3:]
        recent_lows = local_lows[-5:] if len(local_lows) >= 5 else local_lows[-3:]

        if len(recent_highs) < 2 or len(recent_lows) < 2:
            return None

        # Fit trendlines using linear regression
        try:
            # Resistance line (upper trendline)
            high_times = np.array([h[0] for h in recent_highs])
            high_prices = np.array([h[1] for h in recent_highs])
            high_slope, high_intercept = np.polyfit(high_times, high_prices, 1)

            # Support line (lower trendline)
            low_times = np.array([l[0] for l in recent_lows])
            low_prices = np.array([l[1] for l in recent_lows])
            low_slope, low_intercept = np.polyfit(low_times, low_prices, 1)

            # Determine pattern type
            high_slope_threshold = 0.0001
            low_slope_threshold = 0.0001

            if high_slope < -high_slope_threshold and low_slope > low_slope_threshold:
                pattern_type = 'symmetrical'
            elif abs(high_slope) < high_slope_threshold and low_slope > low_slope_threshold:
                pattern_type = 'ascending'
            elif high_slope < -high_slope_threshold and abs(low_slope) < low_slope_threshold:
                pattern_type = 'descending'
            else:
                # Check for convergence
                if high_slope < 0 and low_slope > 0:
                    pattern_type = 'symmetrical'
                elif low_slope > 0 and high_slope >= 0:
                    pattern_type = 'ascending'
                elif high_slope < 0 and low_slope <= 0:
                    pattern_type = 'descending'
                else:
                    return None

            # Calculate apex (where lines converge)
            if abs(high_slope - low_slope) > 0.0001:
                apex_time = (low_intercept - high_intercept) / (high_slope - low_slope)
                apex_price = high_slope * apex_time + high_intercept
            else:
                apex_price = np.mean([high_prices[-1], low_prices[-1]])

            # Calculate confidence based on how well points fit the lines
            high_pred = high_slope * high_times + high_intercept
            low_pred = low_slope * low_times + low_intercept

            high_r_squared = 1 - np.sum((high_prices - high_pred)**2) / (np.var(high_prices) * len(high_prices)) if np.var(high_prices) > 0 else 0
            low_r_squared = 1 - np.sum((low_prices - low_pred)**2) / (np.var(low_prices) * len(low_prices)) if np.var(low_prices) > 0 else 0

            confidence = (max(0, high_r_squared) + max(0, low_r_squared)) / 2

            # Only return if confidence is reasonable
            if confidence < 0.5:
                return None

            # Calculate target price (height of pattern added to breakout point)
            pattern_height = high_prices[-1] - low_prices[-1]
            current_price = df['close'].iloc[-1]

            # Determine likely breakout direction
            if pattern_type == 'ascending':
                breakout_direction = 'bullish'
                target_price = current_price + pattern_height
            elif pattern_type == 'descending':
                breakout_direction = 'bearish'
                target_price = current_price - pattern_height
            else:
                # For symmetrical, use recent trend
                recent_trend = df['close'].iloc[-1] - df['close'].iloc[-10]
                breakout_direction = 'bullish' if recent_trend > 0 else 'bearish'
                target_price = current_price + (pattern_height if breakout_direction == 'bullish' else -pattern_height)

            return TrianglePattern(
                pattern_type=pattern_type,
                breakout_direction=breakout_direction,
                support_line=[(int(t), float(p)) for t, p in zip(low_times, low_pred)],
                resistance_line=[(int(t), float(p)) for t, p in zip(high_times, high_pred)],
                apex_price=float(apex_price),
                confidence=confidence,
                target_price=target_price
            )

        except Exception:
            return None

    def detect_liquidity_pools(self, df: pd.DataFrame, pivots: List[StructurePoint]) -> List[LiquidityPool]:
        """
        Detect Liquidity Pools - Areas where stop losses are likely clustered
        Above equal highs and below equal lows
        """
        liquidity_pools = []

        if len(pivots) < 3:
            return liquidity_pools

        sorted_pivots = sorted(pivots, key=lambda x: x.timestamp)

        # Group highs and lows
        highs = [p for p in sorted_pivots if p.point_type == 'high']
        lows = [p for p in sorted_pivots if p.point_type == 'low']

        # Find equal highs (within 0.5%)
        for i, h1 in enumerate(highs):
            for h2 in highs[i+1:]:
                if abs(h1.price - h2.price) / h1.price < 0.005:
                    liquidity_pools.append(LiquidityPool(
                        price_level=max(h1.price, h2.price) * 1.001,
                        liquidity_type='above_highs',
                        estimated_size=abs(h1.price - h2.price) * 1000  # Estimate
                    ))
                    break

        # Find equal lows (within 0.5%)
        for i, l1 in enumerate(lows):
            for l2 in lows[i+1:]:
                if abs(l1.price - l2.price) / l1.price < 0.005:
                    liquidity_pools.append(LiquidityPool(
                        price_level=min(l1.price, l2.price) * 0.999,
                        liquidity_type='below_lows',
                        estimated_size=abs(l1.price - l2.price) * 1000
                    ))
                    break

        # Add recent swing highs/lows as liquidity pools
        if highs:
            liquidity_pools.append(LiquidityPool(
                price_level=highs[-1].price * 1.002,
                liquidity_type='above_highs',
                estimated_size=df['volume'].iloc[-1] if 'volume' in df.columns else 1000
            ))

        if lows:
            liquidity_pools.append(LiquidityPool(
                price_level=lows[-1].price * 0.998,
                liquidity_type='below_lows',
                estimated_size=df['volume'].iloc[-1] if 'volume' in df.columns else 1000
            ))

        return liquidity_pools[-5:]

    def calculate_premium_discount_zones(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate Premium and Discount zones using Fibonacci levels
        Returns: (equilibrium, premium_threshold, discount_threshold)
        """
        if len(df) < 50:
            return df['close'].iloc[-1], df['close'].iloc[-1], df['close'].iloc[-1]

        # Use recent swing high and low
        recent_high = df['high'].iloc[-50:].max()
        recent_low = df['low'].iloc[-50:].min()

        range_size = recent_high - recent_low
        equilibrium = recent_low + range_size * 0.5
        premium_threshold = recent_low + range_size * 0.618  # 61.8% Fib
        discount_threshold = recent_low + range_size * 0.382  # 38.2% Fib

        return equilibrium, premium_threshold, discount_threshold

    def generate_trading_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = '1h'
    ) -> Optional[TradingSignal]:
        """
        Generate comprehensive trading signal based on all SMC confluences
        """
        # Run all detections
        pivots = self.detect_pivot_points(df)
        fvgs = self.detect_fair_value_gaps(df)
        order_blocks = self.detect_order_blocks(df)
        bos, bos_level = self.detect_break_of_structure(df, pivots)
        triangle = self.detect_triangle_pattern(df)
        liquidity_pools = self.detect_liquidity_pools(df, pivots)
        equilibrium, premium, discount = self.calculate_premium_discount_zones(df)

        current_price = df['close'].iloc[-1]
        timestamp = int(df.index[-1].timestamp())  # Convert Timestamp to Unix timestamp

        confluences = []
        bullish_signals = 0
        bearish_signals = 0
        reasoning_parts = []

        # Check for bullish order block near current price
        bullish_ob = None
        for ob in order_blocks:
            if ob.direction == 'bullish':
                if discount <= ob.price_end <= current_price * 1.02:
                    bullish_ob = ob
                    bullish_signals += 2
                    confluences.append(f"Bullish Order Block at {ob.price_start:.4f}")
                    reasoning_parts.append(f"Price is reacting from bullish order block zone")

        # Check for bearish order block
        bearish_ob = None
        for ob in order_blocks:
            if ob.direction == 'bearish':
                if current_price * 0.98 <= ob.price_start <= premium:
                    bearish_ob = ob
                    bearish_signals += 2
                    confluences.append(f"Bearish Order Block at {ob.price_end:.4f}")
                    reasoning_parts.append(f"Price is approaching bearish order block zone")

        # Check for unfilled bullish FVG
        bullish_fvg = None
        for fvg in fvgs:
            if fvg.direction == 'bullish' and not fvg.filled and fvg.fill_percentage < 0.5:
                if discount <= fvg.low <= current_price * 1.01:
                    bullish_fvg = fvg
                    bullish_signals += 1
                    confluences.append(f"Unfilled Bullish FVG at {fvg.midpoint:.4f}")
                    reasoning_parts.append(f"Price near unfilled bullish fair value gap")

        # Check for unfilled bearish FVG
        bearish_fvg = None
        for fvg in fvgs:
            if fvg.direction == 'bearish' and not fvg.filled and fvg.fill_percentage < 0.5:
                if current_price * 0.99 <= fvg.high <= premium:
                    bearish_fvg = fvg
                    bearish_signals += 1
                    confluences.append(f"Unfilled Bearish FVG at {fvg.midpoint:.4f}")
                    reasoning_parts.append(f"Price near unfilled bearish fair value gap")

        # Check structure break
        if bos:
            if 'BULLISH' in bos:
                bullish_signals += 2
                confluences.append(f"Bullish Structure Break above {bos_level:.4f}")
                reasoning_parts.append("Market structure shows bullish break")
            elif 'BEARISH' in bos:
                bearish_signals += 2
                confluences.append(f"Bearish Structure Break below {bos_level:.4f}")
                reasoning_parts.append("Market structure shows bearish break")

        # Check triangle pattern
        if triangle:
            if triangle.pattern_type == 'ascending':
                bullish_signals += 2
                confluences.append(f"Ascending Triangle Pattern (Confidence: {triangle.confidence:.2f})")
                reasoning_parts.append(f"Ascending triangle detected with target {triangle.target_price:.4f}")
            elif triangle.pattern_type == 'descending':
                bearish_signals += 2
                confluences.append(f"Descending Triangle Pattern (Confidence: {triangle.confidence:.2f})")
                reasoning_parts.append(f"Descending triangle detected with target {triangle.target_price:.4f}")

        # Check premium/discount zone
        if current_price < discount:
            bullish_signals += 1
            confluences.append("Price in Discount Zone")
            reasoning_parts.append("Asset trading in discount zone (potential buy area)")
        elif current_price > premium:
            bearish_signals += 1
            confluences.append("Price in Premium Zone")
            reasoning_parts.append("Asset trading in premium zone (potential sell area)")

        # Check liquidity sweeps
        for lp in liquidity_pools:
            if lp.liquidity_type == 'below_lows' and current_price <= lp.price_level * 1.005:
                bullish_signals += 1
                confluences.append(f"Liquidity Sweep at {lp.price_level:.4f}")
                reasoning_parts.append("Potential liquidity sweep below recent lows")
            elif lp.liquidity_type == 'above_highs' and current_price >= lp.price_level * 0.995:
                bearish_signals += 1
                confluences.append(f"Liquidity Sweep at {lp.price_level:.4f}")
                reasoning_parts.append("Potential liquidity sweep above recent highs")

        # Determine signal
        total_signals = bullish_signals + bearish_signals
        if total_signals < 3:
            return None  # Not enough confluence

        if bullish_signals > bearish_signals + 1:
            signal_type = 'BUY'

            # Calculate entry, SL, TP
            if bullish_ob:
                entry_price = (bullish_ob.price_start + bullish_ob.price_end) / 2
                stop_loss = bullish_ob.price_start * 0.995
            elif bullish_fvg:
                entry_price = bullish_fvg.midpoint
                stop_loss = bullish_fvg.low * 0.995
            else:
                entry_price = current_price
                stop_loss = df['low'].iloc[-20:].min() * 0.995

            # Calculate take profits based on recent range
            recent_range = df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min()
            take_profit_1 = entry_price + recent_range * 0.5
            take_profit_2 = entry_price + recent_range * 1.0
            take_profit_3 = entry_price + recent_range * 1.5 if triangle and triangle.target_price else entry_price + recent_range * 1.5

            if triangle and triangle.target_price:
                take_profit_3 = max(take_profit_3, triangle.target_price)

        elif bearish_signals > bullish_signals + 1:
            signal_type = 'SELL'

            if bearish_ob:
                entry_price = (bearish_ob.price_start + bearish_ob.price_end) / 2
                stop_loss = bearish_ob.price_end * 1.005
            elif bearish_fvg:
                entry_price = bearish_fvg.midpoint
                stop_loss = bearish_fvg.high * 1.005
            else:
                entry_price = current_price
                stop_loss = df['high'].iloc[-20:].max() * 1.005

            recent_range = df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min()
            take_profit_1 = entry_price - recent_range * 0.5
            take_profit_2 = entry_price - recent_range * 1.0
            take_profit_3 = entry_price - recent_range * 1.5 if triangle and triangle.target_price else entry_price - recent_range * 1.5

            if triangle and triangle.target_price:
                take_profit_3 = min(take_profit_3, triangle.target_price)
        else:
            return None  # Conflicting signals

        # Calculate risk-reward ratio
        if signal_type == 'BUY':
            risk = entry_price - stop_loss
            reward = take_profit_1 - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit_1

        risk_reward_ratio = reward / risk if risk > 0 else 0

        # Calculate confidence score
        confidence_score = min(1.0, (bullish_signals if signal_type == 'BUY' else bearish_signals) / 8)
        confidence_score = max(0.3, confidence_score)

        # Determine signal strength
        if confidence_score >= 0.8:
            strength = SignalStrength.VERY_STRONG
        elif confidence_score >= 0.6:
            strength = SignalStrength.STRONG
        elif confidence_score >= 0.4:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK

        reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Multiple SMC confluences detected"

        return TradingSignal(
            symbol=symbol,
            timestamp=timestamp,
            signal_type=signal_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            risk_reward_ratio=risk_reward_ratio,
            confidence_score=confidence_score,
            strength=strength,
            confluences=confluences,
            order_block=bullish_ob if signal_type == 'BUY' else bearish_ob,
            fvg=bullish_fvg if signal_type == 'BUY' else bearish_fvg,
            pattern=triangle,
            reasoning=reasoning
        )
