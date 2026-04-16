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
W, H = 320, 240
CENTRO_X = W // 2
BASE_Y = H

# HSV (Ajuste fino na arena)
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ SISTEMA DE GRAVAÇÃO (DVR) ============
DEBUG_DIR = "debug_videos"
os.makedirs(DEBUG_DIR, exist_ok=True)
print(f"[*] Pasta de vídeos criada: ./{DEBUG_DIR}/")

# Cria um nome único baseado na hora exata para não apagar vídeos antigos
nome_video = time.strftime("%Y%m%d_%H%M%S")
caminho_video = f"{DEBUG_DIR}/gravacao_{nome_video}.avi"

# Configura o gravador (Codec XVID é leve e roda bem na Raspberry)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
gravador = cv2.VideoWriter(caminho_video, fourcc, 20.0, (W, H))
print(f"[*] Gravando vídeo em: {caminho_video}")

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

# ============ PROCESSAMENTO VETORIAL E REGRAS OBR ============
def processar_linha_vetorial(frame):
    hud = frame.copy()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)

    kernel_dilate = np.ones((15, 15), np.uint8)
    mask_black_dilated = cv2.dilate(mask_black, kernel_dilate, iterations=1)

    estado = "PERDIDO"
    comando_serial = "frente"
    erro_x = 0
    angulo = 0.0
    alvo_x, alvo_y = CENTRO_X, BASE_Y // 2

    # 1. ENCONTRAR A LINHA PRINCIPAL
    contours_blk, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours_blk:
        maior_linha = max(contours_blk, key=cv2.contourArea)
        if cv2.contourArea(maior_linha) > 1500: 
            estado = "LINE"
            cv2.drawContours(hud, [maior_linha], -1, (255, 0, 0), 2)
            
            M = cv2.moments(maior_linha)
            if M["m00"] > 0:
                alvo_x = int(M["m10"] / M["m00"])
                alvo_y = int(M["m01"] / M["m00"])
                
                dx = alvo_x - CENTRO_X
                dy = BASE_Y - alvo_y 
                erro_x = dx
                angulo = math.degrees(math.atan2(dx, dy))

    # 2. ENCONTRAR OS VERDES E VALIDAR (REGRAS OBR)
    contours_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_brutos = []
    
    for cnt in contours_grn:
        if cv2.contourArea(cnt) > 400:  
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            
            if 0.5 <= aspect_ratio <= 2.0:
                mask_this_green = np.zeros_like(mask_green)
                cv2.drawContours(mask_this_green, [cnt], -1, 255, -1)
                
                overlap = cv2.bitwise_and(mask_black_dilated, mask_this_green)
                
                if cv2.countNonZero(overlap) > 0:
                    greens_brutos.append((x, y, w, h))
                    cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(hud, "VALIDO", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                else:
                    cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(hud, "FALSO-LONGE", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            else:
                cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 165, 255), 2) 
                cv2.putText(hud, "FALSO-FORMA", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)

    greens_validos = []
    if greens_brutos:
        greens_brutos = sorted(greens_brutos, key=lambda g: g[1], reverse=True)
        y_mais_proximo = greens_brutos[0][1]
        
        for g in greens_brutos:
            if abs(g[1] - y_mais_proximo) < 40:
                greens_validos.append(g)
                
        greens_validos = sorted(greens_validos, key=lambda g: g[0])

    # 3. MÁQUINA DE ESTADOS E DECISÃO DE ROTA
    if len(greens_validos) >= 2:
        estado = "INTERSECTION_180"
        comando_serial = "2 verdes"
        
    elif len(greens_validos) == 1:
        estado = "GREEN_DETECTED"
        gx, gy, gw, gh = greens_validos[0]
        cx_verde = gx + (gw // 2)
        
        if cx_verde < alvo_x:
            comando_serial = "1 verde a esquerda"
        else:
            comando_serial = "1 verde a direita"
            
    elif estado == "PERDIDO":
        estado = "GAP_START"
        comando_serial = "frente" 

    # 4. DESENHANDO O HUD
    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    cv2.circle(hud, (alvo_x, alvo_y), 5, (255, 255, 0), -1)
    
    cv2.putText(hud, f"STATE: {estado}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
    cv2.putText(hud, f"ERR: {erro_x}px", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(hud, f"ANG: {angulo:.1f} deg", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(hud, f"CMD: {comando_serial}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return comando_serial, erro_x, angulo, hud

# ============ LOOP PRINCIPAL ============
print("[*] Iniciando Sistema de Visão OBR (Vídeo Ativado)...")
cap = setup_camera()
if not cap.isOpened():
    print("ERRO: Câmera não encontrada!")
    exit()

last_cmd_time = 0
last_cmd_sent = None

try:
    while True:
        start_time = time.time()
        
        cap.grab()
        ret, frame = cap.retrieve()
        
        if ret:
            comando_serial, erro_x, angulo, frame_hud = processar_linha_vetorial(frame)
            
            fps = 1 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
            cv2.putText(frame_hud, f"FPS: {fps:.1f}", (W - 80, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            # ==========================================
            # ESCREVE O FRAME ATUAL NO ARQUIVO DE VÍDEO
            # ==========================================
            gravador.write(frame_hud)
            
            # Print no terminal para você acompanhar a serial
            # print(f"FPS: {fps:04.1f} | ERR: {erro_x:4d} | CMD: {comando_serial:<18}")

            # Controle de disparo serial com anti-spam
            if comando_serial != "frente" and ser is not None:
                if comando_serial != last_cmd_sent or (time.time() - last_cmd_time) > 1.5:
                    msg = f"{comando_serial}\n"
                    ser.write(msg.encode())
                    last_cmd_time = time.time()
                    last_cmd_sent = comando_serial
                    print(f" [EV3] -> {msg.strip()}")

except KeyboardInterrupt:
    print("\n[*] Encerrando e salvando vídeo...")
finally:
    if cap: cap.release()
    if gravador: gravador.release() # FUNDAMENTAL PARA SALVAR O VÍDEO CORRETAMENTE
    if ser is not None and ser.is_open: ser.close()
    print(f"[*] Vídeo salvo com sucesso em: {caminho_video}")
