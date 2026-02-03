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
ACCESS_TOKEN = ""
MY_INSTAGRAM_ID = ""
TARGET_USER = ""
IMGBB_API_KEY = ""

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
    try:
        response = requests.get(media_url)
        post_img = Image.open(BytesIO(response.content)).convert("RGB")

        max_w, max_h = 864, 778
        post_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        img_w, img_h = post_img.size
        img_x = 108 + (max_w - img_w) // 2
        img_y = 571 + (max_h - img_h) // 2

        canvas.paste(post_img, (img_x, img_y))

    except Exception as e:
        print(f"Erro de processar  imagem do post: {e}")

    # cria um retangulo branco acima do retangulo anterior, mesma largura, baixinho, pontras superiores curvadas (864x108)
    draw.rounded_rectangle([108, 571-108, 972, 571], radius=30,fill=(255, 255, 255))
    # cria um retangulo branco abaixo do reatangulo anterior, mesma largura, baixinho, pontas inferiores curvadas (864x108)
    draw.rounded_rectangle([108, 1349, 972, 1349+108], radius=30,fill=(255, 255, 255))

    profile_size = 64
    profile_path = os.path.join("Images", "dragon.png")

    try:
        profile_img = Image.open(profile_path).convert("RGBA")
        profile_img = profile_img.resize((profile_size, profile_size), Image.Resampling.LANCZOS)

        mask = Image.new('L', (profile_size, profile_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, profile_size, profile_size), fill=255)

        profile_img.putalpha(mask)

        canvas.paste(profile_img, (124, 485), profile_img)

    except Exception as e:
        print(f"Erro ao carregar imagem de perfil: {e}")

    # define as variáveis das fontes
    simple_text = ImageFont.truetype("Fonts/static/Roboto_SemiCondensed-Medium.ttf", 20)
    bold_text = ImageFont.truetype("Fonts/static/Roboto-Light.ttf", 20)

    # adiciona 2 textos no bloco branco de baixo, 10 pixels abaixo do inicio dele e 2 pixels a direita do inicio dele
    # e um no meio do branco de cima, 12 pixels a direita
    draw.text((200, 571-108+44), "dragonmusic_", fill=(0, 0, 0), font=bold_text)

    username = "dragonmusic_"
    y_linha1 = 1349 + 32
    y_linha2 = y_linha1 + 20 + 4
    x_inicio = 110
    x_limite = 970

    largura_user = bold_text.getlength(username)
    x_desc_linha1 = x_inicio + largura_user + 2
    max_w_linha1 = x_limite - x_desc_linha1
    max_w_linha2 = x_limite - x_inicio

    def fatiar_texto(texto, fonte, largura_maxima):
        acumulado = ""
        for char in texto:
            if fonte.getlength(acumulado + char) <= largura_maxima:
                acumulado += char
            else:
                break
        return acumulado
    
    linha1_conteudo = fatiar_texto(caption_text, simple_text, max_w_linha1)
    sobra = caption_text[len(linha1_conteudo):].strip()

    if sobra:
        if simple_text.getlength(sobra) > max_w_linha2:
            largura_com_pontos = max_w_linha2 - simple_text.getlength("...")
            linha2_conteudo = fatiar_texto(sobra, simple_text, largura_com_pontos) + "..."
        else:
            linha2_conteudo = sobra
    else: 
        linha2_conteudo = ""
    
    draw.text((x_inicio, y_linha1), username, fill=(0, 0, 0), font=bold_text)
    draw.text((x_desc_linha1, y_linha1), linha1_conteudo, fill=(0, 0, 0), font=simple_text)

    if linha2_conteudo:
        draw.text((x_inicio, y_linha2), linha2_conteudo, fill=(0, 0, 0), font=simple_text)

    path = os.path.join("Edit", f"final_{post_id}.jpg")
    canvas.save(path, quality=95)
    return path

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