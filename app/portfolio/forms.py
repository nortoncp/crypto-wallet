from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, DateField
from wtforms.validators import DataRequired



class AtivoForm(FlaskForm):
    data_compra = DateField('Data da Compra', format='%Y-%m-%d', validators=[DataRequired()])
    symbol = StringField('Criptomoeda (ex: BTCUSDT)', validators=[DataRequired()])
    quantidade = FloatField('Quantidade', validators=[DataRequired()])
    valor_pago = FloatField('Valor da Crypto no momento da compra (USDT)', validators=[DataRequired()])
    submit = SubmitField('Salvar')
