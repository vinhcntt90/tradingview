import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from .config import Config
from .indicators import calculate_sr_channels

def plot_plotly_chart(df, timeframes_bias, pivots, poc_data, plan):
    """
    Generate Professional Crypto Chart using Plotly
    """
    print("[*] Generating Plotly Chart...")
    
    # Create Figure
    fig = make_subplots(rows=1, cols=1)
    
    # 1. Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='BTC/USDT',
        increasing_line_color='#26a69a', # Teal
        decreasing_line_color='#ef5350'  # Red
    ))
    
    # 2. EMAs
    colors = {'EMA9': '#2962ff', 'EMA21': '#ff6d00', 'EMA50': '#ffab00', 'EMA200': '#e91e63'}
    for ema, color in colors.items():
        if ema in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ema], 
                mode='lines', name=ema,
                line=dict(color=color, width=1)
            ))
            
    # 3. Bollinger Bands
    if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Upper'],
            mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Lower'],
            mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(0, 188, 212, 0.05)',
            showlegend=False, hoverinfo='skip'
        ))

    # 4. Support/Resistance Channels
    sr_data = calculate_sr_channels(df)
    if sr_data and sr_data.get('channels'):
        for ch in sr_data['channels']:
            color = 'rgba(38, 166, 154, 0.2)' if ch['type'] == 'support' else 'rgba(239, 83, 80, 0.2)'
            fig.add_shape(type="rect",
                x0=df.index[0], y0=ch['lo'], x1=df.index[-1], y1=ch['hi'],
                fillcolor=color, line_width=0, layer="below"
            )
            fig.add_annotation(
                x=df.index[-10], y=ch['hi'],
                text=f"{ch['type'].upper()}",
                showarrow=False, font=dict(color=color.replace('0.2', '1.0'), size=10)
            )

    # 5. Trading Plan / Golden Pocket
    if 'golden_pocket_strategy' in plan:
        gp = plan['golden_pocket_strategy']
        if gp.get('valid'):
            # Lines
            fig.add_hline(y=gp['entry'], line_dash="solid", line_color="yellow", annotation_text="ENTRY")
            fig.add_hline(y=gp['sl'], line_dash="dash", line_color="red", annotation_text="SL")
            fig.add_hline(y=gp['tp1'], line_dash="dot", line_color="green", annotation_text="TP1")
            
            # Zone
            gp_zone = gp['golden_pocket']
            color = 'rgba(255, 215, 0, 0.15)' # Gold
            fig.add_shape(type="rect",
                x0=df.index[-50], y0=gp_zone['low'], x1=df.index[-1], y1=gp_zone['high'],
                fillcolor=color, line_width=0
            )

    # 6. Layout
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        title=dict(text=f"BTC/USDT - {plan.get('direction', 'NEUTRAL')} SETUP", font=dict(size=20, color="white")),
        xaxis=dict(
            showgrid=True, gridcolor='#2a2e39', gridwidth=1,
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#2a2e39', gridwidth=1,
            side='right'
        ),
        margin=dict(l=10, r=50, t=50, b=10),
        height=1000,
        width=1600,
        showlegend=False
    )
    
    # Watermark
    fig.add_annotation(
        text="ANTIGRAVITY",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=80, color="rgba(255,255,255,0.05)")
    )

    # Save
    output_path = os.path.join(Config.ARTIFACTS_DIR, 'btc_chart_pro.png')
    try:
        fig.write_image(output_path, scale=2)
        print(f"[+] Plotly Chart Saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"[!] Error saving Plotly chart: {e}")
        return None
