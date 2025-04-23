from ta.momentum import RSIIndicator
from app.services.binance_api import get_klines
from app.services.analise_tecnica import identificar_topos_fundos, calcular_fibonacci
import pandas as pd

def analise_tecnica_grafico(symbol='BTCUSDT', interval='1h', limit=100, return_json=True):
    klines = get_klines(symbol, interval, limit)
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["time"] = pd.to_datetime(df["open_time"], unit='ms')

    topos, fundos = identificar_topos_fundos(df["close"].tolist())
    topo_recente = max(topos, key=lambda x: x[0])[1]
    fundo_recente = max(fundos, key=lambda x: x[0])[1]
    fib = calcular_fibonacci(fundo_recente, topo_recente)

    rsi = RSIIndicator(df["close"]).rsi()


    data = {
        'time': df["time"].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'close': df["close"].tolist(),
        'rsi': rsi.tolist(),
        'fib': fib
    }

    if return_json:
        from flask import jsonify
        return jsonify(data)
    else:
        return data
