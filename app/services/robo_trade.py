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
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Cliente da Binance em produção
client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://fapi.binance.com/fapi'

symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_5MINUTE
lookback = "3 hours"
LOG_FILE = "robo_trade_historico_operacoes.csv"
MARGEM_MINIMA = 0.1  # margem mínima entre preço atual e TP/SL


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

def calcular_rsi(df, period=14):
    delta = df['close'].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ganho_medio = pd.Series(ganho).rolling(window=period).mean()
    perda_medio = pd.Series(perda).rolling(window=period).mean()
    rs = ganho_medio / perda_medio
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def identificar_tendencia(ema20, ema50):
    return 'alta' if ema20.iloc[-1] > ema50.iloc[-1] else 'baixa'

def encontrar_fibonacci(df):
    topo = df['high'].iloc[-30:].max()
    fundo = df['low'].iloc[-30:].min()
    nivel_038 = topo - 0.382 * (topo - fundo)
    nivel_050 = topo - 0.5 * (topo - fundo)
    nivel_061 = topo - 0.618 * (topo - fundo)
    return nivel_038, nivel_050, nivel_061

def validar_fibonacci(preco_atual, niveis):
    return any(abs(preco_atual - nivel) / preco_atual < 0.005 for nivel in niveis)

def existe_posicao_aberta(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        if float(pos['positionAmt']) != 0:
            return True
    return False

def salvar_operacao(tipo, preco_entrada, preco_tp, preco_sl):
    lucro_esperado = round(abs(preco_tp - preco_entrada), 2)
    perda_max = round(abs(preco_sl - preco_entrada), 2)
    relacao = round(lucro_esperado / perda_max, 2) if perda_max else 0
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df = pd.DataFrame([[timestamp, tipo, preco_entrada, preco_tp, preco_sl, lucro_esperado, perda_max, relacao]],
                      columns=['timestamp', 'tipo', 'entrada', 'tp', 'sl', 'lucro_esperado', 'perda_max', 'rr'])
    if not os.path.isfile(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        df.to_csv(LOG_FILE, mode='a', header=False, index=False)

def enviar_ordem(symbol, tipo_ordem, preco_atual, stop_loss, take_profit, atr):
    quantidade = round(2000 / preco_atual, 3)

    # Validação de distância mínima
    if tipo_ordem == 'COMPRA':
        if take_profit <= preco_atual + MARGEM_MINIMA or stop_loss >= preco_atual - MARGEM_MINIMA:
            print("⚠️ TP/SL inválidos para COMPRA. Ordem ignorada.")
            return
    elif tipo_ordem == 'VENDA':
        if take_profit >= preco_atual - MARGEM_MINIMA or stop_loss <= preco_atual + MARGEM_MINIMA:
            print("⚠️ TP/SL inválidos para VENDA. Ordem ignorada.")
            return

    try:
        client.futures_change_leverage(symbol=symbol, leverage=2)
        if tipo_ordem == 'COMPRA':
            client.futures_create_order(symbol=symbol, side=SIDE_BUY, type="MARKET", quantity=quantidade)

            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type="TAKE_PROFIT_MARKET",
                stopPrice=round(take_profit, 2),
                closePosition=True,
                workingType='MARK_PRICE',
                timeInForce=TIME_IN_FORCE_GTC
            )
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type="STOP_MARKET",
                stopPrice=round(stop_loss, 2),
                closePosition=True,
                workingType='MARK_PRICE',
                timeInForce=TIME_IN_FORCE_GTC
            )

        elif tipo_ordem == 'VENDA':
            client.futures_create_order(symbol=symbol, side=SIDE_SELL, type="MARKET", quantity=quantidade)

            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type="TAKE_PROFIT_MARKET",
                stopPrice=round(take_profit, 2),
                closePosition=True,
                workingType='MARK_PRICE',
                timeInForce=TIME_IN_FORCE_GTC
            )
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type="STOP_MARKET",
                stopPrice=round(stop_loss, 2),
                closePosition=True,
                workingType='MARK_PRICE',
                timeInForce=TIME_IN_FORCE_GTC
            )

        salvar_operacao(tipo_ordem, preco_atual, take_profit, stop_loss)
        ajustar_tp_sl(symbol, preco_atual, atr)
        print(
            f"✅ Ordem de {tipo_ordem} enviada | Preço: {round(preco_atual, 2)} | TP: {round(take_profit, 2)} | SL: {round(stop_loss, 2)}"
        )
    except Exception as e:
        print("❌ Erro ao enviar ordem:", e)


def ajustar_tp_sl(symbol, preco_atual, atr):
    try:
        ordens = client.futures_get_open_orders(symbol=symbol)
        # Cancelar TP/SL existentes
        for ordem in ordens:
            if ordem['type'] in ['TAKE_PROFIT_MARKET', 'STOP_MARKET']:
                client.futures_cancel_order(symbol=symbol, orderId=ordem['orderId'])
                print(f"♻️ Ordem {ordem['type']} cancelada para ajuste dinâmico.")

        posicoes = client.futures_position_information(symbol=symbol)
        for pos in posicoes:
            if float(pos['positionAmt']) != 0:
                lado = 'BUY' if float(pos['positionAmt']) > 0 else 'SELL'
                quantidade = abs(float(pos['positionAmt']))

                if lado == 'BUY':
                    novo_tp = preco_atual + 2.5 * atr
                    novo_sl = preco_atual - 1.2 * atr
                    tp_side = SIDE_SELL
                else:
                    novo_tp = preco_atual - 2.5 * atr
                    novo_sl = preco_atual + 1.2 * atr
                    tp_side = SIDE_BUY

                client.futures_create_order(
                    symbol=symbol,
                    side=tp_side,
                    type="TAKE_PROFIT_MARKET",
                    stopPrice=round(novo_tp, 2),
                    closePosition=True,
                    workingType='MARK_PRICE',
                    timeInForce=TIME_IN_FORCE_GTC
                )
                client.futures_create_order(
                    symbol=symbol,
                    side=tp_side,
                    type="STOP_MARKET",
                    stopPrice=round(novo_sl, 2),
                    closePosition=True,
                    workingType='MARK_PRICE',
                    timeInForce=TIME_IN_FORCE_GTC
                )

                print(f"✅ TP/SL ajustados dinamicamente | TP: {round(novo_tp, 2)} | SL: {round(novo_sl, 2)}")
    except Exception as e:
        print("❌ Erro ao ajustar TP/SL dinamicamente:", e)


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
    interval_trend = '15m'  # timeframe maior para tendência
    lookback_trend = '12 hours'  # suficiente para 20-50 candles de 15m

    # Dados do gráfico de 5m (sinais)
    df = obter_dados(symbol, interval, lookback)
    preco_atual = df['close'].iloc[-1]
    rsi = calcular_rsi(df)
    rsi_atual = rsi.iloc[-1]
    rsi_anterior = rsi.iloc[-2]
    atr = calcular_atr(df)

    # Dados do gráfico de 15m (tendência)
    df_trend = obter_dados(symbol, interval_trend, lookback_trend)
    ema20_trend = calcular_ema(df_trend, 20)
    ema50_trend = calcular_ema(df_trend, 50)

    # Verifica cruzamento de médias no timeframe maior
    cruzamento_alta = ema20_trend.iloc[-2] < ema50_trend.iloc[-2] and ema20_trend.iloc[-1] > ema50_trend.iloc[-1]
    cruzamento_baixa = ema20_trend.iloc[-2] > ema50_trend.iloc[-2] and ema20_trend.iloc[-1] < ema50_trend.iloc[-1]

    nivel_038, nivel_050, nivel_061 = encontrar_fibonacci(df)
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lookback_min = int(lookback.split()[0]) * 60
    interval_min = intervalo_em_minutos(interval)
    num_candles = lookback_min // interval_min

    if not validar_fibonacci(preco_atual, [nivel_038, nivel_050, nivel_061]):
        print("🔍 Preço fora dos níveis de Fibonacci. Ignorando...")
        return

    tendencia = identificar_tendencia(ema20_trend, ema50_trend)
    cor = "\033[92m" if tendencia == 'alta' else "\033[91m"
    reset = "\033[0m"

    if not existe_posicao_aberta(symbol):
        ordens_abertas = client.futures_get_open_orders(symbol=symbol)
        for ordem in ordens_abertas:
            try:
                client.futures_cancel_order(symbol=symbol, orderId=ordem['orderId'])
                print(f"🗑️ Ordem cancelada: {ordem['orderId']} ({ordem['type']})")
            except Exception as e:
                print(f"⚠️ Erro ao cancelar ordem {ordem['orderId']}: {e}")
    else:
        print(f"📈 Posição já aberta. Aguardando... Tendência atual: {cor}{tendencia.upper()}{reset}")
        movimento_forte = abs(df['close'].iloc[-1] - df['close'].iloc[-4]) > 2 * atr.iloc[-1]
        if movimento_forte:
            ajustar_tp_sl(symbol, preco_atual, atr.iloc[-1])
        return

    # Condições de entrada baseadas em RSI
    if rsi_anterior > 30 and rsi_atual < 30 and tendencia == 'alta':
        tipo_ordem = 'COMPRA'
        stop_loss = preco_atual - atr.iloc[-1]
        take_profit = preco_atual + 2 * atr.iloc[-1]
        enviar_ordem(symbol, tipo_ordem, preco_atual, stop_loss, take_profit, atr)

    elif rsi_anterior < 70 and rsi_atual > 70 and tendencia == 'baixa':
        tipo_ordem = 'VENDA'
        stop_loss = preco_atual + atr.iloc[-1]
        take_profit = preco_atual - 2 * atr.iloc[-1]
        enviar_ordem(symbol, tipo_ordem, preco_atual, stop_loss, take_profit, atr)

    else:
        print(f"⚠️ Sem Sinal de entrada 🕒 {agora} " 
              f"📈 Tendência atual grafico {interval_trend}: {cor}{tendencia.upper()}{reset} "
              f"📊 Operacional para o gráfico de {interval} baseada nos últimos {num_candles} candles")


# Agendamento a cada 60 segundos
schedule.every(60).seconds.do(analisar_e_operar)

print("🤖 Bot PRODUÇÃO Mercado Futuro iniciado. Verificando sinais a cada 60 segundos...")
while True:
    schedule.run_pending()
    time.sleep(1)
