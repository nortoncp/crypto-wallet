from app import db
from flask_login import UserMixin
from app import login_manager
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    ativos = db.relationship('CryptoAsset', backref='owner', lazy=True)

class CryptoAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10))
    quantidade = db.Column(db.Float)
    valor_pago = db.Column(db.Float)
    data_compra = db.Column(db.Date, nullable=False, default=datetime)

