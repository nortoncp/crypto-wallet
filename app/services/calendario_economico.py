import requests
import os
from dotenv import load_dotenv

load_dotenv()

TRADING_ECONOMICS_API_KEY = os.getenv('TRADING_ECONOMICS_API_KEY')

def buscar_eventos_economicos(pais='Sweden', limite=5):
    if not TRADING_ECONOMICS_API_KEY:
        raise ValueError("Chave da API do Trading Economics não encontrada no .env.")

    url = f"https://api.tradingeconomics.com/calendar/country/sweden?c={TRADING_ECONOMICS_API_KEY}"

    response = requests.get(url)

    if response.status_code != 200:
        print("Erro ao acessar a API:", response.status_code, response.text)
        return []

    dados = response.json()

    eventos = []
    for evento in dados[:limite]:
        eventos.append({
            'data': evento.get('Date', evento.get('DateTime', 'N/A')),
            'evento': evento.get('Event', 'N/A'),
            'atual': evento.get('Actual', 'N/A'),
            'esperado': evento.get('Forecast', 'N/A'),
            'anterior': evento.get('Previous', 'N/A')
        })

    return eventos

