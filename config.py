import os
from dotenv import load_dotenv

load_dotenv()  # 👈 Isso carrega as variáveis do .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua_chave'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')


