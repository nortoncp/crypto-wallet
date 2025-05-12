import os
import time
import schedule
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from datetime import datetime, timezone

# Timestamp para logs
timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

# Carregar variáveis do ambiente
load_dotenv()
API_KEY = os.getenv("TESTNET_BINANCE_API_KEY")
API_SECRET = os.getenv("TESTNET_BINANCE_API_SECRET")

# Cliente da Binance em produção
client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://testnet.binance.com/fapi'

symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_1MINUTE
lookback = "3 hours"

def obter_dados(symbol, interval, lookback):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df = df[['open', 'high', 'low', 'close']]
    df = df.astype(float)
    return df

def calcular_ema(df, period):
    return df['close'].ewm(span=period, adjust=False).mean()


def identificar_tendencia(ema20, ema50):
    return 'alta' if ema20.iloc[-1] > ema50.iloc[-1] else 'baixa'


def existe_posicao_aberta(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        if float(pos['positionAmt']) != 0:
            return True
    return False

def obter_tipo_posicao(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        if float(pos['positionAmt']) > 0:
            return 'COMPRA'
        elif float(pos['positionAmt']) < 0:
            return 'VENDA'
    return None



def enviar_ordem(symbol, tipo, preco_atual):
    # quantidade deve ser calculada conforme seu saldo e risco
    quantidade = round(2000 / preco_atual, 3)

    lado = 'BUY' if tipo == 'COMPRA' else 'SELL'
    try:
        client.futures_change_leverage(symbol=symbol, leverage=2)
        client.futures_create_order(
            symbol=symbol,
            side=lado,
            type='MARKET',
            quantity=quantidade
        )
        print(f"✅ Ordem de {tipo} enviada com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao enviar ordem de {tipo}: {e}")

def fechar_posicao(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        amt = float(pos['positionAmt'])
        if amt == 0:
            return
        lado = 'SELL' if amt > 0 else 'BUY'
        try:
            client.futures_create_order(
                symbol=symbol,
                side=lado,
                type='MARKET',
                quantity=abs(amt)
            )
            print(f"❌ Posição encerrada com ordem de {lado}.")
        except Exception as e:
            print(f"⚠️ Erro ao fechar posição: {e}")

def verificar_lucro_e_fechar(symbol, preco_atual):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        amt = float(pos['positionAmt'])
        if amt == 0:
            continue
        entry_price = float(pos['entryPrice'])
        pnl_percent = ((preco_atual - entry_price) / entry_price) * 100 if amt > 0 else ((entry_price - preco_atual) / entry_price) * 100
        if pnl_percent >= 0.5:
            fechar_posicao(symbol)
            print(f"🎯 Take Profit atingido ({pnl_percent:.2f}%). Posição encerrada.")


def intervalo_em_minutos(interval):
    unidades = {
        'm': 1,
        'h': 60,
        'd': 1440
    }
    valor = int(''.join(filter(str.isdigit, interval)))
    unidade = ''.join(filter(str.isalpha, interval))
    return valor * unidades[unidade]

def analisar_e_operar():
    try:
        df = obter_dados(symbol, interval, lookback)
        preco_atual = df['close'].iloc[-1]
        # ✅ Verifica se já pode realizar o lucro
        verificar_lucro_e_fechar(symbol, preco_atual)
        ema20 = calcular_ema(df, 20)
        ema50 = calcular_ema(df, 50)
        # Verifica cruzamento de médias
        cruzamento_alta = ema20.iloc[-2] < ema50.iloc[-2] and ema20.iloc[-1] > ema50.iloc[-1]
        cruzamento_baixa = ema20.iloc[-2] > ema50.iloc[-2] and ema20.iloc[-1] < ema50.iloc[-1]
        # Verifica o tipo de posição que esta aberta
        posicao = obter_tipo_posicao(symbol)  # 'COMPRA', 'VENDA' ou None

        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lookback_min = int(lookback.split()[0]) * 60  # "3 hours" -> 180 minutos
        interval_min = intervalo_em_minutos(interval)  # '5m' -> 5
        num_candles = lookback_min // interval_min

        tendencia = identificar_tendencia(ema20, ema50)
        cor = "\033[92m" if tendencia == 'alta' else "\033[91m"
        reset = "\033[0m"

        if cruzamento_alta:
            if posicao == 'VENDA':
                fechar_posicao(symbol)
                print("🔄 Reversão: Fechando VENDA e abrindo COMPRA...")
                enviar_ordem(symbol, 'COMPRA', preco_atual)
            elif posicao is None:
                print("📈 Cruzamento de alta. Abrindo COMPRA...")
                enviar_ordem(symbol, 'COMPRA', preco_atual)
            else:
                print("📈 Mantendo COMPRA...")

        elif cruzamento_baixa:
            if posicao == 'COMPRA':
                fechar_posicao(symbol)
                print("🔄 Reversão: Fechando COMPRA e abrindo VENDA...")
                enviar_ordem(symbol, 'VENDA', preco_atual)
            elif posicao is None:
                print("📉 Cruzamento de baixa. Abrindo VENDA...")
                enviar_ordem(symbol, 'VENDA', preco_atual)
            else:
                print("📉 Mantendo VENDA...")

        else:
            print(f"⚠️ Nenhum Cruzamento EMAs, Aguardando 🕒 {agora} " 
                  f"📈 Tendência atual: {cor}{tendencia.upper()}{reset} "
                  f"📊 Análise para o gráfico de {interval} baseada nos últimos {num_candles} candles")

        # (Opcional futuro)
        # Salvar log no arquivo:
        # with open("bot_logs.txt", "a") as f:
        #     f.write(f"{agora} - Tendência: {tendencia.upper()} | EMA20: {ema20.iloc[-1]} | EMA50: {ema50.iloc[-1]}\n")

    except Exception as e:
        print(f"❌ Erro inesperado na análise/operação: {e}")



# Agendamento a cada 30 segundos
schedule.every(30).seconds.do(analisar_e_operar)

print("🤖 Bot PRODUÇÃO Mercado Futuro iniciado. Verificando sinais a cada 30 segundos...")
while True:
    schedule.run_pending()
    time.sleep(1)


