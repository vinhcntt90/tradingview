from datetime import datetime

def print_multi_tf_analysis(analyses):
    """Print detailed multi-timeframe analysis table"""
    print("\n" + "=" * 90)
    print("  MULTI-TIMEFRAME DETAILED ANALYSIS")
    print("=" * 90)
    print(f"  {'TF':<6} {'Price':>12} {'RSI':>8} {'BIAS':>10}")
    print("  " + "-" * 88)
    
    for tf in ['15m', '1H', '4H', '1D']:
        if tf in analyses:
            d = analyses[tf]
            print(f"  {tf:<6} ${d['price']:>10,.0f} {d['rsi']:>7.1f} {d['bias']}")
            
    return "NEUTRAL"

def print_trading_plan(plan, pivots, poc_data):
    """Print formatted trading plan"""
    print("\n" + "=" * 60)
    print("  TRADING PLAN - " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    print("=" * 60)
    print(f"  DIRECTION: {plan['direction']} (Score: {plan['score']})")
    
    if plan['direction'] == 'LONG':
        lp = plan['long']
        print(f"  >>> LONG at ${lp['entry']:,.0f}")
        print(f"      SL: ${lp['sl']:,.0f}")
        print(f"      TP1: ${lp['tp1']:,.0f} | TP2: ${lp['tp2']:,.0f}")
    elif plan['direction'] == 'SHORT':
        sp = plan['short']
        print(f"  >>> SHORT at ${sp['entry']:,.0f}")
        print(f"      SL: ${sp['sl']:,.0f}")
        print(f"      TP1: ${sp['tp1']:,.0f} | TP2: ${sp['tp2']:,.0f}")
    
    print("=" * 60)
