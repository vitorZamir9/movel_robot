import time
import cv2
import torch
import serial
import numpy as np
from ultralytics import YOLO
import os

# ============ CONFIGURAÇÃO RADICAL ============
cv2.setNumThreads(0)
torch.set_num_threads(1)

# Configuração serial
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# ============ MODELO OTIMIZADO ============
model_path = "programacao_rasp4/modelo/ball_detect_s.pt"
yolo_ball = YOLO(model_path)
yolo_ball.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
yolo_ball.fuse()
yolo_ball.conf = 0.75
yolo_ball.iou = 0.45
tamanho = 42 # quanto maior for positivamente menor vai ser o meio ,E, quanto menor positivamente maior vai ser o meio

# ============ VARIÁVEIS ============
camera_ativa = False
cap = None
last_detection = {"time": 0, "side": None}

# ============ CÂMERA ============
def setup_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap

# ============ LOOP PRINCIPAL ============
print("sistema pronto! esperando sinal do Ev3 :>")

try:
    while True:
        # Leitura serial
        cmd = ""
        if ser.in_waiting > 0:
            try:
                cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip()
            except serial.SerialException:
                cmd = ""

        if "Resgate_ON" in cmd and not camera_ativa:
            cap = setup_camera()
            camera_ativa = cap.isOpened()
            print("Câmera ativada!" if camera_ativa else "Erro na câmera!")
        elif "OFF" in cmd and camera_ativa:
            cap.release()
            camera_ativa = False
            print("Câmera desligada.")

        # Pipeline
        if camera_ativa:
            start_time = time.time()
            cap.grab()
            ret, frame = cap.retrieve()

            if ret:
                # ---------------- YOLO BALL ----------------
                results = yolo_ball(frame, 
                                    imgsz=160,
                                    device='cpu',
                                    half=False,
                                    verbose=False,
                                    conf=0.75)[0]

                if results.boxes:
                    box = results.boxes[0]
                    conf = box.conf.item()
                    if conf > 0.75:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        center_x = (x1 + x2) // 2
                        side = "esquerda" if center_x < ((67) + tamanho) else "direita" if center_x > ((253) - tamanho) else "meio"

                        # Área do retângulo em pixels
                        area = (x2 - x1) * (y2 - y1)

                        if side != last_detection["side"] or (time.time() - last_detection["time"]) > 0.3:
                            msg = (
                                f"Detected: {yolo_ball.names[int(box.cls.item())]}\n"
                                f"Confianca: {conf*100:.1f}%\n"
                                f"Lado: {side}\n"
                                f"Area: {area} px\n"
                            )
                            ser.write(msg.encode())
                            last_detection = {"time": time.time(), "side": side}
                            print(f"Enviado: {msg.strip()} | Latência: {(time.time()-start_time)*1000:.1f}ms")

                # ---------------- RETÂNGULOS VERDE/VERMELHO ----------------
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Máscaras vermelho
                lower_red1 = np.array([0, 120, 70])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 120, 70])
                upper_red2 = np.array([180, 255, 255])
                mask_red = cv2.bitwise_or(
                    cv2.inRange(hsv, lower_red1, upper_red1),
                    cv2.inRange(hsv, lower_red2, upper_red2)
                )

                # Máscara verde
                lower_green = np.array([20, 100, 70])
                upper_green = np.array([195, 255, 255])
                mask_green = cv2.inRange(hsv, lower_green, upper_green)

                mask_total = cv2.bitwise_or(mask_red, mask_green)

                contours, _ = cv2.findContours(mask_total, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4 and cv2.contourArea(approx) > 1500:
                        x, y, w, h = cv2.boundingRect(approx)

                        red_pixels = cv2.countNonZero(mask_red[y:y+h, x:x+w])
                        green_pixels = cv2.countNonZero(mask_green[y:y+h, x:x+w])

                        # Calcula centro do retângulo
                        center_x = x + w // 2  

                        # Usa a mesma lógica do YOLO BALL
                        side = "esquerda" if center_x < ((67) + tamanho) else "direita" if center_x > ((253) - tamanho) else "meio"

                        # Códigos ANSI
                        RED = "\033[91m"
                        GREEN = "\033[92m"
                        RESET = "\033[0m"

                        if red_pixels > green_pixels:
                            msg = f"Retangulo Vermelho | Lado: {side}\n"
                            ser.write(msg.encode())
                            print(RED + "Detectado: " + msg.strip() + RESET)

                        elif green_pixels > red_pixels:
                            msg = f"Retangulo Verde | Lado: {side}\n"
                            ser.write(msg.encode())
                            print(GREEN + "Detectado: " + msg.strip() + RESET)

                # ---------------- DEBUG ----------------
                fps = 1 / (time.time() - start_time)
                print(f"FPS: {fps:.1f}")

except KeyboardInterrupt:
    print("\nDesligando sistema...")
finally:
    if cap: cap.release()
    ser.close()
