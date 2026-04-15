import time
import cv2
import serial
import os
import numpy as np 

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)

# Configuração serial
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
except Exception as e:
    print(f"AVISO: Serial não conectada! Erro: {e}")
    ser = None

# ============ CALIBRAÇÃO DE CORES (HSV) ============
GREEN_MIN = np.array([40, 50, 45])
GREEN_MAX = np.array([85, 255, 255])
BLACK_MAX = np.array([180, 255, 60]) 

# ============ SISTEMA DE DEBUG ============
DEBUG_DIR = "debug_visao"
os.makedirs(DEBUG_DIR, exist_ok=True) # Cria a pasta se não existir
print(f"[*] Pasta de imagens garantida: ./{DEBUG_DIR}/")

def salvar_debug(frame, mask_black, mask_green, contador):
    # Salva as imagens para você analisar depois no PC
    cv2.imwrite(f"{DEBUG_DIR}/frame_{contador}_original.jpg", frame)
    cv2.imwrite(f"{DEBUG_DIR}/frame_{contador}_linha.jpg", mask_black)
    cv2.imwrite(f"{DEBUG_DIR}/frame_{contador}_verde.jpg", mask_green)
    print(f"    [+] FOTO SALVA! Verifique a pasta {DEBUG_DIR}")

# ============ CÂMERA TURBO ============
def setup_camera():
    print("[*] Iniciando aquecimento da câmera...")
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    time.sleep(1) # Dá tempo pro sensor regular a luz
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

    greens_validos = sorted(greens_validos, key=lambda g: g[0])

    # 3. LÓGICA DE DECISÃO DAS STRINGS
    if len(greens_validos) >= 2:
        comando_curva = "2 verdes depois da linha preta" if tem_gap else "2 verdes"

    elif len(greens_validos) == 1:
        gx, gy, gw, gh = greens_validos[0]
        cx_verde = gx + (gw // 2) 
        
        if cx_verde < 160: 
            comando_curva = "1 verde depois da linha preta lado esquerdo" if tem_gap else "1 verde a esquerda"
        else:
            comando_curva = "1 verde depois da linha preta lado direito" if tem_gap else "1 verde a direita"

    # 4. CÁLCULO DO PID
    momentos_linha = cv2.moments(mask_black)
    if momentos_linha["m00"] > 0:
        cx_linha = int(momentos_linha["m10"] / momentos_linha["m00"])
        erro_linha = cx_linha - 160 
        status_linha = "ACHOU LINHA"
    else:
        erro_linha = 0 
        status_linha = "PERDIDO (GAP?)"

    return comando_curva, erro_linha, status_linha, mask_black, mask_green


# ============ LOOP PRINCIPAL ============
print("==================================================")
print(" SISTEMA DE VISÃO INTERATIVO ATIVADO (MODO DEBUG) ")
print("==================================================")

cap = setup_camera()
if not cap.isOpened():
    print("ERRO CRÍTICO: Câmera não encontrada!")
    exit()

print("[*] Câmera OK! Iniciando loop de leitura...")

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
            
            # Processa a imagem
            comando_verde, erro_pid, status_linha, mask_black, mask_green = processar_linha_e_verdes(frame)
            
            # Calcula FPS
            process_time = time.time() - start_time
            fps = 1 / process_time if process_time > 0 else 0
            
            # ---- TERMINAL INTERATIVO ----
            print(f"Frame: {contador_frames:04d} | FPS: {fps:04.1f} | Linha: {status_linha:<14} | PID: {erro_pid:4d} | Visão: {comando_verde}")
            
            # ---- SALVAR FOTOS DE DEBUG ----
            # Salva 1 vez a cada 30 frames
            if contador_frames % 30 == 0:
                salvar_debug(frame, mask_black, mask_green, contador_frames)

            # ---- ENVIO SERIAL ----
            if comando_verde != "frente" and ser is not None:
                # Trava de 1.5s
                if comando_verde != last_cmd_sent or (time.time() - last_cmd_time) > 1.5:
                    msg = f"{comando_verde}\n"
                    ser.write(msg.encode())
                    last_cmd_time = time.time()
                    last_cmd_sent = comando_verde
                    print(f"    [>] ENVIADO SERIAL: {msg.strip()}")

except KeyboardInterrupt:
    print("\n[*] Loop interrompido pelo usuário (Ctrl+C).")
finally:
    print("[*] Desligando hardware...")
    if cap: cap.release()
    if ser is not None and ser.is_open: ser.close()
    print("[*] Fim do programa.")
