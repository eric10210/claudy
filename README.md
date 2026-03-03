# claudy
# 🚀 Pro Trading Terminal — Streamlit Cloud Deployment

## Files
```
app.py                      ← main application
requirements.txt            ← dependencies (auto-installed by Streamlit Cloud)
.gitignore                  ← keeps secrets.toml out of git
.streamlit/secrets.toml     ← API keys (local only, never commit)
```

## Deploy to Streamlit Cloud (free)

### 1 — Push to GitHub
```bash
git init
git add app.py requirements.txt .gitignore
# DO NOT add .streamlit/secrets.toml
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2 — Create the Streamlit Cloud app
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app** → select your repo / branch / `app.py`
3. Click **Deploy**

### 3 — Add API secrets (never stored in git)
In Streamlit Cloud:  
**App → ⋮ menu → Settings → Secrets** → paste:

```toml
[binance]
api_key = "your_real_api_key"
secret  = "your_real_secret"
```

Save → the app restarts automatically with the secrets injected.

### 4 — Local development
```bash
pip install -r requirements.txt
# create .streamlit/secrets.toml with your keys (already git-ignored)
streamlit run app.py
```

## Bug fixes vs original code
| Issue | Fix |
|---|---|
| `get_signal` return order swapped (`df, signals`) | Corrected to `signals, df` |
| RSI formula used non-standard rolling min/max | Removed unused RSI; kept clean signal logic |
| `ema_200` used `rolling().mean()` (SMA, not EMA) | Switched to `ewm(span=200)` |
| No `requirements.txt` | Added |
| API keys hardcoded/exposed | Wired to `st.secrets` with sidebar fallback |
| `st.rerun()` missing on refresh button | Added |
| Chart had no EMA overlay | EMA 200 line added to chart |
