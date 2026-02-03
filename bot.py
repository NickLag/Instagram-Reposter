import requests
import schedule
import time
import os
import cv2
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# === CONFIGURAÇÕES ===
ACCESS_TOKEN = "EAALYWnFE4aYBQsCQcbgSutU9ofPb7GOCruRqZCRTUPIsS2xFhsRaX7PNxyFnXXSHad1uhoZBMmpqI9ZAUBg0uVroBZBaZBetLZB27QXbBNcWQ9irllxKZAjjMxAquZBWzwViSZBhTWvFbNqPW4fKF6yoMQS7dXWWZCZCw6V2xwZC6trNIxjzrDMzsUQxY7u9UJfg4dO4"
MY_INSTAGRAM_ID = "17841455197985437"
TARGET_USER = "dragonmusic_"
IMGBB_API_KEY = "d8708c0e7f0dae2ef239523b50ea314d"

MEDIA_DIR, EDIT_DIR, LOG_DIR = "Media", "Edit", "Log"
LOG_FILE = os.path.join(LOG_DIR, "postados_log.txt")

for folder in [MEDIA_DIR, LOG_DIR, EDIT_DIR]:
    os.makedirs(folder, exist_ok=True)

def clean_old_media():
    now = time.time()
    for folder in [MEDIA_DIR, EDIT_DIR]:
        for f in os.listdir(folder):
            f_path = os.path.join(folder, f)
            if os.stat(f_path).st_mtime < now - (7 * 86400):
                os.remove(f_path)

def upload_to_web(path):
    with open(path, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(file.read())}
        res = requests.post(url, payload).json()
        return res['data']['url'] if res.get('success') else None

def prepare_custom_image(media_url, post_id, caption_text):
    # só pra lembrar: aqui eu defini as variáveis que vão definir largura e altura, e coloquei elas como
    # parâmetro para a variável que cria o "bloco" da imagem, então é uma imagem RGb 1080x1920 nessa cor ai
    canvas_w, canvas_h = 1080, 1920
    canvas = Image.new('RGB', (canvas_w, canvas_h), color=(120, 66, 245))

    # aq eu usei a variável, ou seja, criei o bloco no formato retangular, ocupando todo o espaço do
    # story, nas cores que foram definidas dentro do canva, ou seja, é apenas uma imagem roxa preenchendo tudo
    draw = ImageDraw.Draw(canvas)

    # cria um retangulo preto centralizado nas medidas 864x778
    draw.rectangle([108, 571, 972, 1349], fill=(0, 0, 0))

    # cria um retangulo branco acima do retangulo anterior, mesma largura, baixinho, pontras superiores curvadas (864x108)
    draw.rounded_rectangle([108, 571-108, 972, 571], radius=(30, 30, 0, 0),fill=(255, 255, 255))
    # cria um retangulo branco abaixo do reatangulo anterior, mesma largura, baixinho, pontas inferiores curvadas (864x108)
    draw.rounded_rectangle([108, 1349, 972, 1349+108], radius=(0, 0, 30, 30),fill=(255, 255, 255))

    # define as variáveis das fontes
    simple_text = ImageFont.truetype("Fonts/static/Roboto_SemiCondensed-Medium.ttf", 20)
    bold_text = ImageFont.truetype("Fonts/static/Roboto-Light.ttf", 20)

    # adiciona 2 textos no bloco branco de baixo, 10 pixels abaixo do inicio dele e 2 pixels a direita do inicio dele
    # e um no meio do branco de cima, 12 pixels a direita
    draw.text((120, 571-108+44), "dragonmusic_", fill=(0, 0, 0), font=bold_text)
    draw.text((110, 1349+32), "dragonmusic_", fill=(0, 0, 0), font=bold_text)
    draw.text((130, 1349+32+25), "Veja só o que a dragon music postou: (descrição)", fill=(0, 0, 0), font=simple_text)

def share_to_story(media_url, media_type, post_id, caption):
    payload = {'media_type': 'STORIES', 'access_token': ACCESS_TOKEN}
    
    if media_type == 'VIDEO':
        # PROTOCOLO VÍDEO: Postagem direta sem edição para garantir funcionamento
        print(f"Postando vídeo {post_id} nativamente...")
        payload['video_url'] = media_url
        payload['caption'] = f'Confira esse vídeo na @{TARGET_USER} 🎵' # Menção via legenda API
    else:
        # PROTOCOLO IMAGEM: Edição completa com layout roxo
        print(f"Processando imagem {post_id} com layout personalizado...")
        local_path = prepare_custom_image(media_url, post_id, caption)
        web_url = upload_to_web(local_path)
        if not web_url: return False
        payload['image_url'] = web_url

    res = requests.post(f"https://graph.facebook.com/v18.0/{MY_INSTAGRAM_ID}/media", data=payload).json()
    
    if 'id' in res:
        creation_id = res['id']
        if media_type == 'VIDEO': 
            time.sleep(20) # Vídeos exigem mais tempo de processamento na Meta
        
        p_res = requests.post(f"https://graph.facebook.com/v18.0/{MY_INSTAGRAM_ID}/media_publish", 
                              data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
        return 'id' in p_res
    else:
        print(f"Erro na criação do container: {res}")
        return False

def check_and_post():
    print(f"[{datetime.now()}] Verificando @{TARGET_USER}...")
    clean_old_media()
    try:
        with open(LOG_FILE, "r") as f: log = f.read().splitlines()
    except: log = []
    
    url = f"https://graph.facebook.com/v18.0/{MY_INSTAGRAM_ID}"
    fields = f"business_discovery.username({TARGET_USER}){{media{{id,media_url,media_type,caption,children{{media_url,media_type}}}}}}"
    res = requests.get(url, params={'fields': fields, 'access_token': ACCESS_TOKEN}).json()
    
    posts = res.get('business_discovery', {}).get('media', {}).get('data', [])
    
    for p in posts:
        if p['id'] not in log:
            m_t, m_u = p['media_type'], p.get('media_url')
            # Trata Carrossel pegando a primeira imagem e aplicando layout
            if m_t == 'CAROUSEL_ALBUM':
                m_u, m_t = p['children']['data'][0]['media_url'], p['children']['data'][0]['media_type']
            
            if share_to_story(m_u, m_t, p['id'], p.get('caption', '')):
                with open(LOG_FILE, "a") as f: f.write(p['id'] + "\n")
                print(f"✅ Post {p['id']} enviado com sucesso!")
                return
    print("📢 Sem posts novos para compartilhar.")

if __name__ == "__main__":
    check_and_post()
    schedule.every().tuesday.at("19:00").do(check_and_post)
    schedule.every().thursday.at("19:00").do(check_and_post)
    while True:
        schedule.run_pending()
        time.sleep(60)