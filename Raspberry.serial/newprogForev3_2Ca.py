import time
import cv2
import torch
import serial
from ultralytics import YOLO
import os
import numpy as np
import math
import logging
from picamera2 import Picamera2

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)
torch.set_num_threads(1)  
os.environ["LIBCAMERA_LOG_LEVELS"] = "1"
Picamera2.set_logging(logging.ERROR)

# ============ CONFIGURAÇÃO SERIAL ============
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
except Exception as e:
    print(f"AVISO: Serial não conectada! Erro: {e}")
    ser = None

# ============ SISTEMA DE GRAVAÇÃO (DVR) ============
DEBUG_DIR = "debug_videos"
os.makedirs(DEBUG_DIR, exist_ok=True)
gravador_atual = None  

# ============ MODELOS YOLO (RESGATE) ============
print("[*] Carregando I.A. de Resgate...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Modelo Bolas (O Triângulo foi substituído por geometria vetorial OpenCV)
yolo_ball = YOLO("programacao_rasp4/modelo/ball_detect_s.pt")
yolo_ball.to(device)
yolo_ball.fuse()
yolo_ball.conf = 0.55  
yolo_ball.iou = 0.45   

# ============ CONSTANTES DA LINHA ============
W, H = 320, 240
CENTRO_X = W // 2
BASE_Y = H

GREEN_MIN = np.array([35, 40, 40])
GREEN_MAX = np.array([90, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ VARIÁVEIS DE CONTROLE ============
last_detection = {"time": 0, "side": None, "cmd": None} 
picam2 = None  
cap_usb = None 

# ============ GERENCIADORES DE CÂMERA E VÍDEO ============
def iniciar_imx500():
    global picam2, gravador_atual
    if picam2 is None:
        print("\n[*] LIGANDO IMX500 (Linha OBR)...")
        picam2 = Picamera2()
        config = picam2.create_video_configuration(main={"format": "BGR888", "size": (W, H)})
        picam2.configure(config)
        picam2.start()
        
        nome_video = time.strftime("%Y%m%d_%H%M%S")
        caminho = f"{DEBUG_DIR}/camera_imx500_linha_{nome_video}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_atual = cv2.VideoWriter(caminho, fourcc, 20.0, (W, H))
        time.sleep(1)

def parar_imx500():
    global picam2, gravador_atual
    if picam2 is not None:
        print("\n[*] DESLIGANDO IMX500 e salvando vídeo...")
        picam2.stop()
        picam2.close()
        picam2 = None
        if gravador_atual:
            gravador_atual.release()
            gravador_atual = None

def iniciar_imx179():
    global cap_usb, gravador_atual
    if cap_usb is None:
        print("\n[*] LIGANDO IMX179 USB (Resgate/YOLO)...")
        cap_usb = cv2.VideoCapture(0, cv2.CAP_V4L2) 
        cap_usb.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap_usb.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        cap_usb.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        cap_usb.set(cv2.CAP_PROP_FPS, 20)
        cap_usb.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Lê a resolução real que o hardware aceitou para o DVR não falhar
        real_w = int(cap_usb.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(cap_usb.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[*] Resolução real da USB travada em: {real_w}x{real_h}")
        
        nome_video = time.strftime("%Y%m%d_%H%M%S")
        caminho = f"{DEBUG_DIR}/camera_imx179_resgate_{nome_video}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_atual = cv2.VideoWriter(caminho, fourcc, 20.0, (real_w, real_h))
        time.sleep(1)

def parar_imx179():
    global cap_usb, gravador_atual
    if cap_usb is not None:
        print("\n[*] DESLIGANDO IMX179 USB e salvando vídeo...")
        cap_usb.release()
        cap_usb = None
        if gravador_atual:
            gravador_atual.release()
            gravador_atual = None

# ============ LÓGICA VETORIAL DE LINHA ============
# ============ LÓGICA VETORIAL DE LINHA ============
def processar_linha_vetorial(frame):
    hud = frame.copy()
    
    frame_suave = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame_suave, cv2.COLOR_BGR2HSV)
    
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)

    kernel_clean = np.ones((5, 5), np.uint8)
    mask_black = cv2.morphologyEx(mask_black, cv2.MORPH_OPEN, kernel_clean)

    kernel_dilate = np.ones((15, 15), np.uint8)
    mask_black_dilated = cv2.dilate(mask_black, kernel_dilate, iterations=1)

    comando_serial = "frente"
    alvo_x, alvo_y = CENTRO_X, BASE_Y // 2

    contours_blk, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours_blk:
        maior_linha = max(contours_blk, key=cv2.contourArea)
        if cv2.contourArea(maior_linha) > 1500: 
            cv2.drawContours(hud, [maior_linha], -1, (255, 0, 0), 2)
            M = cv2.moments(maior_linha)
            if M["m00"] > 0:
                alvo_x = int(M["m10"] / M["m00"])
                alvo_y = int(M["m01"] / M["m00"])

    contours_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_brutos = []
    
    for cnt in contours_grn:
        if cv2.contourArea(cnt) > 200:  # Abaixei para 200 para garantir que pega verdes menores!
            x, y, w, h = cv2.boundingRect(cnt)
            if 0.5 <= float(w)/h <= 2.0:
                mask_this_green = np.zeros_like(mask_green)
                cv2.drawContours(mask_this_green, [cnt], -1, 255, -1)
                if cv2.countNonZero(cv2.bitwise_and(mask_black_dilated, mask_this_green)) > 0:
                    greens_brutos.append((x, y, w, h))
                    cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 0), 2)

    greens_validos = []
    if greens_brutos:
        greens_brutos = sorted(greens_brutos, key=lambda g: g[1], reverse=True)
        y_mais_proximo = greens_brutos[0][1]
        for g in greens_brutos:
            if abs(g[1] - y_mais_proximo) < 40:
                greens_validos.append(g)
        greens_validos = sorted(greens_validos, key=lambda g: g[0])

    # ==========================================================
    # NOVA ÁRVORE DE DECISÃO GEOMÉTRICA (ANTES vs DEPOIS)
    # ==========================================================
    if len(greens_validos) >= 1:
        # 1. Acha a altura exata do verde (meio do quadrado)
        cy_verde_media = sum([g[1] + (g[3] // 2) for g in greens_validos]) / len(greens_validos)
        
        # 2. A MÁGICA: Se a altura do verde for menor que o ponto vermelho da linha preta (alvo_y), 
        # significa que ele está "mais pra cima" na tela (DEPOIS da linha)!
        # Margem de -10 pixels para evitar falsos positivos se estiver exatamente alinhado.
        verde_depois = cy_verde_media < (alvo_y - 10)
        
        if verde_depois:
            comando_serial = "pelo menos 1 verde depois da linha preta"
        else:
            if len(greens_validos) >= 2:
                comando_serial = "dois verdes antes da linha preta"
            else:
                gx, gy, gw, gh = greens_validos[0]
                cx_verde = gx + (gw // 2)
                
                if cx_verde < alvo_x: 
                    comando_serial = "1 verde esquerda antes da linha preta"
                else: 
                    comando_serial = "1 verde direita antes da linha preta"
    else:
        comando_serial = "frente"
    # ==========================================================

    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    cv2.putText(hud, f"CMD: {comando_serial}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return comando_serial, hud

# ============ ESTADO INICIAL (FALLBACK) ============
print("\n[+] SISTEMA DUAL-CAMERA (COM DVR) PRONTO [+]")
modo_atual = "linha"
iniciar_imx500()

try:
    while True:
        # 1. ESCUTAR O EV3
        if ser and ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip()
            
            if "linha" in cmd.lower() and modo_atual != "linha":
                parar_imx179()
                iniciar_imx500()
                modo_atual = "linha"
                
            elif ("bolas" in cmd.lower() or "resgate_on" in cmd.lower()) and modo_atual != "bolas":
                parar_imx500()
                iniciar_imx179()
                modo_atual = "bolas"
                
            elif "triangulo" in cmd.lower() and modo_atual != "triangulo":
                parar_imx500()
                iniciar_imx179()
                modo_atual = "triangulo"

        # 2. PROCESSAMENTO
        start_time = time.time()
        msg_serial = None

        # ---- LÓGICA DA LINHA (IMX500) ----
        if modo_atual == "linha" and picam2 is not None:
            frame = picam2.capture_array("main")
            
            # IMX500 invertida 180 graus fisicamente
            frame = cv2.flip(frame, -1) 
            
            comando_verde, hud_frame = processar_linha_vetorial(frame)
            
            if gravador_atual:
                gravador_atual.write(hud_frame)
            
            if comando_verde != "frente":
                if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                    msg_serial = f"{comando_verde}\n"
                    last_detection = {"time": time.time(), "side": None, "cmd": comando_verde}

        # ---- LÓGICA DE RESGATE/YOLO (IMX179) ----
        elif modo_atual in ["bolas", "triangulo"] and cap_usb is not None:
            cap_usb.grab()
            ret, frame = cap_usb.retrieve()
            
            if ret:
                hud_frame = frame.copy() # Sem inversão, câmera USB tá normal
                
                # --- DETECÇÃO DE BOLAS (YOLO) ---
                if modo_atual == "bolas":
                    results = yolo_ball(frame, imgsz=160, device='cpu', half=False, verbose=False, conf=0.80)[0]
                    
                    if results.boxes:
                        box = results.boxes[0] 
                        conf = box.conf.item()
                        
                        if conf > 0.90:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            
                            # --- CÁLCULO DE ÁREA DE PIXELS DA VÍTIMA ---
                            largura = x2 - x1
                            altura = y2 - y1
                            area_pixels = largura * altura
                            
                            center_x = x1 + (largura // 2)
                            side = "esquerda" if center_x < 53 else "direita" if center_x > 106 else "meio" 
                            
                            classe = yolo_ball.names[int(box.cls.item())]
                            
                            cv2.rectangle(hud_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(hud_frame, f"{classe} {side} ({area_pixels}px)", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                            
                            if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                                msg_serial = f"Detectado: {classe}\nArea: {area_pixels}px\nLado: {side}\n"
                                last_detection = {"time": time.time(), "side": side, "cmd": None}

                # --- GEOMETRIA DOS TRIÂNGULOS (OPENCV PURO) ---
                elif modo_atual == "triangulo":
                    hsv_resgate = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    
                    # Máscaras de cores exatas (Vermelho tem 2 faixas no HSV)
                    mask_red1 = cv2.inRange(hsv_resgate, np.array([0, 120, 70]), np.array([10, 255, 255]))
                    mask_red2 = cv2.inRange(hsv_resgate, np.array([170, 120, 70]), np.array([180, 255, 255]))
                    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
                    mask_green_resg = cv2.inRange(hsv_resgate, GREEN_MIN, GREEN_MAX)
                    
                    mask_areas = cv2.bitwise_or(mask_red, mask_green_resg)
                    contours, _ = cv2.findContours(mask_areas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    for cnt in contours:
                        if cv2.contourArea(cnt) > 800:
                            x, y, w, h = cv2.boundingRect(cnt)
                            if h > 0:
                                proporcao = float(w) / h
                                
                                # Verifica se a mancha bate com a proporção geométrica 6:1 (36x6cm)
                                if 4.5 <= proporcao <= 7.5:
                                    centro_x = x + (w // 2)
                                    cor_nome = "Vermelho" if mask_red[y+(h//2), centro_x] > 0 else "Verde"
                                    
                                    side = "esquerda" if centro_x < 53 else "direita" if centro_x > 106 else "meio"
                                    
                                    cv2.rectangle(hud_frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                                    cv2.circle(hud_frame, (centro_x, y + (h//2)), 5, (255, 0, 0), -1)
                                    cv2.putText(hud_frame, f"Area {cor_nome} {side}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                                    
                                    if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                                        msg_serial = f"Area: {cor_nome}\nCentro: {centro_x}\nLado: {side}\n"
                                        last_detection = {"time": time.time(), "side": side, "cmd": None}

                if gravador_atual:
                    gravador_atual.write(hud_frame)

        # 3. ENVIO SERIAL
        if msg_serial and ser is not None:
            ser.write(msg_serial.encode())
            print(f" [EV3] <- {msg_serial.strip()} | FPS: {1/(time.time()-start_time):.1f}")

except KeyboardInterrupt:
    print("\n[*] Encerrando sistema de visão...")
finally:
    parar_imx500()
    parar_imx179()
    if ser is not None and ser.is_open: ser.close()
