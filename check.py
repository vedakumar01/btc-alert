import os, time, requests, pandas as pd
from datetime import datetime, timezone

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
LINE = "K"   # "K" = fast line (cyan), "D" = slow line (yellow)
SYMBOL = "BTCUSD"
BASES = ["https://api.india.delta.exchange", "https://cdn.india.deltaex.org"]

def send(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT, "text": text}, timeout=20)

def get_candles():
    now = int(time.time())
    params = {"resolution": "15m", "symbol": SYMBOL,
              "start": now - 250 * 900, "end": now}
    last_err = None
    for base in BASES:
        try:
            r = requests.get(f"{base}/v2/history/candles", params=params, timeout=20)
            r.raise_for_status()
            res = r.json()["result"]
            if res:
                return res
        except Exception as e:
            last_err = e
    raise RuntimeError(f"candle fetch failed: {last_err}")

now = int(time.time())
rows = sorted(get_candles(), key=lambda x: x["time"])
rows = [x for x in rows if x["time"] + 900 <= now]   # closed candles only
c = pd.Series([float(x["close"]) for x in rows])

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
tag = f"{SYMBOL} 15m ({LINE} line)"

if p <= 80 < n: send(f"{tag}: crossed ABOVE 80 ({n:.1f}) | price {price:.0f}")
if p >= 80 > n: send(f"{tag}: crossed BELOW 80 ({n:.1f}) | price {price:.0f}")
if p <= 20 < n: send(f"{tag}: crossed ABOVE 20 ({n:.1f}) | price {price:.0f}")
if p >= 20 > n: send(f"{tag}: crossed BELOW 20 ({n:.1f}) | price {price:.0f}")

t = datetime.now(timezone.utc)
if t.hour == 3 and 30 <= t.minute < 45:     # 03:30 UTC = 9:00 AM IST
    send(f"Bot alive. {SYMBOL} 15m: K={k.iloc[-1]:.1f}, D={dl.iloc[-1]:.1f}, price {price:.0f}")
