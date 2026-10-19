import os, time, requests, pandas as pd
from datetime import datetime, timezone

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
LINE = "K"   # "K" = fast line (cyan), "D" = slow line (yellow)

def send(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT, "text": text}, timeout=20)

r = requests.get("https://data-api.binance.vision/api/v3/klines",
                 params={"symbol": "BTCUSDT", "interval": "15m", "limit": 200},
                 timeout=20)
r.raise_for_status()
now_ms = int(time.time() * 1000)
rows = [x for x in r.json() if x[6] < now_ms]   # closed candles only
c = pd.Series([float(x[4]) for x in rows])

d = c.diff()
up = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
dn = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
rsi = 100 - 100 / (1 + up / dn)
lo, hi = rsi.rolling(14).min(), rsi.rolling(14).max()
k = ((rsi - lo) / (hi - lo) * 100).rolling(3).mean()
dl = k.rolling(3).mean()
s = k if LINE == "K" else dl

p, n = s.iloc[-2], s.iloc[-1]    # previous and latest closed candle
price = c.iloc[-1]
tag = f"BTCUSDT 15m ({LINE} line)"

if p <= 80 < n: send(f"{tag}: crossed ABOVE 80 ({n:.1f}) | price {price:.0f}")
if p >= 80 > n: send(f"{tag}: crossed BELOW 80 ({n:.1f}) | price {price:.0f}")
if p <= 20 < n: send(f"{tag}: crossed ABOVE 20 ({n:.1f}) | price {price:.0f}")
if p >= 20 > n: send(f"{tag}: crossed BELOW 20 ({n:.1f}) | price {price:.0f}")

t = datetime.now(timezone.utc)
if True:     # 03:30 UTC = 9:00 AM IST
    send(f"Bot alive. BTCUSDT 15m: K={k.iloc[-1]:.1f}, D={dl.iloc[-1]:.1f}, price {price:.0f}")
