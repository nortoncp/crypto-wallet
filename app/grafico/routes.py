from flask import Blueprint, render_template, request, flash
from app.services.analise_tecnica_grafico import analise_tecnica_grafico

grafico_bp = Blueprint('grafico', __name__, template_folder='templates')

@grafico_bp.route('/grafico')
def grafico():
    symbol = request.args.get('symbol', 'BTCUSDT').upper()
    interval = request.args.get('interval', '1h')

    try:
        data = analise_tecnica_grafico(symbol=symbol, interval=interval, return_json=False)

        if not data or 'close' not in data:
            flash(f"Erro: Não foi possível encontrar dados para {symbol}.", "danger")
            return render_template('grafico.html', data=None, selected_symbol=symbol, interval=interval)

        return render_template('grafico.html', data=data, selected_symbol=symbol, interval=interval)

    except Exception as e:
        flash(f"Erro ao buscar dados para {symbol}: {str(e)}", "danger")
        return render_template('grafico.html', data=None, selected_symbol=symbol, interval=interval)
