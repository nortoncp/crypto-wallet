import os
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from app.services import *


load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)


###Configura o Mercado Futuro com 2x de Alavancagem e Maregem Isolada
def configurar_mercado_futuro(symbol):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=2)
        client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
        print("✅ Mercado configurado com 2x alavancagem e margem isolada.")
    except Exception as e:
        print("Erro ao configurar mercado futuro:", e)


###Verifica se tem ordem aberta no Mercado Futuro
def existe_ordem_aberta(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        if float(pos['positionAmt']) != 0:
            return True
    return False

###Envia ordem para a Binance
def enviar_ordem_binance(symbol, tipo_ordem, preco_entrada, stop_loss, take_profit):

    configurar_mercado_futuro(symbol)

    preco_atual = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    quantidade = round(1000 / preco_atual, 3)  # Até $1000

    try:
        # Envia a ordem principal
        if tipo_ordem == 'COMPRA':
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )

            # Envia ordem de Take Profit
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                stopPrice=round(take_profit, 2),
                closePosition=True,
                timeInForce=TIME_IN_FORCE_GTC
            )

            # Envia ordem de Stop Loss
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=round(stop_loss, 2),
                closePosition=True,
                timeInForce=TIME_IN_FORCE_GTC
            )

            print("✅ Ordem de COMPRA enviada com TP e SL.")

        elif tipo_ordem == 'VENDA':
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )

            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                stopPrice=round(take_profit, 2),
                closePosition=True,
                timeInForce=TIME_IN_FORCE_GTC
            )

            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=round(stop_loss, 2),
                closePosition=True,
                timeInForce=TIME_IN_FORCE_GTC
            )

            print("✅ Ordem de VENDA enviada com TP e SL.")

    except Exception as e:
        print("Erro ao enviar ordem:", e)

