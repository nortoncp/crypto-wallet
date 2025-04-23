from flask import Blueprint, render_template
from app.services.binance_api import get_futures_positions
from app.services.analise_tecnica import gerar_sinais_entrada
from app.services.plot_analise import plot_analise_tecnica
from app.services.binance_api import get_historico_futuros
from app.services.binance_api import obter_saldo_futuros_usdt


mercado_futuro_bp = Blueprint('mercado_futuro', __name__, template_folder='templates')


@mercado_futuro_bp.route('/mercado-futuro')
def mercado_futuro():
    # Buscar dados da Binance
    posicoes = get_futures_positions()
    sinais = gerar_sinais_entrada()
    analise = {'tipo': sinais[0]['tipo']} if sinais else {'tipo': 'Sem sinal'}
    historico = get_historico_futuros()
    saldo_futuros_usdt = obter_saldo_futuros_usdt()

    total_sinais = len(sinais)
    compras = len([s for s in sinais if s['tipo'] == 'COMPRA'])
    vendas = len([s for s in sinais if s['tipo'] == 'VENDA'])

    return render_template(
        'mercado_futuro.html',
        posicoes=posicoes,
        sinais=sinais,
        analise=analise,
        historico=historico,
        saldo_futuros_usdt=saldo_futuros_usdt,
        total_sinais=total_sinais,
        compras=compras,
        vendas=vendas
    )









