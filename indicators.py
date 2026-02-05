import pandas as pd
import numpy as np

# ============================================
# CONFIGURATION
# ============================================
SRCHANNEL_CONFIG = {
    'pivot_period': 10,
    'channel_width_pct': 5,
    'min_strength': 1,
    'max_channels': 6,
    'loopback': 100,
}

LUXALGO_CONFIG = {
    'length': 8,
    'mult': 50,
    'atr_length': 4,
}

def detect_pivot_points(df, period=10):
    """
    Detect Pivot High and Pivot Low points
    """
    pivots = []
    
    for i in range(period, len(df) - period):
        # Check Pivot High
        is_pivot_high = True
        high_val = df['high'].iloc[i]
        for j in range(i - period, i + period + 1):
            if j != i and df['high'].iloc[j] >= high_val:
                is_pivot_high = False
                break
        
        if is_pivot_high:
            pivots.append({
                'type': 'high',
                'price': high_val,
                'index': i,
                'bar_index': df.index[i]
            })
        
        # Check Pivot Low
        is_pivot_low = True
        low_val = df['low'].iloc[i]
        for j in range(i - period, i + period + 1):
            if j != i and df['low'].iloc[j] <= low_val:
                is_pivot_low = False
                break
        
        if is_pivot_low:
            pivots.append({
                'type': 'low',
                'price': low_val,
                'index': i,
                'bar_index': df.index[i]
            })
    
    return pivots

def calculate_sr_channels(df, config=None):
    """
    Calculate Support/Resistance Channels
    """
    if config is None:
        config = SRCHANNEL_CONFIG
    
    period = config['pivot_period']
    channel_width_pct = config['channel_width_pct']
    min_strength = config['min_strength']
    max_channels = config['max_channels']
    loopback = min(config['loopback'], len(df) - period * 2 - 1)
    
    if loopback < 20:
        return None
    
    highest_300 = df['high'].iloc[-min(300, len(df)):].max()
    lowest_300 = df['low'].iloc[-min(300, len(df)):].min()
    channel_width = (highest_300 - lowest_300) * channel_width_pct / 100
    
    pivots = detect_pivot_points(df, period)
    current_bar = len(df) - 1
    recent_pivots = [p for p in pivots if current_bar - p['index'] <= loopback]
    
    if len(recent_pivots) == 0:
        return None
    
    def get_channel_for_pivot(pivot_idx, all_pivots):
        base_price = all_pivots[pivot_idx]['price']
        lo = base_price
        hi = base_price
        included = []
        
        for i, p in enumerate(all_pivots):
            price = p['price']
            width = price - lo if price > hi else hi - price if price < lo else 0
            
            if width <= channel_width:
                if price < lo:
                    lo = price
                elif price > hi:
                    hi = price
                included.append(i)
        
        return {'hi': hi, 'lo': lo, 'pivot_count': len(included), 'pivots': included}
    
    channel_candidates = []
    for i in range(len(recent_pivots)):
        ch = get_channel_for_pivot(i, recent_pivots)
        strength = ch['pivot_count'] * 20
        
        touches = 0
        for j in range(max(0, len(df) - loopback), len(df)):
            h = df['high'].iloc[j]
            l = df['low'].iloc[j]
            if (h <= ch['hi'] and h >= ch['lo']) or (l <= ch['hi'] and l >= ch['lo']):
                touches += 1
        
        strength += touches
        ch['strength'] = strength
        channel_candidates.append(ch)
    
    # Sort and filter
    used_pivots = set()
    final_channels = []
    channel_candidates.sort(key=lambda x: x['strength'], reverse=True)
    
    for ch in channel_candidates:
        if ch['strength'] < min_strength * 20:
            continue
        
        overlap = False
        for p_idx in ch['pivots']:
            if p_idx in used_pivots:
                overlap = True
                break
        
        if not overlap:
            for p_idx in ch['pivots']:
                used_pivots.add(p_idx)
            final_channels.append(ch)
            if len(final_channels) >= max_channels:
                break
    
    current_price = df['close'].iloc[-1]
    for ch in final_channels:
        if ch['hi'] < current_price and ch['lo'] < current_price:
            ch['type'] = 'support'
            ch['color'] = '#26a69a'
        elif ch['hi'] > current_price and ch['lo'] > current_price:
            ch['type'] = 'resistance'
            ch['color'] = '#ef5350'
        else:
            ch['type'] = 'active'
            ch['color'] = '#808080'
            
    # Check broken
    prev_close = df['close'].iloc[-2] if len(df) > 1 else current_price
    broken_resistance = False
    broken_support = False
    
    for ch in final_channels:
        if prev_close <= ch['hi'] and current_price > ch['hi']:
            broken_resistance = True
        if prev_close >= ch['lo'] and current_price < ch['lo']:
            broken_support = True
            
    return {
        'channels': final_channels,
        'broken_resistance': broken_resistance,
        'broken_support': broken_support,
    }

def calculate_luxalgo_sr_dynamic(df, config=None):
    """
    LuxAlgo-style Support & Resistance Dynamic
    """
    if config is None:
        config = LUXALGO_CONFIG
    
    length = config['length']
    mult = config['mult'] / 100
    atr_length = config['atr_length']
    
    if len(df) < max(length * 2, atr_length) + 10:
        return None
    
    # Simple ATR
    df_calc = df.copy()
    df_calc['tr'] = np.maximum(
        df_calc['high'] - df_calc['low'],
        np.maximum(
            abs(df_calc['high'] - df_calc['close'].shift(1)),
            abs(df_calc['low'] - df_calc['close'].shift(1))
        )
    )
    df_calc['atr'] = df_calc['tr'].rolling(window=atr_length).mean()
    
    current_atr = df_calc['atr'].iloc[-1]
    zone_width = current_atr * mult
    
    zones = []
    
    for i in range(length, len(df) - length):
        # Resistance
        is_pivot_high = True
        high_val = df['high'].iloc[i]
        for j in range(i - length, i + length + 1):
            if j != i and df['high'].iloc[j] >= high_val:
                is_pivot_high = False
                break
        
        if is_pivot_high:
            zones.append({
                'type': 'resistance',
                'top': high_val,
                'bottom': high_val - zone_width,
                'mid': high_val - zone_width/2,
                'color': '#ef5350'
            })
            
        # Support
        is_pivot_low = True
        low_val = df['low'].iloc[i]
        for j in range(i - length, i + length + 1):
            if j != i and df['low'].iloc[j] <= low_val:
                is_pivot_low = False
                break
        
        if is_pivot_low:
            zones.append({
                'type': 'support',
                'top': low_val + zone_width,
                'bottom': low_val,
                'mid': low_val + zone_width/2,
                'color': '#26a69a'
            })
            
    # Return last valid zones
    return zones

def calculate_indicators(df):
    """Calculate all indicators including multi-TF analysis indicators"""
    # EMAs
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Moving Averages
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    
    # Bollinger Bands
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    df['BB_Std'] = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])
    
    # Volume
    df['Vol_MA20'] = df['volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['volume'] / df['Vol_MA20']
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = high_low.combine(high_close, max).combine(low_close, max)
    df['ATR'] = tr.rolling(window=14).mean()
    
    return df
