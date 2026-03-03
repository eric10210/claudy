import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="PRO TRADING TERMINAL", page_icon="🚀", layout="wide")
st.markdown("""
<style>
    .metric-title { font-size: 18px; color: gray; }
    .metric-value { font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 PRO TRADING TERMINAL")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ SYSTEM CONFIG")

# Use Streamlit secrets if available (for cloud deployment), otherwise use input fields
# To use secrets: create .streamlit/secrets.toml with [binance] api_key = "..." secret = "..."
default_api_key = st.secrets.get("binance", {}).get("api_key", "") if hasattr(st, "secrets") else ""
default_secret   = st.secrets.get("binance", {}).get("secret", "")  if hasattr(st, "secrets") else ""

api_key = st.sidebar.text_input("API Key", type="password", value=default_api_key, help="Create in Binance account settings")
secret  = st.sidebar.text_input("Secret",  type="password", value=default_secret)

symbol           = st.sidebar.selectbox("Symbol",    ["BTC/USDT", "ETH/USDT", "SOL/USDT"], index=0)
timeframe        = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h"])
leverage         = st.sidebar.number_input("Leverage", min_value=1, max_value=50, value=10)
account_balance  = st.sidebar.number_input("Account Balance (USDT)", min_value=100, value=1000)
risk_per_trade   = st.sidebar.slider("Risk %", min_value=0.1, max_value=5.0, value=1.0)

# --- HELPER FUNCTIONS ---

def calculate_atr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['hl_range'] = df['high'] - df['low']
    prev_close = df['close'].shift(1)
    df['tr'] = pd.concat(
        [df['hl_range'], (df['high'] - prev_close).abs(), (df['low'] - prev_close).abs()],
        axis=1
    ).max(axis=1)
    df['atr'] = df['tr'].rolling(window=14).mean()
    return df


def calculate_bollinger(df: pd.DataFrame, std_dev: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    sma   = df['close'].rolling(window=20).mean()
    sigma = df['close'].rolling(window=20).std()
    df['upper'] = sma + (sigma * std_dev)
    df['lower'] = sma - (sigma * std_dev)
    return df


def get_signal(df: pd.DataFrame):
    """Return (signals list, enriched dataframe)."""
    df = df.copy()

    # 1. Trend filter — 200-period EMA (using rolling mean as approximation)
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

    # 2. Relative volume
    df['rvol'] = df['volume'] / df['volume'].rolling(20).mean()

    last          = df.iloc[-1]
    current_price = last['close']
    is_up_trend   = current_price > last['ema_200']
    signals       = []

    # SCENARIO: LONG SQUEEZE BOUNCE — price below lower band but above 200 EMA
    if current_price < last['lower'] and is_up_trend:
        signals.append('LONG_SQUEEZE_BOUNCE')

    # SCENARIO: MOMENTUM BREAKOUT — price above upper band with high volume in uptrend
    elif current_price > last['upper'] and last['rvol'] > 1.5 and is_up_trend:
        signals.append('MOMENTUM_BREAKOUT')

    return signals, df


# --- MAIN EXECUTION ---

col1, col2, col3 = st.columns(3)

with st.spinner("Loading Market Data..."):
    try:
        if api_key and secret:
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
            })

            # ── Fetch OHLCV ──────────────────────────────────────────────────
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=300)
            df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')

            df = calculate_atr(df)
            df = calculate_bollinger(df)
            signals, df = get_signal(df)   # ← fixed: unpack (signals, df) in correct order

            curr_price = df['close'].iloc[-1]
            curr_atr   = df['atr'].iloc[-1]
            curr_rvol  = df['rvol'].iloc[-1]

            # ── Signal Dashboard ─────────────────────────────────────────────
            with col1:
                st.metric("Status", signals[0] if signals else "NEUTRAL", delta="Scanning")
            with col2:
                st.metric("Volatility (ATR)", f"${curr_atr:.2f}",
                          delta=f"{(curr_atr / curr_price * 100):.3f}%")
            with col3:
                st.metric("Relative Volume", f"{curr_rvol:.1f}x",
                          delta="High" if curr_rvol > 1.5 else "Low")

            # ── Chart ────────────────────────────────────────────────────────
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df['time'], open=df['open'], high=df['high'],
                low=df['low'],  close=df['close'], name='Price'
            ))
            fig.add_trace(go.Scatter(x=df['time'], y=df['upper'],
                                     line=dict(color='red',  dash='dot'), name='BB Upper'))
            fig.add_trace(go.Scatter(x=df['time'], y=df['lower'],
                                     line=dict(color='blue', dash='dot'), name='BB Lower'))
            fig.add_trace(go.Scatter(x=df['time'], y=df['ema_200'],
                                     line=dict(color='orange', width=1), name='EMA 200'))
            fig.update_layout(
                height=450,
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Risk Engine ──────────────────────────────────────────────────
            st.divider()
            st.subheader("🛡️ Risk Engine")

            sl_points = curr_atr * 2.0        # 2× ATR stop-loss
            tp_points = sl_points * 2.5       # 1 : 2.5 reward ratio

            if signals:
                direction = "BUY" if "LONG" in signals[0] else "SELL"
                actual_sl = curr_price - sl_points if direction == "BUY" else curr_price + sl_points
                actual_tp = curr_price + tp_points if direction == "BUY" else curr_price - tp_points

                dist_risk      = abs(curr_price - actual_sl)
                risk_amount    = account_balance * (risk_per_trade / 100)
                # Position size in base currency units
                position_coins = (risk_amount / dist_risk)
                position_usdt  = position_coins * curr_price

                st.write(f"**Signal Detected:** `{direction}` — {signals[0]}")
                st.write(f"**Entry:**       ${curr_price:,.2f}")
                st.write(f"**Stop Loss:**   ${actual_sl:,.2f}  ({dist_risk / curr_price * 100:.2f}% away)")
                st.write(f"**Take Profit:** ${actual_tp:,.2f}  (1 : 2.5 ratio)")
                st.write(f"**Position Size:** {position_coins:.6f} {symbol.split('/')[0]}  "
                         f"≈ {position_usdt:,.2f} USDT  (leveraged × {leverage})")

                # ── Execute Buttons ──────────────────────────────────────────
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🔥 EXECUTE {direction}", type="primary"):
                        with st.status("Executing...", expanded=True) as status:
                            side = 'buy' if direction == 'BUY' else 'sell'
                            try:
                                order = exchange.create_market_order(
                                    symbol=symbol,
                                    side=side,
                                    amount=position_coins,
                                    params={'leverage': leverage},
                                )
                                status.update(label="✅ Trade Placed!", state="complete", expanded=False)
                                st.success(f"Order ID: {order['id']}")
                            except Exception as exc:
                                status.update(label="❌ Failed", state="error")
                                st.error(f"Execution error: {exc}")

                with col_b:
                    if st.button("🔄 Refresh Data"):
                        st.rerun()

            else:
                st.info("⏳ No high-probability setup found. Waiting for confluence…")
                if st.button("🔄 Refresh Data"):
                    st.rerun()

        else:
            st.warning("⚠️ Enter your Binance API Key & Secret in the sidebar to begin.")
            st.markdown("""
### How to connect
1. Log in to [Binance](https://www.binance.com) → **Account → API Management**
2. Create a key with **Read + Spot Trade** permissions (disable withdrawals)
3. Paste the key & secret in the sidebar  
**Or** — store them in `.streamlit/secrets.toml` (see README)
""")

    except ccxt.AuthenticationError:
        st.error("❌ Authentication failed — check your API key and secret.")
    except ccxt.NetworkError as exc:
        st.error(f"🌐 Network error: {exc}")
    except Exception as exc:
        st.error(f"Critical error: {exc}")
        st.exception(exc)   # shows full traceback in dev; remove for production