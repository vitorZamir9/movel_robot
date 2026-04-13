import time
import cv2
import torch
import serial
from ultralytics import YOLO
import os
import numpy as np 

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)
torch.set_num_threads(1)  # Limita threads do PyTorch

# Configuração serial ultrarrápida
ser = serial.Serial('/dev/serial0', 115200, timeout=1)  # Baudrate aumentado

# ============ MODELOS OTIMIZADOS AO EXTREMO ============
model_path = "programacao_rasp4/modelo/ball_detect_s.pt"
yolo_ball = YOLO(model_path)
yolo_triangulo = YOLO("programacao_rasp4/modelo/Triangulo_detect.pth")
yolo_ball.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
yolo_triangulo.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
yolo_ball.fuse()
yolo_triangulo.fuse()
yolo_ball.conf = 0.55
yolo_ball.iou = 0.45
yolo_triangulo.conf = 0.55
yolo_triangulo.iou = 0.45

# ============ CALIBRAÇÃO DE CORES (LINHA E VERDE) ============
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ VARIÁVEIS DE CONTROLE ============
camera_ativa = False
cap = None
last_detection = {"time": 0, "side": None, "cmd": None} 
modo_atual = "bolas" 

# ============ CÂMERA TURBO ============
def setup_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap

# ============ LÓGICA DE LINHA E VERDES ============
def processar_linha_e_verdes(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)

    # 1. VERIFICAR GAP (Depois da linha preta)
    # Analisamos os últimos 40 pixels da base da imagem (o chão logo à frente do robô)
    roi_base = mask_black[200:240, :]
    # Se a média de pixels for muito baixa (< 15), significa que a linha preta sumiu ali
    tem_gap = np.mean(roi_base) < 15 

    # 2. ACHAR OS VERDES
    contours_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_validos = []
    comando_curva = "frente"

    for cnt in contours_grn:
        area = cv2.contourArea(cnt)
        if area > 400:  
            x, y, w, h = cv2.boundingRect(cnt)
            greens_validos.append((x, y, w, h))

    # Ordenar os verdes do eixo X (garante que sabemos quem está na esquerda/direita)
    greens_validos = sorted(greens_validos, key=lambda g: g[0])

    # 3. LÓGICA DE DECISÃO DAS STRINGS
    if len(greens_validos) >= 2:
        if tem_gap:
            comando_curva = "2 verdes depois da linha preta"
        else:
            comando_curva = "2 verdes"

    elif len(greens_validos) == 1:
        gx, gy, gw, gh = greens_validos[0]
        cx_verde = gx + (gw // 2) # Pega o centro do verde
        
        # Como a tela tem 320 de largura, o centro é 160.
        # Isso define fisicamente de qual lado da pista o verde está.
        if cx_verde < 160: 
            # Está na metade esquerda da câmera
            if tem_gap:
                comando_curva = "1 verde depois da linha preta lado esquerdo"
            else:
                comando_curva = "1 verde a esquerda"
        else:
            # Está na metade direita da câmera
            if tem_gap:
                comando_curva = "1 verde depois da linha preta lado direito"
            else:
                comando_curva = "1 verde a direita"

    # 4. CÁLCULO DO PID (Para a linha preta, se quiser usar)
    momentos_linha = cv2.moments(mask_black)
    if momentos_linha["m00"] > 0:
        cx_linha = int(momentos_linha["m10"] / momentos_linha["m00"])
        erro_linha = cx_linha - 160 
    else:
        erro_linha = 0 

    return comando_curva, erro_linha


# ============ LOOP PRINCIPAL OTIMIZADO ============
print("Sistema pronto - Aguardando ativação...")

try:
    while True:
        # Leitura serial não-bloqueante ultrarrápida
        if ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip()
            
            if "Resgate_ON" in cmd and not camera_ativa:
                cap = setup_camera()
                camera_ativa = cap.isOpened()
                modo_atual = "bolas"
                print("Câmera ativada!" if camera_ativa else "Erro na câmera!")
            elif "OFF" in cmd and camera_ativa:
                cap.release()
                camera_ativa = False
            
            # Controle de Modos pela Serial
            elif "triangulo" in cmd.lower() and camera_ativa:
                modo_atual = "triangulo"
                print("Modo TRIÂNGULO ativado")
            elif "linha" in cmd.lower() and camera_ativa:
                modo_atual = "linha"
                print("Modo LINHA E VERDES ativado")
            elif "bolas" in cmd.lower() and camera_ativa:
                modo_atual = "bolas"
                print("Modo BOLAS ativado")

        # Pipeline de detecção turbo
        if camera_ativa:
            start_time = time.time()
            
            cap.grab()
            ret, frame = cap.retrieve()
            
            if ret:
                if modo_atual == "triangulo":
                    results = yolo_triangulo(frame, imgsz=160, device='cpu', half=False, verbose=False, conf=0.90)[0]
                    if results.boxes:
                        box = results.boxes[0]
                        conf = box.conf.item()
                        if conf > 0.90:
                            class_name = yolo_triangulo.names[int(box.cls.item())]
                            msg = f"Triangulo: {class_name}\nConfiança: {conf*100:.1f}%\n"
                            ser.write(msg.encode())
                            last_detection["time"] = time.time()

                elif modo_atual == "bolas":
                    results = yolo_ball(frame, imgsz=160, device='cpu', half=False, verbose=False, conf=0.80)[0]
                    if results.boxes:
                        box = results.boxes[0]
                        conf = box.conf.item()
                        if conf > 0.90:
                            x1, _, x2, _ = map(int, box.xyxy[0].tolist())
                            center_x = (x1 + x2) // 2
                            side = "esquerda" if center_x < 107 else "direita" if center_x > 213 else "meio"
                            
                            if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                                msg = f"Detected: {yolo_ball.names[int(box.cls.item())]}\nConf: {conf*100:.1f}%\nLado: {side}\n"
                                ser.write(msg.encode())
                                last_detection = {"time": time.time(), "side": side, "cmd": None}

                elif modo_atual == "linha":
                    comando_verde, erro_pid = processar_linha_e_verdes(frame)
                    
                    if comando_verde != "frente":
                        # Trava de 1.5s para ele não enviar a mesma curva 30 vezes seguidas para o EV3
                        if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                            # Monta a mensagem exatamente como você pediu
                            msg = f"{comando_verde}\n"
                            ser.write(msg.encode())
                            
                            last_detection = {"time": time.time(), "side": None, "cmd": comando_verde}
                            print(f"Enviado para EV3: {msg.strip()}")

                fps = 1 / (time.time() - start_time)
                if fps < 5:
                    print(f"ALERTA: FPS {fps:.1f} - CPU sobrecarregada!")

except KeyboardInterrupt:
    print("\nDesligando sistema...")
finally:
    if cap: cap.release()
    ser.close()
