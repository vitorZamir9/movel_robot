import time
import cv2
import serial
import os
import numpy as np 

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)

# Configuração serial ultrarrápida
ser = serial.Serial('/dev/serial0', 115200, timeout=1)  # Baudrate 115200

# ============ CALIBRAÇÃO DE CORES (HSV) ============
# Ajuste conforme a iluminação da arena
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ VARIÁVEIS DE CONTROLE ============
camera_ativa = False
cap = None
last_detection = {"time": 0, "cmd": None} 

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
    roi_base = mask_black[200:240, :]
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

    # Ordenar os verdes do eixo X
    greens_validos = sorted(greens_validos, key=lambda g: g[0])

    # 3. LÓGICA DE DECISÃO DAS STRINGS
    if len(greens_validos) >= 2:
        if tem_gap:
            comando_curva = "2 verdes depois da linha preta"
        else:
            comando_curva = "2 verdes"

    elif len(greens_validos) == 1:
        gx, gy, gw, gh = greens_validos[0]
        cx_verde = gx + (gw // 2) 
        
        if cx_verde < 160: 
            if tem_gap:
                comando_curva = "1 verde depois da linha preta lado esquerdo"
            else:
                comando_curva = "1 verde a esquerda"
        else:
            if tem_gap:
                comando_curva = "1 verde depois da linha preta lado direito"
            else:
                comando_curva = "1 verde a direita"

    # 4. CÁLCULO DO PID (Para o meio da linha preta)
    momentos_linha = cv2.moments(mask_black)
    if momentos_linha["m00"] > 0:
        cx_linha = int(momentos_linha["m10"] / momentos_linha["m00"])
        erro_linha = cx_linha - 160 
    else:
        erro_linha = 0 

    return comando_curva, erro_linha


# ============ LOOP PRINCIPAL ============
print("Sistema de Linha pronto - Aguardando 'linhaON' via Serial...")

try:
    while True:
        # Leitura serial não-bloqueante
        if ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip()
            
            if "linhaON" in cmd and not camera_ativa:
                cap = setup_camera()
                camera_ativa = cap.isOpened()
                print("Câmera ativada para seguir linha!" if camera_ativa else "Erro na câmera!")
            
            elif "OFF" in cmd and camera_ativa:
                if cap: cap.release()
                camera_ativa = False
                print("Câmera desligada.")

        # Pipeline de processamento (se ativo)
        if camera_ativa:
            start_time = time.time()
            
            cap.grab()
            ret, frame = cap.retrieve()
            
            if ret:
                comando_verde, erro_pid = processar_linha_e_verdes(frame)
                
                if comando_verde != "frente":
                    # Trava de 1.5s para não enviar o mesmo verde repetidas vezes
                    if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                        msg = f"{comando_verde}\n"
                        ser.write(msg.encode())
                        last_detection = {"time": time.time(), "cmd": comando_verde}
                        print(f"Enviado para EV3: {msg.strip()}")

                # Opcional: Se quiser enviar o erro do PID também, tire o # abaixo
                # ser.write(f"PID:{erro_pid}\n".encode())

            # Monitoramento de FPS
            fps = 1 / (time.time() - start_time)
            if fps < 2:
                print(f"ALERTA: FPS baixo ({fps:.1f})")

except KeyboardInterrupt:
    print("\nDesligando sistema...")
finally:
    if cap: cap.release()
    if 'ser' in locals() and ser.is_open: ser.close()
