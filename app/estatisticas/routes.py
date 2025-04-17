from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import CryptoAsset

estatisticas_bp = Blueprint('estatisticas', __name__)


@estatisticas_bp.route('/estatisticas')
@login_required
def estatisticas():
    return render_template('estatisticas.html')


@estatisticas_bp.route('/estatisticas/dados')
@login_required
def grafico_dados():
    ativos = CryptoAsset.query.filter_by(user_id=current_user.id).all()

    dados = {}
    for ativo in ativos:
        data = ativo.data_compra.strftime('%d-%m-%Y')
        valor = ativo.valor_pago
        dados[data] = dados.get(data, 0) + valor

    return jsonify(sorted(dados.items()))


