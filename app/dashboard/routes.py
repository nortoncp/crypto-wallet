from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import CryptoAsset
from app.services.cryptopanic_api import get_btc_news
from app.services.binance_api import get_price
from app.services.binance_api import obter_saldo_futuros_usdt
from app.services.binance_api import obter_saldo_spot_usdt
from app.services.binance_api import get_top_movers


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    ativos = CryptoAsset.query.filter_by(user_id=current_user.id).all()
    total_investido = round(sum(a.quantidade * a.valor_pago for a in ativos), 2)
    valor_atual_total = round(sum(a.quantidade * get_price(a.symbol) for a in ativos), 2)
    lucro_prejuizo_total = round(valor_atual_total - total_investido, 2)
    saldo_futuros_usdt = obter_saldo_futuros_usdt()
    saldo_spot_usdt = obter_saldo_spot_usdt()
    top_movers = get_top_movers()

    carteira = []

    for ativo in ativos:
        preco_atual = get_price(ativo.symbol)
        preco_medio = ativo.valor_pago / ativo.quantidade
        lucro_prejuizo = (preco_atual - ativo.valor_pago) * ativo.quantidade
        variacao = ((preco_atual - ativo.valor_pago) / ativo.valor_pago) * 100

        carteira.append({
            'id': ativo.id,
            'data_compra': ativo.data_compra,
            'symbol': ativo.symbol,
            'quantidade': ativo.quantidade,
            'valor_pago': ativo.valor_pago,
            'preco_atual': preco_atual,
            'preco_medio': round(preco_medio, 2),
            'lucro_prejuizo': round(lucro_prejuizo, 2),
            'variacao': round(variacao, 2)
        })

    noticias = get_btc_news()
    return render_template('home.html', total_investido=total_investido, noticias=noticias, carteira=carteira, valor_atual_total=valor_atual_total, lucro_prejuizo_total=lucro_prejuizo_total, saldo_futuros_usdt=saldo_futuros_usdt, saldo_spot_usdt=saldo_spot_usdt, top_movers=top_movers )


