# claudy
## 🚀 Pro Trading Terminal

A real-time crypto futures trading terminal built with Streamlit, connected to Bybit via the ccxt library. Scans for high-probability setups using Bollinger Bands, EMA 200, ATR-based risk sizing, and relative volume filters — and executes trades directly from the browser.

---

## Features

- **Live market data** — OHLCV candles streamed from Bybit (BTC, ETH, SOL)
- **Signal detection** — two strategies: Squeeze Bounce and Momentum Breakout
- **Risk engine** — auto-calculates position size, stop loss, and take profit based on ATR and your account settings
- **One-click execution** — places leveraged market orders directly on Bybit
- **Interactive chart** — candlesticks with Bollinger Bands and EMA 200 overlay
- **Secure secrets** — API keys never stored in code or git

---

## Project Structure

```
app.py                       # Main application
requirements.txt             # Python dependencies
.gitignore                   # Excludes secrets from git
.streamlit/
    secrets.toml             # API keys — local only, never commit this
```

---

## Deploying to Streamlit Cloud

### Step 1 — Push to GitHub

Make sure you **do not** include `.streamlit/secrets.toml` in the commit.

```bash
git init
git add app.py requirements.txt .gitignore
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2 — Create the app on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select your repository, branch (`main`), and entry point (`app.py`)
5. Click **Deploy**

### Step 3 — Add your Bybit API keys

Your keys are **never** stored in the code. Add them securely through the Streamlit Cloud dashboard:

**App → ⋮ menu → Settings → Secrets**

Paste the following and click Save:

```toml
[bybit]
api_key = "your_bybit_api_key"
secret  = "your_bybit_secret"
```

The app will restart automatically and pick up the credentials.

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API keys for local use
mkdir -p .streamlit
nano .streamlit/secrets.toml   # paste the [bybit] block above

# Run
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## Getting a Bybit API Key

1. Log in at [bybit.com](https://www.bybit.com)
2. Go to **Account → API Management → Create New Key**
3. Set permissions: **Read + Unified Trading** (leave withdrawals OFF)
4. Optionally whitelist your Streamlit Cloud server IP for extra security
5. Copy the API Key and Secret — you only see the secret once

---

## Trading Settings (Sidebar)

| Setting | Description |
|---|---|
| Symbol | Trading pair — BTC/USDT, ETH/USDT, SOL/USDT |
| Timeframe | Candle interval — 15m, 1h, 4h |
| Leverage | Futures leverage multiplier (1–50×) |
| Account Balance | Your USDT balance, used for position sizing |
| Risk % | Percentage of balance to risk per trade |

---

## Signal Logic

**LONG_SQUEEZE_BOUNCE** — triggers when price closes below the lower Bollinger Band while remaining above the 200 EMA. Signals a potential mean-reversion long in an established uptrend.

**MOMENTUM_BREAKOUT** — triggers when price closes above the upper Bollinger Band with relative volume above 1.5× the 20-period average, in an uptrend. Signals continuation momentum.

If neither condition is met the terminal displays **NEUTRAL** and waits.

---

## Risk Management

Stop loss and take profit are calculated automatically on every signal:

- **Stop Loss** — 2× ATR below entry (long) or above entry (short)
- **Take Profit** — 2.5× the stop distance (1:2.5 reward ratio)
- **Position size** — derived from your risk % and the distance to stop loss

> ⚠️ **This tool executes real trades with real money. Always test on a Bybit Testnet account first before going live.**

---

## Bybit Testnet (Recommended First Step)

1. Create a testnet account at [testnet.bybit.com](https://testnet.bybit.com)
2. Generate API keys there
3. In `app.py`, add `'testnet': True` to the exchange options:
```python
exchange = ccxt.bybit({
    ...
    'options': {
        'defaultType': 'linear',
        'testnet': True,
    }
})
```
4. Test the full flow with paper money before switching to live keys

---

## License

MIT — use freely, trade responsibly.
