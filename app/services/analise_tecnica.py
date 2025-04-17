import requests
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from app.services.binance_api import get_klines
from app.services.telegram_alert import enviar_alerta_telegram
import os
from dotenv import load_dotenv
from datetime import datetime


# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('CHAT_ID')


def identificar_topos_fundos(precos):
    topos = []
    fundos = []

    for i in range(2, len(precos) - 2):
        if precos[i] > precos[i - 1] and precos[i] > precos[i + 1]:
            topos.append((i, precos[i]))
        elif precos[i] < precos[i - 1] and precos[i] < precos[i + 1]:
            fundos.append((i, precos[i]))

    return topos, fundos

def calcular_fibonacci(fundo, topo):
    diff = topo - fundo
    niveis = {
        "0.0": topo,
        "0.236": topo - diff * 0.236,
        "0.382": topo - diff * 0.382,
        "0.5": topo - diff * 0.5,
        "0.618": topo - diff * 0.618,
        "1.0": fundo
    }
    return niveis

def calcular_rsi(close_prices):
    rsi = RSIIndicator(pd.Series(close_prices), window=14).rsi()
    return rsi

def gerar_sinais_entrada(simbolo='BTCUSDT', intervalo='1h', limite=100):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Executando análise técnica para {simbolo} ({intervalo})")
    klines = get_klines(simbolo, intervalo, limite)
    closes = [float(kline[4]) for kline in klines]
    highs = [float(kline[2]) for kline in klines]
    lows = [float(kline[3]) for kline in klines]

    topos, fundos = identificar_topos_fundos(closes)
    sinais = []

    if not topos or not fundos:
        print("⚠️ Nenhum topo ou fundo identificado.")
        return []

    topo_recente = max(topos, key=lambda x: x[0])[1]
    fundo_recente = max(fundos, key=lambda x: x[0])[1]

    fib = calcular_fibonacci(fundo_recente, topo_recente)
    rsi = calcular_rsi(closes)
    rsi_atual = rsi.iloc[-1]

    preco_atual = closes[-1]
    stop_loss = round(preco_atual * 0.99, 2)  # 1% abaixo
    take_profit = round(preco_atual * 1.02, 2)  # 2% acima

    if rsi_atual < 30 and preco_atual <= fib["0.618"]:
        print(f"📈 Sinal de COMPRA detectado: preço={preco_atual}, RSI={rsi_atual}, Fib=0.618")
        sinais.append({
            'tipo': 'COMPRA',
            'entrada': preco_atual,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'rsi': round(rsi_atual, 2),
            'nivel_fibonacci': '0.618'
        })

        # Enviar alerta no Telegram
        mensagem = f"🚀 **Sinal de COMPRA**\n\nEntrada: ${preco_atual}\nStop Loss: ${stop_loss}\nTake Profit: ${take_profit}\nRSI: {round(rsi_atual, 2)}\nFibonacci: 0.618"
        enviar_alerta_telegram(token, chat_id, mensagem)


    elif rsi_atual > 70 and preco_atual >= fib["0.382"]:
        print(f"📉 Sinal de VENDA detectado: preço={preco_atual}, RSI={rsi_atual}, Fib=0.382")
        sinais.append({
            'tipo': 'VENDA',
            'entrada': preco_atual,
            'stop_loss': round(preco_atual * 1.01, 2),
            'take_profit': round(preco_atual * 0.98, 2),
            'rsi': round(rsi_atual, 2),
            'nivel_fibonacci': '0.382'
        })

        # Enviar alerta no Telegram
        mensagem = f"⚠️ **Sinal de VENDA**\n\nEntrada: ${preco_atual}\nStop Loss: ${round(preco_atual * 1.01, 2)}\nTake Profit: ${round(preco_atual * 0.98, 2)}\nRSI: {round(rsi_atual, 2)}\nFibonacci: 0.382"
        enviar_alerta_telegram(token, chat_id, mensagem)


    return sinais


