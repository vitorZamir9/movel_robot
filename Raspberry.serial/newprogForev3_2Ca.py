import time
import cv2
import torch
import serial
from ultralytics import YOLO
import os
import numpy as np
import math
from picamera2 import Picamera2

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)
torch.set_num_threads(1)  

os.environ["LIBCAMERA_LOG_LEVELS"] = "4"
Picamera2.set_logging(Picamera2.ERROR)

# ============ CONFIGURAÇÃO SERIAL ============
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
except Exception as e:
    print(f"AVISO: Serial não conectada! Erro: {e}")
    ser = None

# ============ SISTEMA DE GRAVAÇÃO (DVR) ============
DEBUG_DIR = "debug_videos"
os.makedirs(DEBUG_DIR, exist_ok=True)
gravador_atual = None  # Variável global para o gravador de vídeo

# ============ MODELOS YOLO (IMX179) ============
print("[*] Carregando I.A. de Resgate/Obstáculos...")
yolo_ball = YOLO("programacao_rasp4/modelo/ball_detect_s.pt")
yolo_triangulo = YOLO("programacao_rasp4/modelo/Triangulo_detect.pth")
yolo_obstaculo = YOLO("programacao_rasp4/modelo/Obstaculo_detect.pt")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
for model in [yolo_ball, yolo_triangulo, yolo_obstaculo]:
    model.to(device)
    model.fuse()

# ============ CONSTANTES ============
W, H = 320, 240
CENTRO_X = W // 2
BASE_Y = H

GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
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
        config = picam2.create_video_configuration({"main": {"format": "BGR888", "size": (W, H)}})
        picam2.configure(config)
        picam2.start()
        
        # Inicia a gravação desta câmera
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
        
        # Inicia a gravação desta câmera (resolução 160x120)
        nome_video = time.strftime("%Y%m%d_%H%M%S")
        caminho = f"{DEBUG_DIR}/camera_imx179_resgate_{nome_video}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_atual = cv2.VideoWriter(caminho, fourcc, 20.0, (160, 120))
        
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
def processar_linha_vetorial(frame):
    hud = frame.copy()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)

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
        if cv2.contourArea(cnt) > 400:  
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

    if len(greens_validos) >= 2:
        comando_serial = "2 verdes"
    elif len(greens_validos) == 1:
        cx_verde = greens_validos[0][0] + (greens_validos[0][2] // 2)
        comando_serial = "1 verde a esquerda" if cx_verde < alvo_x else "1 verde a direita"

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

            elif "obstaculo" in cmd.lower() and modo_atual != "obstaculo":
                parar_imx500()
                iniciar_imx179()
                modo_atual = "obstaculo"

        # 2. PROCESSAMENTO
        start_time = time.time()
        msg_serial = None

        # ---- LÓGICA DA LINHA (IMX500) ----
        if modo_atual == "linha" and picam2 is not None:
            frame = picam2.capture_array("main")
            comando_verde, hud_frame = processar_linha_vetorial(frame)
            
            # Escreve no vídeo da IMX500
            if gravador_atual:
                gravador_atual.write(hud_frame)
            
            if comando_verde != "frente":
                if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                    msg_serial = f"{comando_verde}\n"
                    last_detection = {"time": time.time(), "side": None, "cmd": comando_verde}

        # ---- LÓGICA DE RESGATE/YOLO (IMX179) ----
        elif modo_atual in ["bolas", "triangulo", "obstaculo"] and cap_usb is not None:
            cap_usb.grab()
            ret, frame = cap_usb.retrieve()
            
            if ret:
                hud_frame = frame.copy()
                
                if modo_atual == "bolas":
                    modelo, conf_min = yolo_ball, 0.80
                elif modo_atual == "triangulo":
                    modelo, conf_min = yolo_triangulo, 0.90
                elif modo_atual == "obstaculo":
                    modelo, conf_min = yolo_obstaculo, 0.85

                results = modelo(frame, imgsz=160, device='cpu', half=False, verbose=False, conf=conf_min)[0]
                
                if results.boxes:
                    box = results.boxes[0] 
                    conf = box.conf.item()
                    
                    if conf > conf_min:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        center_x = (x1 + x2) // 2
                        side = "esquerda" if center_x < 53 else "direita" if center_x > 106 else "meio" # Ajustado para 160px de largura
                        classe = modelo.names[int(box.cls.item())]
                        
                        # Desenha a detecção no vídeo do resgate!
                        cv2.rectangle(hud_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(hud_frame, f"{classe} {side}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                        
                        if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                            msg_serial = f"Detectado: {classe} | Lado: {side}\n"
                            last_detection = {"time": time.time(), "side": side, "cmd": None}

                # Escreve no vídeo da IMX179
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
