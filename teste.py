import requests

# Preencha com seus dados
APP_ID = ''
APP_SECRET = ''
SHORT_TOKEN = ''

def get_long_lived_token():
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': APP_ID,
        'client_secret': APP_SECRET,
        'fb_exchange_token': SHORT_TOKEN
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'access_token' in data:
        print("\n✅ Token de Longa Duração gerado com sucesso!")
        print(f"Novo Token: {data['access_token']}")
        print(f"Expira em: {data.get('expires_in', 'N/A')} segundos")
    else:
        print("❌ Erro:", data)

get_long_lived_token()