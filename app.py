from flask import Flask, render_template, request, redirect, url_for
import requests
import numpy as np
import json
import os
import time

app = Flask(__name__)

TRADE_FILE = "trades.json"
SUPPORT_FILE_5MIN = "support_cache_5min.json"
SUPPORT_FILE_1H = "support_cache_1h.json"
SUPPORT_TIMEOUT_5MIN = 86400  # Recalcular suportes 5min a cada 24 horas
SUPPORT_TIMEOUT_1H = 604800   # Recalcular suportes 1h a cada 7 dias

def load_trades():
    if os.path.exists(TRADE_FILE):
        with open(TRADE_FILE, 'r') as f:
            return json.load(f)
    return {
        "btc_entry_price": None, "eth_entry_price": None, "sol_entry_price": None,
        "xrp_entry_price": None
    }

def save_trades(trades):
    with open(TRADE_FILE, 'w') as f:
        json.dump(trades, f)

def load_support_cache(filename, timeout):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cache = json.load(f)
        if time.time() - cache.get("timestamp", 0) < timeout:
            return cache.get("supports", {})
    return None

def save_support_cache(filename, supports):
    cache = {"timestamp": time.time(), "supports": supports}
    with open(filename, 'w') as f:
        json.dump(cache, f)

def get_price(pair):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data["result"][pair]["c"][0])  # Último preço de fechamento
        print(f"{time.strftime('%H:%M:%S')} - {pair} Price fetched: {price}")
        return price
    except requests.exceptions.RequestException as e:
        print(f"{time.strftime('%H:%M:%S')} - Error fetching {pair} price: {str(e)}")
        return 0
    except (KeyError, ValueError) as e:
        print(f"{time.strftime('%H:%M:%S')} - Error parsing {pair} price data: {str(e)}")
        return 0

def get_historical_data(pair, interval=5, since=None):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    if since:
        url += f"&since={since}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()["result"][pair]
        limit = 288 if interval == 5 else 168
        data = data[-limit:] if len(data) > limit else data
        lows = [float(candle[3]) for candle in data]
        closes = [float(candle[4]) for candle in data]
        volumes = [float(candle[5]) for candle in data]
        support = min(lows)
        print(f"{time.strftime('%H:%M:%S')} - {pair} {interval}min Support fetched: {support}")
        return {"lows": lows, "closes": closes, "volumes": volumes, "support": support}
    except requests.exceptions.RequestException as e:
        print(f"{time.strftime('%H:%M:%S')} - Error fetching {pair} {interval}min historical data: {str(e)}")
        return {"lows": [0], "closes": [0], "volumes": [0], "support": 0}
    except (KeyError, ValueError) as e:
        print(f"{time.strftime('%H:%M:%S')} - Error parsing {pair} {interval}min historical data: {str(e)}")
        return {"lows": [0], "closes": [0], "volumes": [0], "support": 0}

def get_all_prices_and_supports():
    cached_supports_5min = load_support_cache(SUPPORT_FILE_5MIN, SUPPORT_TIMEOUT_5MIN)
    cached_supports_1h = load_support_cache(SUPPORT_FILE_1H, SUPPORT_TIMEOUT_1H)

    pairs = ["XBTUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    prices = {}
    supports_5min = {}
    supports_1h = {}

    # Preços em tempo real (sem cache)
    for pair in pairs:
        prices[pair] = get_price(pair)

    # Suportes 5min (24h de velas de 5min)
    if cached_supports_5min:
        supports_5min = cached_supports_5min
        print(f"{time.strftime('%H:%M:%S')} - Using cached supports (5min):", supports_5min)
    else:
        for pair in pairs:
            hist_data = get_historical_data(pair, interval=5)
            supports_5min[pair] = hist_data["support"]
        save_support_cache(SUPPORT_FILE_5MIN, supports_5min)

    # Suportes 1h (7 dias de velas de 1h)
    if cached_supports_1h:
        supports_1h = cached_supports_1h
        print(f"{time.strftime('%H:%M:%S')} - Using cached supports (1h):", supports_1h)
    else:
        for pair in pairs:
            hist_data = get_historical_data(pair, interval=60)
            supports_1h[pair] = hist_data["support"]
        save_support_cache(SUPPORT_FILE_1H, supports_1h)

    return prices, supports_5min, supports_1h

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    deltas = np.diff(closes)
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

trades = load_trades()
btc_entry_price = trades["btc_entry_price"]
eth_entry_price = trades["eth_entry_price"]
sol_entry_price = trades["sol_entry_price"]
xrp_entry_price = trades["xrp_entry_price"]

@app.route('/', methods=['GET'])
def home():
    global btc_entry_price, eth_entry_price, sol_entry_price, xrp_entry_price

    prices, supports_5min, supports_1h = get_all_prices_and_supports()

    # BTC/USDT
    btc_price = prices["XBTUSDT"]
    btc_data_5min = get_historical_data("XBTUSDT", interval=5)
    btc_data_1h = get_historical_data("XBTUSDT", interval=60)
    btc_support_5min = supports_5min["XBTUSDT"]
    btc_support_1h = supports_1h["XBTUSDT"]
    btc_rsi_5min = calculate_rsi(btc_data_5min["closes"])
    btc_rsi_1h = calculate_rsi(btc_data_1h["closes"])
    btc_volume_avg_5min = np.mean(btc_data_5min["volumes"][-50:])
    btc_volume_avg_1h = np.mean(btc_data_1h["volumes"][-50:])
    btc_current_volume_5min = btc_data_5min["volumes"][-1]
    btc_current_volume_1h = btc_data_1h["volumes"][-1]
    btc_alert = None
    btc_exit_alert = None
    btc_profit_loss = None

    if (btc_price and btc_support_5min and btc_price <= btc_support_5min * 1.005 and 
        btc_rsi_5min < 30 and btc_current_volume_5min > btc_volume_avg_5min):
        btc_alert = "Alerta de entrada de 5 minutos"
        print(f"{time.strftime('%H:%M:%S')} - BTC 5min Alert: Price={btc_price}, Support={btc_support_5min}, RSI={btc_rsi_5min}, Volume={btc_current_volume_5min}, Avg={btc_volume_avg_5min}")
    elif (btc_price and btc_support_1h and btc_price <= btc_support_1h * 1.005 and 
          btc_rsi_1h < 30 and btc_current_volume_1h > btc_volume_avg_1h):
        btc_alert = "Alerta de entrada de 1 hora"
        print(f"{time.strftime('%H:%M:%S')} - BTC 1h Alert: Price={btc_price}, Support={btc_support_1h}, RSI={btc_rsi_1h}, Volume={btc_current_volume_1h}, Avg={btc_volume_avg_1h}")

    if btc_entry_price and btc_price:
        btc_profit_loss = ((btc_price - btc_entry_price) / btc_entry_price) * 100
        btc_profit_loss = round(btc_profit_loss, 2)
        profit_5 = btc_entry_price * 1.05
        profit_10 = btc_entry_price * 1.10
        if btc_price >= profit_10:
            btc_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif btc_price >= profit_5:
            btc_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # ETH/USDT
    eth_price = prices["ETHUSDT"]
    eth_data_5min = get_historical_data("ETHUSDT", interval=5)
    eth_data_1h = get_historical_data("ETHUSDT", interval=60)
    eth_support_5min = supports_5min["ETHUSDT"]
    eth_support_1h = supports_1h["ETHUSDT"]
    eth_rsi_5min = calculate_rsi(eth_data_5min["closes"])
    eth_rsi_1h = calculate_rsi(eth_data_1h["closes"])
    eth_volume_avg_5min = np.mean(eth_data_5min["volumes"][-50:])
    eth_volume_avg_1h = np.mean(eth_data_1h["volumes"][-50:])
    eth_current_volume_5min = eth_data_5min["volumes"][-1]
    eth_current_volume_1h = eth_data_1h["volumes"][-1]
    eth_alert = None
    eth_exit_alert = None
    eth_profit_loss = None

    if (eth_price and eth_support_5min and eth_price <= eth_support_5min * 1.005 and 
        eth_rsi_5min < 30 and eth_current_volume_5min > eth_volume_avg_5min):
        eth_alert = "Alerta de entrada de 5 minutos"
        print(f"{time.strftime('%H:%M:%S')} - ETH 5min Alert: Price={eth_price}, Support={eth_support_5min}, RSI={eth_rsi_5min}, Volume={eth_current_volume_5min}, Avg={eth_volume_avg_5min}")
    elif (eth_price and eth_support_1h and eth_price <= eth_support_1h * 1.005 and 
          eth_rsi_1h < 30 and eth_current_volume_1h > eth_volume_avg_1h):
        eth_alert = "Alerta de entrada de 1 hora"
        print(f"{time.strftime('%H:%M:%S')} - ETH 1h Alert: Price={eth_price}, Support={eth_support_1h}, RSI={eth_rsi_1h}, Volume={eth_current_volume_1h}, Avg={eth_volume_avg_1h}")

    if eth_entry_price and eth_price:
        eth_profit_loss = ((eth_price - eth_entry_price) / eth_entry_price) * 100
        eth_profit_loss = round(eth_profit_loss, 2)
        profit_5 = eth_entry_price * 1.05
        profit_10 = eth_entry_price * 1.10
        if eth_price >= profit_10:
            eth_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif eth_price >= profit_5:
            eth_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # SOL/USDT
    sol_price = prices["SOLUSDT"]
    sol_data_5min = get_historical_data("SOLUSDT", interval=5)
    sol_data_1h = get_historical_data("SOLUSDT", interval=60)
    sol_support_5min = supports_5min["SOLUSDT"]
    sol_support_1h = supports_1h["SOLUSDT"]
    sol_rsi_5min = calculate_rsi(sol_data_5min["closes"])
    sol_rsi_1h = calculate_rsi(sol_data_1h["closes"])
    sol_volume_avg_5min = np.mean(sol_data_5min["volumes"][-50:])
    sol_volume_avg_1h = np.mean(sol_data_1h["volumes"][-50:])
    sol_current_volume_5min = sol_data_5min["volumes"][-1]
    sol_current_volume_1h = sol_data_1h["volumes"][-1]
    sol_alert = None
    sol_exit_alert = None
    sol_profit_loss = None

    if (sol_price and sol_support_5min and sol_price <= sol_support_5min * 1.005 and 
        sol_rsi_5min < 30 and sol_current_volume_5min > sol_volume_avg_5min):
        sol_alert = "Alerta de entrada de 5 minutos"
        print(f"{time.strftime('%H:%M:%S')} - SOL 5min Alert: Price={sol_price}, Support={sol_support_5min}, RSI={sol_rsi_5min}, Volume={sol_current_volume_5min}, Avg={sol_volume_avg_5min}")
    elif (sol_price and sol_support_1h and sol_price <= sol_support_1h * 1.005 and 
          sol_rsi_1h < 30 and sol_current_volume_1h > sol_volume_avg_1h):
        sol_alert = "Alerta de entrada de 1 hora"
        print(f"{time.strftime('%H:%M:%S')} - SOL 1h Alert: Price={sol_price}, Support={sol_support_1h}, RSI={sol_rsi_1h}, Volume={sol_current_volume_1h}, Avg={sol_volume_avg_1h}")

    if sol_entry_price and sol_price:
        sol_profit_loss = ((sol_price - sol_entry_price) / sol_entry_price) * 100
        sol_profit_loss = round(sol_profit_loss, 2)
        profit_5 = sol_entry_price * 1.05
        profit_10 = sol_entry_price * 1.10
        if sol_price >= profit_10:
            sol_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif sol_price >= profit_5:
            sol_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # XRP/USDT
    xrp_price = prices["XRPUSDT"]
    xrp_data_5min = get_historical_data("XRPUSDT", interval=5)
    xrp_data_1h = get_historical_data("XRPUSDT", interval=60)
    xrp_support_5min = supports_5min["XRPUSDT"]
    xrp_support_1h = supports_1h["XRPUSDT"]
    xrp_rsi_5min = calculate_rsi(xrp_data_5min["closes"])
    xrp_rsi_1h = calculate_rsi(xrp_data_1h["closes"])
    xrp_volume_avg_5min = np.mean(xrp_data_5min["volumes"][-50:])
    xrp_volume_avg_1h = np.mean(xrp_data_1h["volumes"][-50:])
    xrp_current_volume_5min = xrp_data_5min["volumes"][-1]
    xrp_current_volume_1h = xrp_data_1h["volumes"][-1]
    xrp_alert = None
    xrp_exit_alert = None
    xrp_profit_loss = None

    if (xrp_price and xrp_support_5min and xrp_price <= xrp_support_5min * 1.005 and 
        xrp_rsi_5min < 30 and xrp_current_volume_5min > xrp_volume_avg_5min):
        xrp_alert = "Alerta de entrada de 5 minutos"
        print(f"{time.strftime('%H:%M:%S')} - XRP 5min Alert: Price={xrp_price}, Support={xrp_support_5min}, RSI={xrp_rsi_5min}, Volume={xrp_current_volume_5min}, Avg={xrp_volume_avg_5min}")
    elif (xrp_price and xrp_support_1h and xrp_price <= xrp_support_1h * 1.005 and 
          xrp_rsi_1h < 30 and xrp_current_volume_1h > xrp_volume_avg_1h):
        xrp_alert = "Alerta de entrada de 1 hora"
        print(f"{time.strftime('%H:%M:%S')} - XRP 1h Alert: Price={xrp_price}, Support={xrp_support_1h}, RSI={xrp_rsi_1h}, Volume={xrp_current_volume_1h}, Avg={xrp_volume_avg_1h}")

    if xrp_entry_price and xrp_price:
        xrp_profit_loss = ((xrp_price - xrp_entry_price) / xrp_entry_price) * 100
        xrp_profit_loss = round(xrp_profit_loss, 2)
        profit_5 = xrp_entry_price * 1.05
        profit_10 = xrp_entry_price * 1.10
        if xrp_price >= profit_10:
            xrp_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif xrp_price >= profit_5:
            xrp_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    return render_template('index.html', 
                           btc_price=btc_price, btc_support_5min=btc_support_5min, btc_support_1h=btc_support_1h, btc_alert=btc_alert, 
                           btc_entry_price=btc_entry_price, btc_exit_alert=btc_exit_alert, btc_profit_loss=btc_profit_loss,
                           eth_price=eth_price, eth_support_5min=eth_support_5min, eth_support_1h=eth_support_1h, eth_alert=eth_alert, 
                           eth_entry_price=eth_entry_price, eth_exit_alert=eth_exit_alert, eth_profit_loss=eth_profit_loss,
                           sol_price=sol_price, sol_support_5min=sol_support_5min, sol_support_1h=sol_support_1h, sol_alert=sol_alert, 
                           sol_entry_price=sol_entry_price, sol_exit_alert=sol_exit_alert, sol_profit_loss=sol_profit_loss,
                           xrp_price=xrp_price, xrp_suppor