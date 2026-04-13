import time
import cv2
import torch
import serial
from ultralytics import YOLO
import os
import numpy as np # IMPORTANTE: Adicionado para matrizes do OpenCV

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
# ATENÇÃO: Você precisará ajustar esses valores no dia da competição!
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
# Para o preto, geralmente olhamos o brilho (Value) baixo no HSV
BLACK_MAX = np.array([180, 255, 60]) 

# ============ VARIÁVEIS DE CONTROLE ============
camera_ativa = False
cap = None
last_detection = {"time": 0, "side": None, "cmd": None}  # Evita repetições na serial
modo_atual = "bolas"  # Pode ser: "bolas", "triangulo", "linha"

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

    # Achar contornos verdes
    contours_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    greens_validos = []
    comando_curva = "frente" # Padrão se não achar verde

    for cnt in contours_grn:
        area = cv2.contourArea(cnt)
        if area > 400:  # Tamanho mínimo do verde para resolução 320x240
            x, y, w, h = cv2.boundingRect(cnt)
            greens_validos.append((x, y, w, h))

    if len(greens_validos) >= 2:
        comando_curva = "meia_volta"
    elif len(greens_validos) == 1:
        gx, gy, gw, gh = greens_validos[0]
        
        # O "ENCAIXE": Olhar a linha preta ao redor do verde
        # Pegamos pequenas fatias (ROIs - Regions of Interest) da máscara preta
        margem = int(gw * 0.8) # 80% do tamanho do verde
        
        # Cuidado para não sair dos limites da imagem (0 a 320/240)
        roi_top = mask_black[max(0, gy-margem):gy, gx:gx+gw]
        roi_left = mask_black[gy:gy+gh, max(0, gx-margem):gx]
        roi_right = mask_black[gy:gy+gh, gx+gw:min(320, gx+gw+margem)]

        # Média de pixels pretos (se for > 50, consideramos que tem linha ali)
        tem_preto_cima = np.mean(roi_top) > 50 if roi_top.size > 0 else False
        tem_preto_esq = np.mean(roi_left) > 50 if roi_left.size > 0 else False
        tem_preto_dir = np.mean(roi_right) > 50 if roi_right.size > 0 else False

        # Lógica de curva
        if tem_preto_cima and tem_preto_esq:
            comando_curva = "direita" # A linha tá na esquerda, o marcador aponta pra direita
        elif tem_preto_cima and tem_preto_dir:
            comando_curva = "esquerda" # A linha tá na direita, o marcador aponta pra esquerda

    # Opcional: Achar o centro da linha preta para o PID
    momentos_linha = cv2.moments(mask_black)
    if momentos_linha["m00"] > 0:
        cx_linha = int(momentos_linha["m10"] / momentos_linha["m00"])
        erro_linha = cx_linha - 160 # 160 é o meio exato de 320px
    else:
        erro_linha = 0 # Perdeu a linha

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
            
            # Captura frame direto (sem buffer)
            cap.grab()
            ret, frame = cap.retrieve()
            
            if ret:
                if modo_atual == "triangulo":
                    # DETECÇÃO DE TRIÂNGULOS (YOLO)
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
                    # DETECÇÃO DE BOLAS (YOLO)
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
                    # DETECÇÃO DE LINHA E VERDES (OPENCV RÁPIDO)
                    comando_verde, erro_pid = processar_linha_e_verdes(frame)
                    
                    # Só envia mensagem de verde se achar um, para não encher o buffer do EV3
                    if comando_verde != "frente":
                        # Cooldown de 1.5s para não ler o mesmo verde mil vezes
                        if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                            msg = f"Verde: {comando_verde}\n"
                            ser.write(msg.encode())
                            last_detection = {"time": time.time(), "side": None, "cmd": comando_verde}
                            print(f"Enviado Verde: {msg.strip()}")
                    
                    # Enviar erro do PID constantemente (ajuste a string conforme seu EV3 lê)
                    # ser.write(f"PID:{erro_pid}\n".encode())

                # Monitoramento de performance
                fps = 1 / (time.time() - start_time)
                if fps < 5:  # Alterado para 5, pois OpenCV puro deve rodar bem rápido
                    print(f"ALERTA: FPS {fps:.1f} - CPU sobrecarregada!")

except KeyboardInterrupt:
    print("\nDesligando sistema...")
finally:
    if cap: cap.release()
    ser.close()