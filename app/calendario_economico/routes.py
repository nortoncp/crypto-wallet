from flask import Blueprint, render_template
from app.services.calendario_economico import buscar_eventos_economicos


calendario_economico_bp = Blueprint('calendario_economico', __name__, template_folder='templates')

@calendario_economico_bp.route('/calendario-economico')
def index():
    eventos_economicos = buscar_eventos_economicos()

    return render_template(
        'calendario_economico.html',
        eventos_economicos=eventos_economicos,
        # outros dados que você já envia aqui...
    )