import requests
import os
from flask.cli import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_alerta_telegram(TELEGRAM_TOKEN, CHAT_ID, mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'  # ou 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.ok
#Para envio de testes de Alertas
#print(enviar_alerta_telegram("Vai dar bom esse bot"))