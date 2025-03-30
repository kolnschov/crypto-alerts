from flask import Flask, render_template, request, redirect, url_for
import requests
import numpy as np
import json
import os

app = Flask(__name__)

TRADE_FILE = "trades.json"

def load_trades():
    if os.path.exists(TRADE_FILE):
        with open(TRADE_FILE, 'r') as f:
            return json.load(f)
    return {
        "btc_entry_price": None, "eth_entry_price": None, "sol_entry_price": None,
        "xrp_entry_price": None, "bnb_entry_price": None, "ada_entry_price": None,
        "dot_entry_price": None, "link_entry_price": None, "avax_entry_price": None
    }

def save_trades(trades):
    with open(TRADE_FILE, 'w') as f:
        json.dump(trades, f)

trades = load_trades()
btc_entry_price = trades["btc_entry_price"]
eth_entry_price = trades["eth_entry_price"]
sol_entry_price = trades["sol_entry_price"]
xrp_entry_price = trades["xrp_entry_price"]
bnb_entry_price = trades["bnb_entry_price"]
ada_entry_price = trades["ada_entry_price"]
dot_entry_price = trades["dot_entry_price"]
link_entry_price = trades["link_entry_price"]
avax_entry_price = trades["avax_entry_price"]

def get_price(pair):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    try:
        response = requests.get(url)
        return float(response.json()["price"])
    except:
        return 0

def get_historical_data(pair, interval="5m", limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        data = response.json()
        lows = [float(candle[3]) for candle in data]
        closes = [float(candle[4]) for candle in data]
        volumes = [float(candle[5]) for candle in data]
        return {"lows": lows, "closes": closes, "volumes": volumes}
    except:
        return {"lows": [0], "closes": [0], "volumes": [0]}

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

@app.route('/', methods=['GET'])
def home():
    global btc_entry_price, eth_entry_price, sol_entry_price, xrp_entry_price
    global bnb_entry_price, ada_entry_price, dot_entry_price, link_entry_price, avax_entry_price

    # BTC/USDT
    btc_price = get_price("BTCUSDT")
    btc_data = get_historical_data("BTCUSDT")
    btc_support = min(btc_data["lows"])
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
    eth_price = get_price("ETHUSDT")
    eth_data = get_historical_data("ETHUSDT")
    eth_support = min(eth_data["lows"])
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
    sol_price = get_price("SOLUSDT")
    sol_data = get_historical_data("SOLUSDT")
    sol_support = min(sol_data["lows"])
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

    # XRP/USDT
    xrp_price = get_price("XRPUSDT")
    xrp_data = get_historical_data("XRPUSDT")
    xrp_support = min(xrp_data["lows"])
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

    # BNB/USDT
    bnb_price = get_price("BNBUSDT")
    bnb_data = get_historical_data("BNBUSDT")
    bnb_support = min(bnb_data["lows"])
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

    # ADA/USDT
    ada_price = get_price("ADAUSDT")
    ada_data = get_historical_data("ADAUSDT")
    ada_support = min(ada_data["lows"])
    ada_rsi = calculate_rsi(ada_data["closes"])
    ada_volume_avg = np.mean(ada_data["volumes"][-50:])
    ada_current_volume = ada_data["volumes"][-1]
    ada_alert = None
    ada_exit_alert = None
    ada_profit_loss = None

    if (ada_price and ada_support and ada_price <= ada_support * 1.005 and 
        ada_rsi < 30 and ada_current_volume > ada_volume_avg):
        ada_alert = f"Entrada: Suporte ${ada_support:.2f}, RSI {ada_rsi:.1f}, Vol > Média"
        print(f"ADA Alert: Price={ada_price}, Support={ada_support}, RSI={ada_rsi}, Volume={ada_current_volume}, Avg={ada_volume_avg}")

    if ada_entry_price and ada_price:
        ada_profit_loss = ((ada_price - ada_entry_price) / ada_entry_price) * 100
        ada_profit_loss = round(ada_profit_loss, 2)
        profit_5 = ada_entry_price * 1.05
        profit_10 = ada_entry_price * 1.10
        if ada_price >= profit_10:
            ada_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif ada_price >= profit_5:
            ada_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # DOT/USDT
    dot_price = get_price("DOTUSDT")
    dot_data = get_historical_data("DOTUSDT")
    dot_support = min(dot_data["lows"])
    dot_rsi = calculate_rsi(dot_data["closes"])
    dot_volume_avg = np.mean(dot_data["volumes"][-50:])
    dot_current_volume = dot_data["volumes"][-1]
    dot_alert = None
    dot_exit_alert = None
    dot_profit_loss = None

    if (dot_price and dot_support and dot_price <= dot_support * 1.005 and 
        dot_rsi < 30 and dot_current_volume > dot_volume_avg):
        dot_alert = f"Entrada: Suporte ${dot_support:.2f}, RSI {dot_rsi:.1f}, Vol > Média"
        print(f"DOT Alert: Price={dot_price}, Support={dot_support}, RSI={dot_rsi}, Volume={dot_current_volume}, Avg={dot_volume_avg}")

    if dot_entry_price and dot_price:
        dot_profit_loss = ((dot_price - dot_entry_price) / dot_entry_price) * 100
        dot_profit_loss = round(dot_profit_loss, 2)
        profit_5 = dot_entry_price * 1.05
        profit_10 = dot_entry_price * 1.10
        if dot_price >= profit_10:
            dot_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif dot_price >= profit_5:
            dot_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # LINK/USDT
    link_price = get_price("LINKUSDT")
    link_data = get_historical_data("LINKUSDT")
    link_support = min(link_data["lows"])
    link_rsi = calculate_rsi(link_data["closes"])
    link_volume_avg = np.mean(link_data["volumes"][-50:])
    link_current_volume = link_data["volumes"][-1]
    link_alert = None
    link_exit_alert = None
    link_profit_loss = None

    if (link_price and link_support and link_price <= link_support * 1.005 and 
        link_rsi < 30 and link_current_volume > link_volume_avg):
        link_alert = f"Entrada: Suporte ${link_support:.2f}, RSI {link_rsi:.1f}, Vol > Média"
        print(f"LINK Alert: Price={link_price}, Support={link_support}, RSI={link_rsi}, Volume={link_current_volume}, Avg={link_volume_avg}")

    if link_entry_price and link_price:
        link_profit_loss = ((link_price - link_entry_price) / link_entry_price) * 100
        link_profit_loss = round(link_profit_loss, 2)
        profit_5 = link_entry_price * 1.05
        profit_10 = link_entry_price * 1.10
        if link_price >= profit_10:
            link_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif link_price >= profit_5:
            link_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    # AVAX/USDT
    avax_price = get_price("AVAXUSDT")
    avax_data = get_historical_data("AVAXUSDT")
    avax_support = min(avax_data["lows"])
    avax_rsi = calculate_rsi(avax_data["closes"])
    avax_volume_avg = np.mean(avax_data["volumes"][-50:])
    avax_current_volume = avax_data["volumes"][-1]
    avax_alert = None
    avax_exit_alert = None
    avax_profit_loss = None

    if (avax_price and avax_support and avax_price <= avax_support * 1.005 and 
        avax_rsi < 30 and avax_current_volume > avax_volume_avg):
        avax_alert = f"Entrada: Suporte ${avax_support:.2f}, RSI {avax_rsi:.1f}, Vol > Média"
        print(f"AVAX Alert: Price={avax_price}, Support={avax_support}, RSI={avax_rsi}, Volume={avax_current_volume}, Avg={avax_volume_avg}")

    if avax_entry_price and avax_price:
        avax_profit_loss = ((avax_price - avax_entry_price) / avax_entry_price) * 100
        avax_profit_loss = round(avax_profit_loss, 2)
        profit_5 = avax_entry_price * 1.05
        profit_10 = avax_entry_price * 1.10
        if avax_price >= profit_10:
            avax_exit_alert = f"Saída com 10% de lucro: Venda em ${profit_10:.2f}"
        elif avax_price >= profit_5:
            avax_exit_alert = f"Saída com 5% de lucro: Venda em ${profit_5:.2f}"

    return render_template('index.html', 
                           btc_price=btc_price, btc_support=btc_support, btc_alert=btc_alert, 
                           btc_entry_price=btc_entry_price, btc_exit_alert=btc_exit_alert, btc_profit_loss=btc_profit_loss,
                           eth_price=eth_price, eth_support=eth_support, eth_alert=eth_alert, 
                           eth_entry_price=eth_entry_price, eth_exit_alert=eth_exit_alert, eth_profit_loss=eth_profit_loss,
                           sol_price=sol_price, sol_support=sol_support, sol_alert=sol_alert, 
                           sol_entry_price=sol_entry_price, sol_exit_alert=sol_exit_alert, sol_profit_loss=sol_profit_loss,
                           xrp_price=xrp_price, xrp_support=xrp_support, xrp_alert=xrp_alert, 
                           xrp_entry_price=xrp_entry_price, xrp_exit_alert=xrp_exit_alert, xrp_profit_loss=xrp_profit_loss,
                           bnb_price=bnb_price, bnb_support=bnb_support, bnb_alert=bnb_alert, 
                           bnb_entry_price=bnb_entry_price, bnb_exit_alert=bnb_exit_alert, bnb_profit_loss=bnb_profit_loss,
                           ada_price=ada_price, ada_support=ada_support, ada_alert=ada_alert, 
                           ada_entry_price=ada_entry_price, ada_exit_alert=ada_exit_alert, ada_profit_loss=ada_profit_loss,
                           dot_price=dot_price, dot_support=dot_support, dot_alert=dot_alert, 
                           dot_entry_price=dot_entry_price, dot_exit_alert=dot_exit_alert, dot_profit_loss=dot_profit_loss,
                           link_price=link_price, link_support=link_support, link_alert=link_alert, 
                           link_entry_price=link_entry_price, link_exit_alert=link_exit_alert, link_profit_loss=link_profit_loss,
                           avax_price=avax_price, avax_support=avax_support, avax_alert=avax_alert, 
                           avax_entry_price=avax_entry_price, avax_exit_alert=avax_exit_alert, avax_profit_loss=avax_profit_loss)

@app.route('/enter_btc', methods=['POST'])
def enter_btc_trade():
    global btc_entry_price
    btc_entry_price = get_price("BTCUSDT")
    trades["btc_entry_price"] = btc_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_eth', methods=['POST'])
def enter_eth_trade():
    global eth_entry_price
    eth_entry_price = get_price("ETHUSDT")
    trades["eth_entry_price"] = eth_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_sol', methods=['POST'])
def enter_sol_trade():
    global sol_entry_price
    sol_entry_price = get_price("SOLUSDT")
    trades["sol_entry_price"] = sol_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_xrp', methods=['POST'])
def enter_xrp_trade():
    global xrp_entry_price
    xrp_entry_price = get_price("XRPUSDT")
    trades["xrp_entry_price"] = xrp_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_bnb', methods=['POST'])
def enter_bnb_trade():
    global bnb_entry_price
    bnb_entry_price = get_price("BNBUSDT")
    trades["bnb_entry_price"] = bnb_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_ada', methods=['POST'])
def enter_ada_trade():
    global ada_entry_price
    ada_entry_price = get_price("ADAUSDT")
    trades["ada_entry_price"] = ada_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_dot', methods=['POST'])
def enter_dot_trade():
    global dot_entry_price
    dot_entry_price = get_price("DOTUSDT")
    trades["dot_entry_price"] = dot_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_link', methods=['POST'])
def enter_link_trade():
    global link_entry_price
    link_entry_price = get_price("LINKUSDT")
    trades["link_entry_price"] = link_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

@app.route('/enter_avax', methods=['POST'])
def enter_avax_trade():
    global avax_entry_price
    avax_entry_price = get_price("AVAXUSDT")
    trades["avax_entry_price"] = avax_entry_price
    save_trades(trades)
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)