from flask import Blueprint, render_template
from app.services.analise_tecnica_grafico import analise_tecnica_grafico

grafico_bp = Blueprint('grafico', __name__, template_folder='templates')

@grafico_bp.route('/grafico')
def grafico():
    data = analise_tecnica_grafico(return_json=False)  # Alteramos aqui para retornar dict, não jsonify
    return render_template('grafico.html', data=data)











