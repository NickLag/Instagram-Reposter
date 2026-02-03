import requests

# Preencha com seus dados
APP_ID = '800832912417190'
APP_SECRET = 'f77582f599a9b2da134861840d2a6bce'
SHORT_TOKEN = 'EAALYWnFE4aYBQpMsety2oZCl2omkgGPg2UKuEqdK4fZCmWXDOVmD63j0voSAsk8ZC7aAbt9Awk4mzc5FXwtyh9ZA4V3Q2m82NUbZBFE7EpUwQNvc0wGvLS7V44EHcP3qQxZAUZBaMf6GZClmFsbZBokMrn1V7QttsZCClkAJrajrCp0ZAZChXaOjyjTB0DH0phQAOsfRWStIGGaO5hfmelmgOywWpbLLhWRyuHOvwkZCOukqid4ZB0l72LcmZAFBZBkCD69VtERXhJDGosZCJpWogsieCWIKLpar9'

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