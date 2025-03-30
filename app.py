from flask import Flask, render_template, request, redirect, url_for
import requests
import numpy as np
import json
import os
import time

app = Flask(__name__)

TRADE_FILE = "trades.json"
CACHE_FILE = "price_cache.json"
SUPPORT_FILE = "support_cache.json"
CACHE_TIMEOUT = 300  # Cache de preços por 5 minutos
SUPPORT_TIMEOUT = 604800  # Recalcular suportes a cada 7 dias

def load_trades():
    if os.path.exists(TRADE_FILE):
        with open(TRADE_FILE, 'r') as f:
            return json.load(f)
    return {
        "btc_entry_price": None, "eth_entry_price": None, "sol_entry_price": None,
        "bnb_entry_price": None, "xrp_entry_price": None
    }

def save_trades(trades):
    with open(TRADE_FILE, 'w') as f:
        json.dump(trades, f)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if time.time() - cache.get("timestamp", 0) < CACHE_TIMEOUT:
            return cache.get("prices", {})
    return None

def save_cache(prices):
    cache = {"timestamp": time.time(), "prices": prices}
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def load_support_cache():
    if os.path.exists(SUPPORT_FILE):
        with open(SUPPORT_FILE, 'r') as f:
            cache = json.load(f)
        if time.time() - cache.get("timestamp", 0) < SUPPORT_TIMEOUT:
            return cache.get("supports", {})
    return None

def save_support_cache(supports):
    cache = {"timestamp": time.time(), "supports": supports}
    with open(SUPPORT_FILE, 'w') as f:
        json.dump(cache, f)

def get_price(pair):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data["price"])
        print(f"{pair} Price fetched: {price}")
        return price
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {pair} price: {str(e)}")
        return 0

def get_historical_data(pair, interval="1h", limit=168):  # 7 dias em 1h
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        lows = [float(candle[3]) for candle in data]
        closes = [float(candle[4]) for candle in data]
        volumes = [float(candle[5]) for candle in data]
        support = min(lows)  # Mínima dos últimos 7 dias
        print(f"{pair} Support fetched: {support}")
        return {"lows": lows, "closes": closes, "volumes": volumes, "support": support}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {pair} historical data: {str(e)}")
        return {"lows": [0], "closes": [0], "volumes": [0], "support": 0}

def get_all_prices_and_supports():
    cached_prices = load_cache()
    cached_supports = load_support_cache()

    pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    prices = {}
    supports = {}

    if cached_prices and cached_supports:
        print("Using cached prices and supports:", cached_prices, cached_supports)
        return cached_prices, cached_supports

    for pair in pairs:
        prices[pair] = get_price(pair)
        hist_data = get_historical_data(pair)
        supports[pair] = hist_data["support"]

    save_cache(prices)
    save_support_cache(supports)
    return prices, supports

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
bnb_entry_price = trades["bnb_entry_price"]
xrp_entry_price = trades["xrp_entry_price"]

@app.route('/', methods=['GET'])
def home():
    global btc_entry_price, eth_entry_price, sol_entry_price, bnb_entry_price, xrp_entry_price

    prices, supports = get_all_prices_and_supports()

    # BTC/USDT
    btc_price = prices["BTCUSDT"]
    btc_data = get_historical_data("BTCUSDT")
    btc_support = supports["BTCUSDT"]
    btc_rsi = calculate_rsi(btc_data["closes"])
    btc_volume_avg = np.mean(btc_data["volumes"][-50:])
    btc_current_volume = btc_data["volumes"][-1]
    btc_alert = None
    btc_exit_alert = None
    btc_profit_loss = None

    if (btc_price and btc_support and btc_price <= btc_support * 1.005 and 
        btc_rsi < 30 and btc_current_volume > btc_volume_avg):
        btc_alert = f"Entrada: Suporte ${btc_support:.2f}, RSI {btc_rsi:.1f}, Vol > Média"
        print(f"BTC Alert: Price={btc_price}, Support={btc_support}, RSI={btc_rsi}, Volume={btc_current_volume}, Avg={btc_volume_avg}")

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
    eth_data = get_historical_data("ETHUSDT")
    eth_support = supports["ETHUSDT"]
    eth_rsi = calculate_rsi(eth_data["closes"])
    eth_volume_avg = np.mean(eth_data["volumes"][-50:])
    eth_current_volume = eth_data["volumes"][-1]
    eth_alert = None
    eth_exit_alert = None
    eth_profit_loss = None

    if (eth_price and eth_support and eth_price <= eth_support * 1.005 and 
        eth_rsi < 30 and eth_current_volume > eth_volume_avg):
        eth_alert = f"Entrada: Suporte ${eth_support:.2f}, RSI {eth_rsi:.1f}, Vol > Média"
        print(f"ETH Alert: Price={eth_price}, Support={eth_support}, RSI={eth_rsi}, Volume={eth_current_volume}, Avg={eth_volume_avg}")

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
    sol_data = get_historical_data("SOLUSDT")
    sol_support = supports["SOLUSDT"]
    sol_rsi = calculate_rsi(sol_data["closes"])
    sol_volume_avg = np.mean(sol_data["volumes"][-50:])
    sol_current_volume = sol_data["volumes"][-1]
    sol_alert = None
    sol_exit_alert = None
    sol_profit_loss = None

    if (sol_price and sol_support and sol_price <= sol_support * 1.005 and 
        sol_rsi < 30 and sol_current_volume > sol_volume_avg):
        sol_alert = f"Entrada: Suporte ${sol_support:.2f}, RSI {sol_rsi:.1f}, Vol > Média"
        print(f"SOL Alert: Price={sol_price}, Support={sol_support}, RSI={sol_rsi}, Volume={sol_current_volume}, Avg={sol_volume_avg}")

    if sol_entry_price and sol_price:
        sol_profit_loss = ((sol_price - sol_entry_price) / sol_entry_price) * 100
        sol_profit_loss = round(sol_profit_loss, 2)
        profit_5 = sol_entry_price * 1.05
        profit_10 = sol_entry_price * 1.10
        if sol_price >= profit_10:
            sol_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif sol_price >= profit_5:
            sol_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # BNB/USDT
    bnb_price = prices["BNBUSDT"]
    bnb_data = get_historical_data("BNBUSDT")
    bnb_support = supports["BNBUSDT"]
    bnb_rsi = calculate_rsi(bnb_data["closes"])
    bnb_volume_avg = np.mean(bnb_data["volumes"][-50:])
    bnb_current_volume = bnb_data["volumes"][-1]
    bnb_alert = None
    bnb_exit_alert = None
    bnb_profit_loss = None

    if (bnb_price and bnb_support and bnb_price <= bnb_support * 1.005 and 
        bnb_rsi < 30 and bnb_current_volume > bnb_volume_avg):
        bnb_alert = f"Entrada: Suporte ${bnb_support:.2f}, RSI {bnb_rsi:.1f}, Vol > Média"
        print(f"BNB Alert: Price={bnb_price}, Support={bnb_support}, RSI={bnb_rsi}, Volume={bnb_current_volume}, Avg={bnb_volume_avg}")

    if bnb_entry_price and bnb_price:
        bnb_profit_loss = ((bnb_price - bnb_entry_price) / bnb_entry_price) * 100
        bnb_profit_loss = round(bnb_profit_loss, 2)
        profit_5 = bnb_entry_price * 1.05
        profit_10 = bnb_entry_price * 1.10
        if bnb_price >= profit_10:
            bnb_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif bnb_price >= profit_5:
            bnb_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # XRP/USDT
    xrp_price = prices["XRPUSDT"]
    xrp_data = get_historical_data("XRPUSDT")
    xrp_support = supports["XRPUSDT"]
    xrp_rsi = calculate_rsi(xrp_data["closes"])
    xrp_volume_avg = np.mean(xrp_data["volumes"][-50:])
    xrp_current_volume = xrp_data["volumes"][-1]
    xrp_alert = None
    xrp_exit_alert = None
    xrp_profit_loss = None

    if (xrp_price and xrp_support and xrp_price <= xrp_support * 1.005 and 
        xrp_rsi < 30 and xrp_current_volume > xrp_volume_avg):
        xrp_alert = f"Entrada: Suporte ${xrp_support:.2f}, RSI {xrp_rsi:.1f}, Vol > Média"
        print(f"XRP Alert: Price={xrp_price}, Support={xrp_support}, RSI={xrp_rsi}, Volume={xrp_current_volume}, Avg={xrp_volume_avg}")

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
                           btc_price=btc_price, btc_support=btc_support, btc_alert=btc_alert, 
                           btc_entry_price=btc_entry_price, btc_exit_alert=btc_exit_alert, btc_profit_loss=btc_profit_loss,
                           eth_price=eth_price, eth_support=eth_support, eth_alert=eth_alert, 
                           eth_entry_price=eth_entry_price, eth_exit_alert=eth_exit_alert, eth_profit_loss=eth_profit_loss,
                           sol_price=sol_price, sol_support=sol_support, sol_alert=sol_alert, 
                           sol_entry_price=sol_entry_price, sol_exit_alert=sol_exit_alert, sol_profit_loss=sol_profit_loss,
                           bnb_price=bnb_price, bnb_support=bnb_support, bnb_alert=bnb_alert, 
                           bnb_entry_price=bnb_entry_price, bnb_exit_alert=bnb_exit_alert, bnb_profit_loss=bnb_profit_loss,
                           xrp_price=xrp_price, xrp_support=xrp_support, xrp_alert=xrp_alert, 
                           xrp_entry_price=xrp_entry_price, xrp_exit_alert=xrp_exit_alert, xrp_profit_loss=xrp_profit_loss)

@app.route('/enter_btc', methods=['POST'])
def enter_btc_trade():
    global btc_entry_price
    prices, _ = get_all_prices_and_supports()
    btc_entry_price = prices["BTCUSDT"]
    trades["btc_entry_price"] = btc_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_eth', methods=['POST'])
def enter_eth_trade():
    global eth_entry_price
    prices, _ = get_all_prices_and_supports()
    eth_entry_price = prices["ETHUSDT"]
    trades["eth_entry_price"] = eth_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_sol', methods=['POST'])
def enter_sol_trade():
    global sol_entry_price
    prices, _ = get_all_prices_and_supports()
    sol_entry_price = prices["SOLUSDT"]
    trades["sol_entry_price"] = sol_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_bnb', methods=['POST'])
def enter_bnb_trade():
    global bnb_entry_price
    prices, _ = get_all_prices_and_supports()
    bnb_entry_price = prices["BNBUSDT"]
    trades["bnb_entry_price"] = bnb_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_xrp', methods=['POST'])
def enter_xrp_trade():
    global xrp_entry_price
    prices, _ = get_all_prices_and_supports()
    xrp_entry_price = prices["XRPUSDT"]
    trades["xrp_entry_price"] = xrp_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)