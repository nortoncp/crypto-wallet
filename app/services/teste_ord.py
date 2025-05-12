import os
import time
import schedule
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

# Carregar variáveis do ambiente
load_dotenv()
API_KEY = os.getenv("TESTNET_BINANCE_API_KEY")
API_SECRET = os.getenv("TESTNET_BINANCE_API_SECRET")

# Cliente da Binance Testnet
client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'

def enviar_ordem_teste(symbol="BTCUSDT"):
    from binance.enums import SIDE_BUY

    preco_atual = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    quantidade = round(1000 / preco_atual, 3)

    stop_loss = round(preco_atual * 0.99, 2)      # 1% abaixo
    take_profit = round(preco_atual * 1.02, 2)     # 2% acima

    try:

        client.futures_change_leverage(symbol=symbol, leverage=2)
        # Ordem de compra
        client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type="MARKET",
            quantity=quantidade
        )

        # TP
        client.futures_create_order(
            symbol=symbol,
            side="SELL",
            type="TAKE_PROFIT_MARKET",
            stopPrice=take_profit,
            closePosition=True,
            timeInForce="GTC"
        )

        # SL
        client.futures_create_order(
            symbol=symbol,
            side="SELL",
            type="STOP_MARKET",
            stopPrice=stop_loss,
            closePosition=True,
            timeInForce="GTC"
        )

        print(
            f"✅ Ordem de COMPRA enviada: Preço atual = {round(preco_atual, 2)}, com TP = {round(take_profit, 2)}, SL = {round(stop_loss, 2)}.")

    except Exception as e:
        print("❌ Erro ao enviar ordem de teste:", e)


enviar_ordem_teste("BTCUSDT")
