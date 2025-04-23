import matplotlib.pyplot as plt
import pandas as pd
from ta.momentum import RSIIndicator
from app.services.binance_api import get_klines
from app.services.analise_tecnica import identificar_topos_fundos, calcular_fibonacci


def plot_analise_tecnica(symbol='BTCUSDT', interval='1h', limit=100):
    # Pega dados
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

    # RSI
    rsi = RSIIndicator(df["close"]).rsi()
    df["rsi"] = rsi

    # Topos e Fundos
    topos, fundos = identificar_topos_fundos(df["close"].tolist())

    # Fibonacci entre topo e fundo recentes
    if not topos or not fundos:
        print("Sem topos ou fundos suficientes.")
        return False

    topo_recente = max(topos, key=lambda x: x[0])[1]
    fundo_recente = max(fundos, key=lambda x: x[0])[1]
    fib = calcular_fibonacci(fundo_recente, topo_recente)

    # --- PLOT ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Preço
    ax1.plot(df["time"], df["close"], label="Preço", color="black")

    # Exibir apenas os níveis desejados de Fibonacci
    niveis_desejados = ['0.0', '0.382', '0.618', '1.0']
    for nivel, valor in fib.items():
        if nivel in niveis_desejados:
            estilo = '-' if nivel in ['0.382', '0.618'] else '--'
            cor = 'orange' if nivel in ['0.382', '0.618'] else 'blue'
            ax1.axhline(y=valor, linestyle=estilo, linewidth=1.5, color=cor, label=f"Fib {nivel}")

    # Topos e Fundos
    for i, valor in topos:
        ax1.plot(df["time"].iloc[i], valor, "ro")
    for i, valor in fundos:
        ax1.plot(df["time"].iloc[i], valor, "go")

    ax1.set_title(f'{symbol} - Análise Técnica')
    ax1.legend()
    ax1.grid(True)

    # RSI com destaque nas zonas de sobrecompra/sobrevenda
    ax2.plot(df["time"], df["rsi"], label="RSI", color="purple")
    ax2.axhline(30, linestyle='--', color='green', linewidth=1.5, label='Suporte RSI 30')
    ax2.axhline(70, linestyle='--', color='red', linewidth=1.5, label='Resistência RSI 70')
    ax2.set_title("Índice de Força Relativa (RSI)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()

#Para testar o gráfico
#plot_analise_tecnica()
