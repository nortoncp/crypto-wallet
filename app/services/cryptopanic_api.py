import requests

API_KEY = '2babbff78ce87a8e079ad58919d9b43971e2bf94'

def get_btc_news():
    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={API_KEY}&currencies=BTC&public=true'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])
