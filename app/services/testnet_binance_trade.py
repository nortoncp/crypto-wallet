import os
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from app.services import *

load_dotenv()
API_KEY = os.getenv("TESTNET_BINANCE_API_KEY")
API_SECRET = os.getenv("TESTNET_BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET, testnet=True)

### Configura o Mercado Futuro com 2x de Alavancagem e Margem Isolada
def configurar_mercado_futuro(symbol):
    try:
        # Tenta obter as informações da bolsa
        info = client.futures_exchange_info()

        # Inicializa a variável que armazenará o tipo de margem
        margin_type = None

        # Verifica os símbolos para encontrar o tipo de margem
        for s in info['symbols']:
            if s['symbol'] == symbol:
                margin_type = s['marginType']
                break

        # Se o tipo de margem não for isolado, tenta configurá-lo
        if margin_type != 'ISOLATED':
            client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED', ignoreError=True)
            print("✅ Margem isolada configurada.")

        # Configura a alavancagem para 2x
        client.futures_change_leverage(symbol=symbol, leverage=2)
        print("✅ Alavancagem de 2x configurada.")

    except Exception as e:
        print("Erro ao configurar mercado futuro:", e)


### Verifica se tem ordem aberta no Mercado Futuro
def existe_ordem_aberta(symbol):
    posicoes = client.futures_position_information(symbol=symbol)
    for pos in posicoes:
        if float(pos['positionAmt']) != 0:
            return True
    return False


### Envia ordem para a Binance
def enviar_ordem_binance(symbol, tipo_ordem, preco_entrada, stop_loss, take_profit):

    preco_atual = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    quantidade = round(1000 / preco_atual, 3)  # Até $1000

    try:
        if tipo_ordem == 'COMPRA':
            # Ordem principal - COMPRA
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )

            # Ordem de Take Profit
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_TAKE_PROFIT,
                stopPrice=round(take_profit, 2),
                timeInForce=TIME_IN_FORCE_GTC,
                priceProtect=False,
                quantity=quantidade
            )

            # Ordem de Stop Loss
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_LOSS,
                stopPrice=round(stop_loss, 2),
                timeInForce=TIME_IN_FORCE_GTC,
                priceProtect=False,
                quantity=quantidade
            )

            print("✅ Ordem de COMPRA enviada com TP e SL.")

        elif tipo_ordem == 'VENDA':
            # Ordem principal - VENDA
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )

            # Ordem de Take Profit
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_TAKE_PROFIT,
                price=round(take_profit, 2),
                timeInForce=TIME_IN_FORCE_GTC,
                priceProtect=True,
                quantity=quantidade,
            )

            # Ordem de Stop Loss
            client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS,
                stopPrice=round(stop_loss, 2),
                timeInForce=TIME_IN_FORCE_GTC,
                priceProtect=True,
                quantity=quantidade
            )

            print("✅ Ordem de VENDA enviada com TP e SL.")

    except Exception as e:
        print("❌ Erro ao enviar ordem:", e)
