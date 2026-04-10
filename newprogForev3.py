import time
import cv2
import torch
import serial
from ultralytics import YOLO
import os

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)
torch.set_num_threads(1)  # Limita threads do PyTorch

# Configuração serial ultrarrápida
ser = serial.Serial('/dev/serial0', 115200, timeout=1)  # Baudrate aumentado

# ============ MODELOS OTIMIZADOS AO EXTREMO ============
model_path = "programacao_rasp4/modelo/ball_detect_s.pt"
yolo_ball = YOLO(model_path)
yolo_triangulo = YOLO("programacao_rasp4/modelo/Triangulo_detect.pth")  # Novo modelo
yolo_ball.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
yolo_triangulo.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
yolo_ball.fuse()
yolo_triangulo.fuse()
yolo_ball.conf = 0.55  # Aumente para filtrar detecções fracas
yolo_ball.iou = 0.45   # Balanceamento precisão/performance
yolo_triangulo.conf = 0.55  # Configurações similares para o modelo de triângulos
yolo_triangulo.iou = 0.45

# ============ VARIÁVEIS DE CONTROLE ============
camera_ativa = False
cap = None
last_detection = {"time": 0, "side": None}  # Evita repetições
modo_triangulo = False  # Novo flag para controle de modo

# ============ CÂMERA TURBO ============
def setup_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))  # Codec hardware
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Resolução mínima viável
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)     # Buffer mínimo absoluto
    return cap

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
                modo_triangulo = False  # Reseta para modo padrão
                print("Câmera ativada!" if camera_ativa else "Erro na câmera!")
            elif "OFF" in cmd and camera_ativa:
                cap.release()
                camera_ativa = False
            elif "triangulo" in cmd.lower() and camera_ativa:
                modo_triangulo = not modo_triangulo  # Alterna o modo
                print(f"Modo triângulo {'ativado' if modo_triangulo else 'desativado'}")

        # Pipeline de detecção turbo
        if camera_ativa:
            start_time = time.time()
            
            # Captura frame direto (sem buffer)
            cap.grab()
            ret, frame = cap.retrieve()
            
            if ret:
                if modo_triangulo:
                    # DETECÇÃO DE TRIÂNGULOS
                    results = yolo_triangulo(frame, 
                                           imgsz=160,
                                           device='cpu',
                                           half=False,
                                           verbose=False,
                                           conf=0.90)[0]
                    
                    if results.boxes:
                        box = results.boxes[0]  # Pega a melhor detecção
                        conf = box.conf.item()
                        if conf > 0.90:
                            class_name = yolo_triangulo.names[int(box.cls.item())]
                            msg = f"Triangulo: {class_name}\nConfiança: {conf*100:.1f}%\n"
                            ser.write(msg.encode())
                            last_detection = {"time": time.time(), "side": None}
                            print(f"Enviado: {msg.strip()} | Latência: {(time.time()-start_time)*1000:.1f}ms")
                else:
                    # DETECÇÃO DE BOLAS (código original)
                    results = yolo_ball(frame, 
                                      imgsz=160,
                                      device='cpu',
                                      half=False,
                                      verbose=False,
                                      conf=0.80)[0]
                    
                    if results.boxes:
                        box = results.boxes[0]  # Pega apenas a melhor detecção
                        conf = box.conf.item()
                        if conf > 0.90:
                            x1, _, x2, _ = map(int, box.xyxy[0].tolist())
                            center_x = (x1 + x2) // 2
                            side = "esquerda" if center_x < 107 else "direita" if center_x > 213 else "meio"
                            
                            if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                                msg = f"Detected: {yolo_ball.names[int(box.cls.item())]}\nConfiança: {conf*100:.1f}%\nLado: {side}\n"
                                ser.write(msg.encode())
                                last_detection = {"time": time.time(), "side": side}
                                print(f"Enviado: {msg.strip()} | Latência: {(time.time()-start_time)*1000:.1f}ms")

                # Monitoramento de performance (mantido)
                fps = 1 / (time.time() - start_time)
                if fps < 2:  # Alerta de baixo desempenho
                    print(f"ALERTA: FPS {fps:.1f} - Verifique iluminação/câmera")

except KeyboardInterrupt:
    print("\nDesligando sistema...")
finally:
    if cap: cap.release()
    ser.close()