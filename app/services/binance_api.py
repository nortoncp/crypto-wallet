import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode
from datetime import datetime, UTC, timezone
from collections import defaultdict

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
FUTURES_BASE_URL = os.getenv("BINANCE_FUTURES_BASE_URL", "https://fapi.binance.com")

def get_price(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

def get_klines(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"{FUTURES_BASE_URL}/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_futures_positions():
    endpoint = "/fapi/v2/positionRisk"
    url = f"{FUTURES_BASE_URL}{endpoint}"

    timestamp = int(time.time() * 1000)
    query_string = urlencode({"timestamp": timestamp})
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    full_url = f"{url}?{query_string}&signature={signature}"

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Erro:", response.status_code, response.text)
        return None


def get_historico_futuros():
    """
    Retorna o histórico de lucros/prejuízos realizados em posições futuras no mês atual,
    agrupando entradas por símbolo e timestamp.
    """
    endpoint = "/fapi/v1/income"
    url = f"{FUTURES_BASE_URL}{endpoint}"

    timestamp = int(time.time() * 1000)
    query_string = urlencode({
        "timestamp": timestamp,
        "limit": 1000,
        "incomeType": "REALIZED_PNL"
    })

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    full_url = f"{url}?{query_string}&signature={signature}"
    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    response = requests.get(full_url, headers=headers)

    if response.status_code != 200:
        print("Erro ao obter histórico de posições:", response.status_code, response.text)
        return []

    posicoes_fechadas = response.json()

    # Filtrar apenas o mês atual
    agora = datetime.now(timezone.utc)
    mes = agora.month
    ano = agora.year

    # Agrupar entradas por símbolo e timestamp
    transacoes_agrupadas = defaultdict(lambda: {
        'symbol': '',
        'income': 0.0,
        'asset': '',
        'time': 0,
        'info': ''
    })

    for p in posicoes_fechadas:
        data = datetime.fromtimestamp(p['time'] / 1000, tz=timezone.utc)
        if data.month == mes and data.year == ano:
            chave = (p['symbol'], p['time'])
            transacoes_agrupadas[chave]['symbol'] = p['symbol']
            transacoes_agrupadas[chave]['income'] += float(p['income'])
            transacoes_agrupadas[chave]['asset'] = p['asset']
            transacoes_agrupadas[chave]['time'] = p['time']
            transacoes_agrupadas[chave]['info'] = p.get('info', '')

    # Converter o dicionário agrupado em uma lista
    historico_mes = list(transacoes_agrupadas.values())

    # Ordenar a lista por timestamp (opcional)
    historico_mes.sort(key=lambda x: x['time'], reverse=True)

    return historico_mes

def obter_saldo_futuros_usdt():
    base_url = 'https://fapi.binance.com'
    endpoint = '/fapi/v2/balance'
    timestamp = int(time.time() * 1000)
    query_string = f'timestamp={timestamp}'

    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    url = f'{base_url}{endpoint}?{query_string}&signature={signature}'
    headers = {
        'X-MBX-APIKEY': API_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dados = response.json()
        for ativo in dados:
            if ativo['asset'] == 'USDT':
                return float(ativo['balance'])
    else:
        print(f'Erro ao obter saldo: {response.status_code} - {response.text}')
        return None

def obter_saldo_spot_usdt():
    base_url = 'https://api.binance.com'
    endpoint = '/api/v3/account'
    timestamp = int(time.time() * 1000)
    query_string = f'timestamp={timestamp}'

    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    url = f'{base_url}{endpoint}?{query_string}&signature={signature}'
    headers = {
        'X-MBX-APIKEY': API_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dados = response.json()
        for ativo in dados['balances']:
            if ativo['asset'] == 'USDT':
                return float(ativo['free'])
    else:
        print(f'Erro ao obter saldo Spot: {response.status_code} - {response.text}')
        return None

def get_top_movers(limit=50, top_hots=5):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code != 200:
        print("Erro ao buscar dados da Binance:", response.text)
        return []

    dados = response.json()

    # Filtrar apenas pares com USDT e volume relevante
    usdt_pairs = [d for d in dados if d['symbol'].endswith('USDT') and float(d['quoteVolume']) > 1000000]

    # Ordenar por volume
    usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)

    # Pegar os top N com maior volume (hots)
    top_hots_list = usdt_pairs[:top_hots]

    # Pegar os top 50 para análise de gainers/losers
    top_ativos = usdt_pairs[:limit]

    # Ordenar por variação percentual
    top_gainers = sorted(top_ativos, key=lambda x: float(x['priceChangePercent']), reverse=True)[:5]
    top_losers = sorted(top_ativos, key=lambda x: float(x['priceChangePercent']))[:5]

    return {
        'hots': top_hots_list,
        'gainers': top_gainers,
        'losers': top_losers
    }




#print(get_price("BTCUSDT"))
#print(get_klines("BTCUSDT", "1h", 5))
#print(get_futures_positions())