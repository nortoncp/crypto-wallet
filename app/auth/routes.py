from flask import Blueprint, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from app import db
from app.models import User
from flask_login import login_user, logout_user, login_required
import os
import uuid

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

@auth_bp.record_once
def setup(state):
    oauth.init_app(state.app)
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        },
        api_base_url='https://openidconnect.googleapis.com/v1/'  # Corrigido para o endpoint correto
    )

@auth_bp.route('/login')
def login():
    nonce = uuid.uuid4().hex  # Gera um nonce único
    session['nonce'] = nonce  # Salva na sessão
    redirect_uri = url_for('auth.authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)


@auth_bp.route('/authorize/google')
def authorize_google():
    token = oauth.google.authorize_access_token()
    nonce = session.get('nonce')  # Recupera o mesmo nonce salvo antes
    if not nonce:
        return "Nonce não encontrado. Faça login novamente.", 400
    print("🔐 Token recebido:", token)  # <-- aqui!
    user_info = oauth.google.parse_id_token(token, nonce=nonce)

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(email=user_info['email'], google_id=user_info['sub'])
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard.index'))
