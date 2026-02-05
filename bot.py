import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import requests
import schedule
import time
import requests
import schedule
import time
import numpy as np
import subprocess
import cv2
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from io import BytesIO

FFMPEG_EXE = os.path.join(os.getcwd(), "ffmpeg.exe")

ACCESS_TOKEN = ""
MY_INSTAGRAM_ID = ""
TARGET_USER = ""
IMGBB_API_KEY = ""

MEDIA_DIR, LOG_DIR, AUDIO_DIR = "Media", "Log", "Audio"
LOG_FILE = os.path.join(LOG_DIR, "postados_log.txt")

for folder in [MEDIA_DIR, LOG_DIR, AUDIO_DIR]:
    os.makedirs(folder, exist_ok=True)

def get_size_str(path):
    size = os.path.getsize(path) / (1024 * 1024)
    return f"[{size:.1f}mb]"

def cut_video_30s(input_path, post_id):
    """Corta o vídeo para 30s exatos com re-encoding para precisão"""
    output_path = os.path.join(MEDIA_DIR, f"cut_{post_id}.mp4")
    comando = [
        FFMPEG_EXE, '-y', '-i', input_path, 
        '-t', '30', 
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
        '-c:a', 'aac', 
        output_path
    ]
    subprocess.run(comando, check=True, capture_output=True)
    return output_path

def extract_audio(input_path, post_id):
    """Extrai o áudio para a pasta Audio"""
    audio_path = os.path.join(AUDIO_DIR, f"audio_{post_id}.mp3")
    comando = [FFMPEG_EXE, '-y', '-i', input_path, '-vn', '-acodec', 'libmp3lame', audio_path]
    subprocess.run(comando, check=True, capture_output=True)
    return audio_path

def merge_audio_video(video_editado, audio_caminho, post_id):
    """Une áudio e vídeo cravando a duração em 30s e corrigindo o FPS"""
    output_final = os.path.join(MEDIA_DIR, f"final_com_som_{post_id}.mp4")
    print(f" -> Combinando áudio com vídeo (Sincronia Forçada 30s)...")
    
    comando = [
        FFMPEG_EXE, '-y',
        '-i', video_editado,
        '-i', audio_caminho,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_final
    ]

    try:
        subprocess.run(comando, check=True, capture_output=True)
        print(f" -> Sucesso: Vídeo final gerado {get_size_str(output_final)}")
        return output_final
    except Exception as e:
        print(f" !! Erro Crítico na mesclagem: {e}")
        return video_editado

def clean_old_media():
    now = time.time()
    for folder in [MEDIA_DIR, AUDIO_DIR]:
        for f in os.listdir(folder):
            f_path = os.path.join(folder, f)
            if os.stat(f_path).st_mtime < now - (7 * 86400):
                os.remove(f_path)

def upload_to_web(path):
    with open(path, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY, 
            "image": base64.b64encode(file.read())
        }
        res = requests.post(url, payload).json()
        if res.get('success'):
            return res['data']['url'] 
        else:
            print(f" -> ERRO ImgBB: {res.get('error', {}).get('message', 'Erro desconhecido')}")
            return None

def download_file(url, post_id, ext):
    path = os.path.join(MEDIA_DIR, f"{post_id}.{ext}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        return path
    return None

def upload_video_to_web(path, max_retries=3):
    url = "https://catbox.moe/user/api.php"
    for attempt in range(1, max_retries + 1):
        try:
            with open(path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                res = requests.post(url, data=data, files=files, timeout=180)
                
                if res.status_code == 200 and "https" in res.text:
                    return res.text.strip()
                else:
                    print(f" -> Tentativa {attempt}/{max_retries} falhou. Resposta: {res.text}")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f" -> Tentativa {attempt}/{max_retries} falhou por erro de conexão/tempo.")
        
        if attempt < max_retries:
            time.sleep(5)
            
    return None

def prepare_custom_image(media_url, post_id, caption_text):
    caption_text = caption_text.replace('\n', ' ')
    
    try:
        response = requests.get(media_url)
        original_img = Image.open(BytesIO(response.content)).convert("RGB")
        
        harmonic_color = original_img.resize((1, 1)).getpixel((0, 0))

    except Exception as e:
        print(f"Erro de processar  imagem do post: {e}")
        harmonic_color = (120, 66, 245) 

    canvas_w, canvas_h = 1080, 1920
    canvas = Image.new('RGB', (canvas_w, canvas_h), color=harmonic_color)

    draw = ImageDraw.Draw(canvas)

    try:
        bg_w, bg_h = 864, 778
        bg_img  = original_img.copy()
        bg_img = ImageOps.fit(bg_img, (bg_w, bg_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=70))
        canvas.paste(bg_img, (108, 571))

        post_img = original_img.copy()

        max_w, max_h = 864, 778
        post_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        img_w, img_h = post_img.size
        img_x = 108 + (max_w - img_w) // 2
        img_y = 571 + (max_h - img_h) // 2

        canvas.paste(post_img, (img_x, img_y))

    except Exception as e:
        print(f"Erro de processar  imagem do post: {e}")

    draw.rounded_rectangle([108, 571-108, 972, 571], radius=30,fill=(255, 255, 255))
    draw.rectangle([108, 621-108, 972, 571], fill=(255, 255, 255))

    draw.rounded_rectangle([108, 1349, 972, 1349+108], radius=30,fill=(255, 255, 255))
    draw.rectangle([108, 1349, 972, 1299+108], fill=(255, 255, 255))

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

    bold_text = ImageFont.truetype("Fonts/static/Roboto_SemiCondensed-Medium.ttf", 35)
    simple_text = ImageFont.truetype("Fonts/static/Roboto-Light.ttf", 30)

    draw.text((200, 571-108+44-8), "dragonmusic_", fill=(0, 0, 0), font=bold_text)

    username = "dragonmusic_"
    y_linha1 = 1366
    y_offset_desc = 3
    y_linha2 = y_linha1 + 35 + 12
    x_inicio = 120
    x_limite = 960

    largura_user = bold_text.getlength(username)
    x_desc_linha1 = x_inicio + largura_user + 12
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
    draw.text((x_desc_linha1, y_linha1 + y_offset_desc), linha1_conteudo, fill=(0, 0, 0), font=simple_text)

    if linha2_conteudo:
        draw.text((x_inicio, y_linha2), linha2_conteudo, fill=(0, 0, 0), font=simple_text)

    path = os.path.join("Media", f"final_{post_id}.jpg")
    canvas.save(path, quality=95)
    return path

def prepare_custom_video(video_path, post_id):
    cap = cv2.VideoCapture(video_path)
    
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f" -> Editando vídeo: {total_frames} frames detectados ({int(duration)}s)")

    ret, first_frame = cap.read()
    if not ret: return None
    avg_color_bgr = cv2.resize(first_frame, (1, 1))[0][0]
    avg_color_rgb = (int(avg_color_bgr[2]), int(avg_color_bgr[1]), int(avg_color_bgr[0]))

    output_path = os.path.join("Media", f"temp_silent_{post_id}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1080, 1920))

    scale = min(1080/w, 1920/h)
    new_w, new_h = int(w * scale), int(h * scale)
    x_offset = (1080 - new_w) // 2
    y_offset = (1920 - new_h) // 2

    bold_font = ImageFont.truetype("Fonts/static/Roboto_SemiCondensed-Medium.ttf", 50)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        pil_img = Image.new("RGB", (1080, 1920), color=avg_color_rgb)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb).resize((new_w, new_h), Image.Resampling.LANCZOS)
        pil_img.paste(frame_pil, (x_offset, y_offset))
        
        draw = ImageDraw.Draw(pil_img)
        draw.text((50, 170), "dragonmusic_", fill=(255, 255, 255), font=bold_font)

        remaining_time = max(0, duration - (count / fps))
        timestamp = f"00:{int(remaining_time):02d}"
        t_w = bold_font.getlength(timestamp)
        draw.text((1080 - 50 - t_w, 170), timestamp, fill=(255, 255, 255), font=bold_font)

        final_frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        out.write(final_frame)
        
        count += 1
        if count % 30 == 0 or count == total_frames:
            percent = int((count / total_frames) * 100)
            print(f"    [Processando] {count}/{total_frames} frames ({percent}%)", end='\r')

    print("\n -> Renderização visual concluída.")
    cap.release()
    out.release()
    print(f"\n -> Renderização visual concluída. {get_size_str(output_path)}")
    return output_path

def share_to_story(media_url, media_type, post_id, caption):
    payload = {
        'media_type': 'STORIES',
        'access_token': ACCESS_TOKEN
    }
    
    if media_type == 'VIDEO':
        print(f"\n[{post_id}] Iniciando protocolo de VÍDEO...")
        
        raw_full = download_file(media_url, post_id, "mp4")
        if not raw_full: return False
        print(f" -> Arquivo original baixado {get_size_str(raw_full)}")
        
        print(" -> Aplicando corte de 30 segundos...")
        raw_30s = cut_video_30s(raw_full, post_id)
        os.remove(raw_full) 
        print(f" -> Vídeo cortado pronto {get_size_str(raw_30s)}")

        audio_path = extract_audio(raw_30s, post_id)
        processed_video = prepare_custom_video(raw_30s, post_id)
        os.remove(raw_30s) 
        
        final_video = merge_audio_video(processed_video, audio_path, post_id)
        os.remove(processed_video) 

        print(f" -> Fazendo upload para o Catbox {get_size_str(final_video)}...")
        web_url = upload_video_to_web(final_video)

        if not web_url:
            print(" -> ERRO: Upload falhou.")
            return False
        
        print(f" -> Upload concluído: {web_url}")
        
        print(" -> Aguardando 10s para propagação de link...")
        time.sleep(10)

        payload['video_url'] = web_url

    else:
        print(f"Processando imagem {post_id} com layout personalizado...")
        local_path = prepare_custom_image(media_url, post_id, caption)

        web_url = upload_to_web(local_path)

        if not web_url: 
            print(" -> Abortando postagem da imagem por falha no upload.")
            return False
        
        payload['image_url'] = web_url

    print(f" -> Enviando comando de postagem para o Instagram...")
    print(f" -> Criando container no Instagram...")
    response = requests.post(f"https://graph.facebook.com/v18.0/{MY_INSTAGRAM_ID}/media", data=payload)
    res = response.json()
    
    if 'id' in res:
        creation_id = res['id']
        if media_type == 'VIDEO': 
            print(f" -> Vídeo em processamento (ID: {creation_id}). Aguardando 45s...")
            time.sleep(45) 
        else:
            print(f" -> Imagem em processamento (ID: {creation_id}). Aguardando 15s...")
            time.sleep(15)
        
        print(f" -> Solicitando publicação do ID {creation_id}...")
        p_res = requests.post(f"https://graph.facebook.com/v18.0/{MY_INSTAGRAM_ID}/media_publish", 
                              data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in p_res:
            return True
        else:
            print(f" !! FALHA NA PUBLICAÇÃO: {p_res}")
            return False
    else:
        print(f" !! FALHA NO CONTAINER: {res}")
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
            if m_t == 'CAROUSEL_ALBUM':
                m_u, m_t = p['children']['data'][0]['media_url'], p['children']['data'][0]['media_type']

            tentativas_max = 3
            for i in range(tentativas_max):
                print(f" -> Tentativa {i+1}/{tentativas_max} para o post {p['id']}...")
                
                if share_to_story(m_u, m_t, p['id'], p.get('caption', '')):
                    with open(LOG_FILE, "a") as f: f.write(p['id'] + "\n")
                    print(f" -> Post {p['id']} enviado com sucesso!")
                    return 
                
                if i < tentativas_max - 1:
                    print(f" !! Falha na tentativa {i+1}. Aguardando 5 minutos para tentar novamente...")
                    time.sleep(300) 
                else:
                    print(f" !! Esgotadas as {tentativas_max} tentativas para o post {p['id']}. Desistindo por hoje.")
                    return

    print("Sem posts novos ou fila processada.")

if __name__ == "__main__":
    check_and_post()
    schedule.every().tuesday.at("19:00").do(check_and_post)
    schedule.every().thursday.at("19:00").do(check_and_post)
    while True:
        schedule.run_pending()
        time.sleep(60)