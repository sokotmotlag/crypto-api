from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
TFS = ["4h", "1h", "15m", "5m"]

def klines(sym, tf):
    r = requests.get("https://api.binance.com/api/v3/klines",
                     params={"symbol": sym, "interval": tf, "limit": 100},
                     timeout=10)
    d = r.json()
    return ([float(k[4]) for k in d],   # close
            [float(k[2]) for k in d],   # high
            [float(k[3]) for k in d])   # low

def ema(v, n):
    k, e = 2 / (n + 1), v[0]
    for x in v[1:]:
        e = x * k + e * (1 - k)
    return e

def rsi(v, n=14):
    g = l = 0
    for i in range(1, n + 1):
        d = v[i] - v[i - 1]
        g += max(d, 0); l += max(-d, 0)
    g, l = g / n, l / n
    for i in range(n + 1, len(v)):
        d = v[i] - v[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
    return 100 if l == 0 else 100 - 100 / (1 + g / l)

def analyze(sym, tf):
    c, h, l = klines(sym, tf)
    p = c[-1]
    e20, e50 = ema(c, 20), ema(c, 50)
    trend = "صعودی" if p > e20 > e50 else "نزولی" if p < e20 < e50 else "خنثی"
    return {"price": p, "trend": trend, "rsi": round(rsi(c), 1),
            "support": min(l[-50:]), "resistance": max(h[-50:])}

@app.route("/analyze")
def run():
    sym = request.args.get("symbol", "BTCUSDT").upper()
    res = {tf: analyze(sym, tf) for tf in TFS}
    t4, t1 = res["4h"]["trend"], res["1h"]["trend"]
    s5, s15 = res["5m"], res["15m"]
    signal = {"type": "منتظر بمان", "entry": None, "sl": None, "tp": None}
    if t4 == t1 == "صعودی" and s15["rsi"] < 40:
        signal = {"type": "خرید", "entry": s5["price"],
                  "sl": s15["support"], "tp": res["1h"]["resistance"]}
    elif t4 == t1 == "نزولی" and s15["rsi"] > 60:
        signal = {"type": "فروش", "entry": s5["price"],
                  "sl": s15["resistance"], "tp": res["1h"]["support"]}
    return jsonify({"symbol": sym, "frames": res, "signal": signal,
                    "note": "تحلیل آموزشی، نه توصیه مالی"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
