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

    # Identificar topos e fundos
    topos, fundos = identificar_topos_fundos(df["close"].tolist())

    # Inicializa fib vazio
    fib = {}

    # Pega o último topo e último fundo para calcular Fibonacci
    if topos and fundos:
        topo_recente_idx, topo_recente_val = max(topos, key=lambda x: x[0])
        fundo_recente_idx, fundo_recente_val = max(fundos, key=lambda x: x[0])

        # Só cria o Fibonacci se tiver uma distância aceitável
        if abs(topo_recente_idx - fundo_recente_idx) > 5:  # Exemplo: mínimo 5 candles de diferença
            fib_values = calcular_fibonacci(fundo_recente_val, topo_recente_val)
            inicio = min(fundo_recente_idx, topo_recente_idx)
            fim = max(fundo_recente_idx, topo_recente_idx)

            fib = {
                nivel: {
                    "valor": valor,
                    "inicio": inicio,
                    "fim": fim
                }
                for nivel, valor in fib_values.items()
            }

    # Calcula o RSI
    rsi = RSIIndicator(df["close"]).rsi()

    # Prepara listas de topos e fundos para o gráfico
    topos_lista = [None] * len(df)
    fundos_lista = [None] * len(df)
    for idx, value in topos:
        if idx < len(topos_lista):
            topos_lista[idx] = value
    for idx, value in fundos:
        if idx < len(fundos_lista):
            fundos_lista[idx] = value

    # Função para calcular linhas de tendência (simples)
    def calcular_linha_tendencia(pontos):
        if len(pontos) < 2:
            return [None] * len(df)
        idx1, valor1 = pontos[-2]
        idx2, valor2 = pontos[-1]
        if idx2 - idx1 == 0:
            return [None] * len(df)
        m = (valor2 - valor1) / (idx2 - idx1)
        linha = [None] * len(df)
        for i in range(len(df)):
            if idx1 <= i <= idx2:
                linha[i] = valor1 + m * (i - idx1)
        return linha

    # Calcula LTA e LTB baseados nos fundos e topos
    lta = calcular_linha_tendencia(fundos)
    ltb = calcular_linha_tendencia(topos)

    # Monta o dicionário final de dados
    data = {
        'time': df["time"].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'close': df["close"].tolist(),
        'rsi': rsi.tolist(),
        'fib': fib,
        'topos': topos_lista,
        'fundos': fundos_lista,
        'lta': lta,
        'ltb': ltb
    }

    if return_json:
        from flask import jsonify
        return jsonify(data)
    else:
        return data
