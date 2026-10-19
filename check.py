import os, requests, pandas as pd

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]

r = requests.get("https://data-api.binance.vision/api/v3/klines",
                 params={"symbol": "BTCUSDT", "interval": "15m", "limit": 200},
                 timeout=20)
r.raise_for_status()
c = pd.Series([float(x[4]) for x in r.json()])

d = c.diff()
up = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
dn = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
rsi = 100 - 100 / (1 + up / dn)
lo, hi = rsi.rolling(14).min(), rsi.rolling(14).max()
k = ((rsi - lo) / (hi - lo) * 100).rolling(3).mean()

p, n = k.iloc[-3], k.iloc[-2]   # last two closed candles
msg = None
if p <= 80 < n: msg = f"BTCUSDT 15m: StochRSI crossed ABOVE 80 ({n:.1f})"
if p >= 20 > n: msg = f"BTCUSDT 15m: StochRSI crossed BELOW 20 ({n:.1f})"
if msg:
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT, "text": msg}, timeout=20)
if msg:
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT, "text": msg}, timeout=20)
