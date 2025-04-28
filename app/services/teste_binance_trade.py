from binance_trade import enviar_ordem_binance
from app.services.binance_api import *

# Configuração para testar com BTC
symbol = 'BTCUSDT'    # Par que você quer testar
tipo_ordem = 'COMPRA' # Pode ser 'COMPRA' ou 'VENDA'

# Preço atual aproximado para cálculo do SL e TP
preco_atual = get_price("BTCUSDT")

# Define o Stop Loss e o Take Profit
stop_loss = preco_atual * 0.99   # 1% abaixo
take_profit = preco_atual * 1.01 # 1% acima

# Envia a ordem
print(f"\n🚀 Enviando {tipo_ordem} no {symbol} com SL={stop_loss:.2f} e TP={take_profit:.2f}\n")
enviar_ordem_binance(symbol, tipo_ordem, preco_atual, stop_loss, take_profit)
