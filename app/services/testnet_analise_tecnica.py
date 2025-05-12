import requests
import numpy as np
from scipy.signal import argrelextrema
import pandas as pd
from fontTools.misc.cython import returns
from ta.momentum import RSIIndicator
from app.services.testnet_binance_api import  get_klines
from app.services.testnet_binance_trade import existe_ordem_aberta
from app.services.telegram_alert import enviar_alerta_telegram
import os
from dotenv import load_dotenv
from datetime import datetime
from app.services.testnet_binance_trade import *





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

def calcular_volatilidade_media(closes):
    variacoes = [abs(closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))]
    return sum(variacoes) / len(variacoes)

def detectar_tendencia(df):
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()

    if df['MA50'].iloc[-1] > df['MA200'].iloc[-1]:
        return 'ALTA'
    elif df['MA50'].iloc[-1] < df['MA200'].iloc[-1]:
        return 'BAIXA'
    else:
        return 'LATERAL'


def identificar_lta_ltb(df):
    df['min'] = df['low'][argrelextrema(df['low'].values, np.less_equal, order=5)[0]]
    df['max'] = df['high'][argrelextrema(df['high'].values, np.greater_equal, order=5)[0]]

    ultimos_fundos = df.dropna(subset=['min']).tail(2)
    ultimos_topos = df.dropna(subset=['max']).tail(2)

    lta = None
    ltb = None

    if len(ultimos_fundos) == 2:
        lta = (ultimos_fundos.index[0], ultimos_fundos['min'].iloc[0]), \
            (ultimos_fundos.index[1], ultimos_fundos['min'].iloc[1])

    if len(ultimos_topos) == 2:
        ltb = (ultimos_topos.index[0], ultimos_topos['max'].iloc[0]), \
            (ultimos_topos.index[1], ultimos_topos['max'].iloc[1])

    return lta, ltb


def gerar_sinais_entrada(simbolo='BTCUSDT', intervalo='1h', limite=100):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Executando análise técnica para {simbolo} ({intervalo})")

    klines = get_klines(simbolo, intervalo, limite)
    closes = [float(kline[4]) for kline in klines]

    topos, fundos = identificar_topos_fundos(closes)
    sinais = []

    if not topos or not fundos:
        print("⚠️ Nenhum topo ou fundo identificado.")
        return []

    volatilidade = calcular_volatilidade_media(closes)
    print(f"📊 Volatilidade média: {volatilidade:.2f}%")

    topo_recente = max(topos, key=lambda x: x[0])[1]
    fundo_recente = max(fundos, key=lambda x: x[0])[1]
    fib = calcular_fibonacci(fundo_recente, topo_recente)
    rsi = calcular_rsi(closes)
    rsi_atual = rsi.iloc[-1]
    preco_atual = closes[-1]

    # 🧠 Detectando tendência com MME curta e longa
    df = pd.DataFrame({'close': closes})
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()

    tendencia = 'ALTA' if df['ema20'].iloc[-1] > df['ema50'].iloc[-1] else 'BAIXA'
    print(f"📈 Tendência detectada: {tendencia}")

    # 📉 Linhas de tendência com últimos topos e fundos
    ultimos_fundos = sorted(fundos, key=lambda x: x[0])[-2:]
    ultimos_topos = sorted(topos, key=lambda x: x[0])[-2:]

    lta_valida = len(ultimos_fundos) == 2
    ltb_valida = len(ultimos_topos) == 2

    stop_percent = (volatilidade * 2) / 100
    take_percent = (volatilidade * 3) / 100

    stop_loss = round(preco_atual * (1 - stop_percent), 2)
    take_profit = round(preco_atual * (1 + take_percent), 2)

    # Verifica se existe uma ordem aberta no Mercado Futuro antes de enviar alerta
    if existe_ordem_aberta(simbolo):
        print("🚫 Já existe Posição aberta no Mercado Futuro.")
        return []

    if rsi_atual < 30 and preco_atual <= fib["0.618"] and tendencia == 'ALTA' and lta_valida:
        print(f"📈 Sinal de COMPRA detectado: preço={preco_atual}, RSI={rsi_atual:.2f}, Fib=0.618")
        sinais.append({
            'tipo': 'COMPRA',
            'entrada': preco_atual,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'rsi': round(rsi_atual, 2),
            'nivel_fibonacci': '0.618',
            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'tendencia': tendencia
        })
        mensagem = f"🚀 **Sinal de COMPRA**\n\nEntrada: ${preco_atual}\nStop Loss: ${stop_loss}\nTake Profit: ${take_profit}\nRSI: {round(rsi_atual, 2)}\nFibonacci: 0.618\nTendência: {tendencia}"
        enviar_alerta_telegram(token, chat_id, mensagem)
        enviar_ordem_binance(simbolo, 'COMPRA', preco_atual, stop_loss, take_profit)

    elif rsi_atual > 70 and preco_atual >= fib["0.382"] and tendencia == 'BAIXA' and ltb_valida:
        stop_loss_venda = round(preco_atual * (1 + stop_percent), 2)
        take_profit_venda = round(preco_atual * (1 - take_percent), 2)

        print(f"📉 Sinal de VENDA detectado: preço={preco_atual}, RSI={rsi_atual:.2f}, Fib=0.382")
        sinais.append({
            'tipo': 'VENDA',
            'entrada': preco_atual,
            'stop_loss': stop_loss_venda,
            'take_profit': take_profit_venda,
            'rsi': round(rsi_atual, 2),
            'nivel_fibonacci': '0.382',
            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'tendencia': tendencia
        })
        mensagem = f"⚠️ **Sinal de VENDA**\n\nEntrada: ${preco_atual}\nStop Loss: ${stop_loss_venda}\nTake Profit: ${take_profit_venda}\nRSI: {round(rsi_atual, 2)}\nFibonacci: 0.382\nTendência: {tendencia}"
        enviar_alerta_telegram(token, chat_id, mensagem)
        enviar_ordem_binance(simbolo, 'VENDA', preco_atual, stop_loss_venda, take_profit_venda)

    return sinais


