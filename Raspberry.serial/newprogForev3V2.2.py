import time
import cv2
import serial
import os
import numpy as np
import math

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)

# Configuração serial
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
except Exception as e:
    print(f"AVISO: Serial não conectada! Erro: {e}")
    ser = None

# ============ CONSTANTES E CORES ============
# Resolução
W, H = 320, 240
CENTRO_X = W // 2
BASE_Y = H

# HSV (Ajuste conforme a luz da arena)
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ SISTEMA DE DEBUG VISUAL ============
DEBUG_DIR = "debug_hud"
os.makedirs(DEBUG_DIR, exist_ok=True)
print(f"[*] Pasta HUD criada: ./{DEBUG_DIR}/")

# ============ CÂMERA ============
def setup_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    time.sleep(1) 
    return cap

# ============ PROCESSAMENTO VETORIAL E HUD ============
def processar_linha_vetorial(frame):
    # Faz uma cópia para desenhar o HUD sem sujar a imagem original
    hud = frame.copy()
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)

    # Variáveis padrão
    estado = "PERDIDO"
    comando_serial = "frente"
    erro_x = 0
    angulo = 0.0
    alvo_x, alvo_y = CENTRO_X, BASE_Y // 2

    # 1. ENCONTRAR A LINHA (Maior contorno preto)
    contours_blk, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours_blk:
        # Pega apenas o maior contorno (filtra sujeiras pequenas e sombras)
        maior_linha = max(contours_blk, key=cv2.contourArea)
        area_linha = cv2.contourArea(maior_linha)
        
        if area_linha > 1500: # Ignora sombras muito pequenas
            estado = "LINE"
            
            # Desenha o contorno da linha em AZUL (Igual ao vídeo)
            cv2.drawContours(hud, [maior_linha], -1, (255, 0, 0), 2)
            
            # Calcula o Centróide (Centro de Massa) da linha
            M = cv2.moments(maior_linha)
            if M["m00"] > 0:
                alvo_x = int(M["m10"] / M["m00"])
                alvo_y = int(M["m01"] / M["m00"])
                
                # Matemática Vetorial
                dx = alvo_x - CENTRO_X
                dy = BASE_Y - alvo_y # Inverte o Y porque no PC o Y cresce para baixo
                
                erro_x = dx
                # Calcula o ângulo em graus
                angulo = math.degrees(math.atan2(dx, dy))

    # 2. ENCONTRAR OS VERDES
    contours_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_validos = []
    
    for cnt in contours_grn:
        if cv2.contourArea(cnt) > 400:  
            x, y, w, h = cv2.boundingRect(cnt)
            greens_validos.append((x, y, w, h))
            # Desenha a caixa verde neon (Igual ao vídeo)
            cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(hud, "VERDE", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # 3. MÁQUINA DE ESTADOS E DECISÃO
    if len(greens_validos) >= 2:
        estado = "INTERSECTION"
        comando_serial = "2 verdes"
    elif len(greens_validos) == 1:
        estado = "GREEN_MARKER"
        gx, gy, gw, gh = greens_validos[0]
        cx_verde = gx + (gw // 2)
        
        # Decide o lado baseado no centróide da linha! 
        # Se o verde tá na esquerda da linha principal, curva pra esquerda.
        if cx_verde < alvo_x:
            comando_serial = "1 verde a esquerda"
        else:
            comando_serial = "1 verde a direita"
            
    elif estado == "PERDIDO":
        estado = "GAP_START"
        comando_serial = "frente" # Mantém reto procurando linha

    # 4. DESENHANDO O HUD (Interface de Videogame)
    # Linha Vermelha de Direção (Do centro da base até o alvo)
    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    # Círculo Ciano no Alvo
    cv2.circle(hud, (alvo_x, alvo_y), 5, (255, 255, 0), -1)
    
    # Textos na tela
    cv2.putText(hud, f"STATE: {estado}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
    cv2.putText(hud, f"ERR: {erro_x}px", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(hud, f"ANG: {angulo:.1f} deg", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(hud, f"CMD: {comando_serial}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return comando_serial, erro_x, angulo, hud

# ============ LOOP PRINCIPAL ============
print("[*] Iniciando Sistema de Visão Vetorial...")
cap = setup_camera()
if not cap.isOpened():
    print("ERRO: Câmera não encontrada!")
    exit()

contador_frames = 0
last_cmd_time = 0
last_cmd_sent = None

try:
    while True:
        start_time = time.time()
        
        cap.grab()
        ret, frame = cap.retrieve()
        
        if ret:
            contador_frames += 1
            
            # Processa e pega a imagem já com os desenhos
            comando_serial, erro_x, angulo, frame_hud = processar_linha_vetorial(frame)
            
            # FPS
            fps = 1 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
            
            # Escreve o FPS no canto da imagem
            cv2.putText(frame_hud, f"FPS: {fps:.1f}", (W - 80, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            # Salva o frame na pasta a cada 10 frames (meio segundo)
            if contador_frames % 10 == 0:
                caminho = f"{DEBUG_DIR}/hud_frame_{contador_frames:04d}.jpg"
                cv2.imwrite(caminho, frame_hud)
            
            # Print no terminal para você acompanhar
            print(f"FPS: {fps:04.1f} | ERR: {erro_x:4d} | ANG: {angulo:5.1f} | CMD: {comando_serial:<18}")

            # Envio para o EV3
            if comando_serial != "frente" and ser is not None:
                if comando_serial != last_cmd_sent or (time.time() - last_cmd_time) > 1.5:
                    msg = f"{comando_serial}\n"
                    ser.write(msg.encode())
                    last_cmd_time = time.time()
                    last_cmd_sent = comando_serial
                    print(f" [EV3] -> {msg.strip()}")

except KeyboardInterrupt:
    print("\n[*] Encerrando...")
finally:
    if cap: cap.release()
    if ser is not None and ser.is_open: ser.close()
