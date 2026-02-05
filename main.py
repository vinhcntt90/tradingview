import sys
import argparse
from .config import Config
from .data import get_btc_data, get_derivatives_data
from .indicators import calculate_indicators, calculate_sr_channels
from .analysis import (
    calculate_trading_plan, calculate_pivot_points, calculate_poc,
    analyze_timeframe_detailed, calculate_golden_pocket_strategy,
    calculate_gann_fan, get_moon_phase_simple, 
    detect_wyckoff_phase, analyze_smc
)
from .plotting import plot_plotly_chart
from .reporting import print_trading_plan, print_multi_tf_analysis
from .notifications import send_telegram_photo, send_telegram_message

def main():
    parser = argparse.ArgumentParser(description="BTC Advanced Charting")
    parser.add_argument("--test", action="store_true", help="Run in test mode (no Telegram)")
    args = parser.parse_args()

    print("\n[*] BTC Advanced Charting Started")
    
    # 1. Fetch Data
    print("[*] Fetching BTC/USDT data (15m)...")
    df = get_btc_data('15m', limit=Config.LIMIT)
    if df is None:
        print("[!] Failed to fetch data. Exiting.")
        return
    
    # 2. Daily Data for Pivots
    print("[*] Fetching Daily data for Pivots...")
    df_daily = get_btc_data('1d', limit=60)
    pivots = calculate_pivot_points(df_daily)
    
    # 3. Calculate Indicators
    print("[*] Calculating Indicators...")
    df = calculate_indicators(df)
    poc_data = calculate_poc(df)
    
    # 4. Multi-TF Analysis
    print("[*] Performing Multi-Timeframe Analysis...")
    timeframes_config = {'15m': '15m', '1H': '1h', '4H': '4h', '1D': '1d'}
    analyses = {}
    timeframes_bias = {}
    
    for tf_name, interval in timeframes_config.items():
        tf_df = get_btc_data(interval, limit=100)
        if tf_df is not None:
            ans = analyze_timeframe_detailed(tf_df, tf_name)
            analyses[tf_name] = ans
            timeframes_bias[tf_name] = ans['bias']
    
    print_multi_tf_analysis(analyses)
    
    # 5. Advanced Analysis
    print("[*] Running Advanced Analysis (SMC, Gann, Lunar)...")
    smc_data = analyze_smc(df)
    derivatives_data = get_derivatives_data()
    gann_up, _, gann_price = calculate_gann_fan(df, 'low')
    moon_phase = get_moon_phase_simple()
    
    # 6. Generate Trading Plan
    plan = calculate_trading_plan(
        df, pivots, poc_data, timeframes_bias, 
        gann_data={'lines': gann_up}, 
        lunar_data={'phase': moon_phase},
        derivatives_data=derivatives_data,
        smc_data=smc_data
    )
    
    # 7. Golden Pocket
    gp_strat = calculate_golden_pocket_strategy(df)
    plan['golden_pocket_strategy'] = gp_strat
    
    print_trading_plan(plan, pivots, poc_data)
    
    # 8. Plot Chart
    chart_path = plot_plotly_chart(df, timeframes_bias, pivots, poc_data, plan)
    
    # 9. Send Notification
    if chart_path and not args.test:
        print("[*] Sending Telegram Notification...")
        caption = f"BTC/USDT Update\nPrice: ${df['close'].iloc[-1]:,.0f}\nBias: {plan['direction']}\nScore: {plan['score']}"
        send_telegram_photo(chart_path, caption)
        
    print("[*] Done!")

if __name__ == "__main__":
    main()
