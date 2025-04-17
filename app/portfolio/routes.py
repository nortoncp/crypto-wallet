from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.portfolio.forms import AtivoForm
from app.models import CryptoAsset
from app import db
from flask import flash

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_ativo():
    form = AtivoForm()
    if form.validate_on_submit():
        ativo = CryptoAsset(
            user_id=current_user.id,
            symbol=form.symbol.data.upper(),
            quantidade=form.quantidade.data,
            valor_pago=form.valor_pago.data,
            data_compra=form.data_compra.data

        )
        db.session.add(ativo)
        db.session.commit()
        return redirect(url_for('dashboard.index'))
    
    return render_template('portfolio.html', form=form)

@portfolio_bp.route('/excluir/<int:ativo_id>', methods=['POST'])
@login_required
def excluir_ativo(ativo_id):
    ativo = CryptoAsset.query.get_or_404(ativo_id)

    # Garante que o ativo pertence ao usuário logado
    if ativo.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))

    db.session.delete(ativo)
    db.session.commit()
    flash(f'Ativo {ativo.symbol} excluído com sucesso.', 'success')
    return redirect(url_for('dashboard.index'))



