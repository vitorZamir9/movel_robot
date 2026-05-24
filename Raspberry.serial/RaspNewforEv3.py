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
import smbus2

# ============ CONFIGURAÇÃO RADICAL ============
os.environ['DISPLAY'] = ':0'
cv2.setNumThreads(0)
torch.set_num_threads(1)  
os.environ["LIBCAMERA_LOG_LEVELS"] = "1"
Picamera2.set_logging(logging.ERROR)

# ============ CONFIGURAÇÃO DO GIROSCÓPIO (MPU6050) ============
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT = 0x3B
ACCEL_YOUT = 0x3D
ACCEL_ZOUT = 0x3F
GYRO_ZOUT = 0x47

try:
    bus = smbus2.SMBus(1)
    bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)
    mpu_ativo = True
    print("\n[+] MPU6050 Conectado via I2C [+]")
except Exception as e:
    print(f"\n[AVISO] MPU6050 não encontrado! Erro: {e}")
    mpu_ativo = False

def ler_dados_mpu(registo):
    if not mpu_ativo: return 0.0
    try:
        high = bus.read_byte_data(MPU_ADDR, registo)
        low = bus.read_byte_data(MPU_ADDR, registo + 1)
        valor = ((high << 8) | low)
        if valor > 32768:
            valor = valor - 65536
        return valor
    except:
        return 0.0

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
gravador_usb = None  # <--- GRAVADOR SEPARADO PRA IMX179 NO MODO LINHA

# ============ MODELOS YOLO (RESGATE) ============
print("[*] Carregando I.A. de Resgate...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

yolo_ball = YOLO("programacao_rasp4/modelo/ball_detect_s.pt")
yolo_ball.to(device)
yolo_ball.fuse()
yolo_ball.conf = 0.55  
yolo_ball.iou = 0.45   

# ============ CONSTANTES DA LINHA ============
W, H = 320, 240
CENTRO_X = W // 2
BASE_Y = H

GREEN_MIN = np.array([40, 80, 40])
GREEN_MAX = np.array([90, 255, 255])
BLACK_MAX = np.array([180, 255, 60])

# ============ VARIÁVEIS DE CONTROLE ============
last_detection = {"time": 0, "side": None, "cmd": None}
picam2 = None  
cap_usb = None

# ============ ESTADO DO OBSTÁCULO ============
# Máquina de estados para o fluxo de detecção de obstáculo
# Estados: "idle" -> "aviso_enviado" -> "aguardando_confirmacao" -> "verificando_linha" -> "idle"
estado_obstaculo = "idle"
ultimo_aviso_obstaculo = 0.0
COOLDOWN_OBSTACULO = 3.0  # segundos de espera após um ciclo completo

# ============ PARÂMETROS DE DETECÇÃO DE OBSTÁCULO ============
# A câmera IMX179 trabalha a 160x120
# Um retângulo de 15x40cm ocupa uma área significativa na imagem quando colado na câmera
# Vamos buscar por uma área grande de pixels ocupados no CENTRO da imagem
# Região central de busca: 60% da largura, 70% da altura (centralizado)
# Threshold de pixels ocupados: 25% da área da região central
USB_W = 160
USB_H = 120

# Região central onde o obstáculo deve aparecer (colado na câmera)
OBST_X1 = int(USB_W * 0.20)   # 20% da esquerda
OBST_X2 = int(USB_W * 0.80)   # 80% da largura
OBST_Y1 = int(USB_H * 0.10)   # 10% do topo
OBST_Y2 = int(USB_H * 0.90)   # 90% da altura
OBST_AREA = (OBST_X2 - OBST_X1) * (OBST_Y2 - OBST_Y1)

# Quantos % da região central precisam estar "ocupados" para considerar obstáculo
OBST_THRESHOLD_PERCENT = 0.30  # 30% da região central preenchida

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
        print("\n[*] DESLIGANDO IMX500...")
        picam2.stop()
        picam2.close()
        picam2 = None
        if gravador_atual:
            gravador_atual.release()
            gravador_atual = None

def iniciar_imx179():
    """Inicia a câmera USB IMX179. Usada tanto no modo linha (obstáculo)
    quanto nos modos bolas/triangulo."""
    global cap_usb, gravador_usb
    if cap_usb is None:
        print("\n[*] LIGANDO IMX179 USB...")
        cap_usb = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap_usb.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap_usb.set(cv2.CAP_PROP_FRAME_WIDTH, USB_W)
        cap_usb.set(cv2.CAP_PROP_FRAME_HEIGHT, USB_H)
        cap_usb.set(cv2.CAP_PROP_FPS, 20)
        cap_usb.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        real_w = int(cap_usb.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(cap_usb.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[*] Resolução real da USB: {real_w}x{real_h}")
        nome_video = time.strftime("%Y%m%d_%H%M%S")
        caminho = f"{DEBUG_DIR}/camera_imx179_{nome_video}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_usb = cv2.VideoWriter(caminho, fourcc, 20.0, (real_w, real_h))
        time.sleep(1)

def parar_imx179():
    global cap_usb, gravador_usb
    if cap_usb is not None:
        print("\n[*] DESLIGANDO IMX179 USB...")
        cap_usb.release()
        cap_usb = None
        if gravador_usb:
            gravador_usb.release()
            gravador_usb = None

# ============ LÓGICA VETORIAL DE LINHA (IMX500) ============
def processar_linha_vetorial(frame):
    hud = frame.copy()
    frame_suave = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame_suave, cv2.COLOR_BGR2HSV)
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), BLACK_MAX)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)

    kernel_green = np.ones((5, 5), np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel_green)
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
        area = cv2.contourArea(cnt)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            proporcao = float(w)/h
            solidez = area / (w * h)
            if 0.5 <= proporcao <= 2.0 and solidez > 0.45:
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

    if len(greens_validos) >= 1:
        cy_verde_media = sum([g[1] + (g[3] // 2) for g in greens_validos]) / len(greens_validos)
        verde_depois = cy_verde_media < (alvo_y - 10)
        if verde_depois:
            comando_serial = "verde depois"
        else:
            if len(greens_validos) >= 2:
                comando_serial = "dois verdes"
            else:
                gx, gy, gw, gh = greens_validos[0]
                cx_verde = gx + (gw // 2)
                if cx_verde < alvo_x:
                    comando_serial = "esquerda antes"
                else:
                    comando_serial = "direita antes"
    else:
        comando_serial = "frente"

    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    cv2.putText(hud, f"CMD: {comando_serial}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return comando_serial, hud

# ============ DETECÇÃO DE OBSTÁCULO (IMX179 - MODO LINHA) ============
def detectar_obstaculo(frame_usb):
    """
    Verifica se há um objeto grande (obstáculo) no centro da imagem da IMX179.
    
    Estratégia: converte para escala de cinza, aplica threshold adaptativo
    para encontrar qualquer objeto com textura/cor diferente do fundo, e verifica
    se a região central está suficientemente preenchida.
    
    Retorna True se detectar obstáculo, False caso contrário.
    """
    # Recorta só a região central de interesse
    roi = frame_usb[OBST_Y1:OBST_Y2, OBST_X1:OBST_X2]
    
    # Converte pra cinza
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Blur pra reduzir ruído
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold adaptativo: detecta qualquer objeto independente de cor
    # O fundo do chão costuma ser uniforme; o obstáculo cria uma região diferente
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 4
    )
    
    # Morfologia pra fechar buracos
    kernel = np.ones((5, 5), np.uint8)
    thresh_clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Conta pixels "ocupados"
    pixels_ocupados = cv2.countNonZero(thresh_clean)
    percentual = pixels_ocupados / OBST_AREA
    
    return percentual >= OBST_THRESHOLD_PERCENT, percentual

def verificar_linha_lados_usb(frame_usb):
    """
    Analisa se há linha preta à esquerda e/ou à direita na imagem da IMX179.
    Isso é chamado quando o obstáculo está COLADO na câmera (bem próximo),
    então a linha aparecerá nas laterais da imagem.
    
    Divide a imagem em metade esquerda e metade direita.
    Procura por pixels pretos (linha) em cada lado.
    
    Retorna uma string com o resultado: 
      "linha esquerda", "linha direita", "linha ambos", "linha nenhum"
    """
    gray = cv2.cvtColor(frame_usb, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Threshold simples para preto (linha preta no chão claro)
    # Pixels muito escuros = linha preta
    _, mask_preta = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Morfologia pra limpar ruído
    kernel = np.ones((3, 3), np.uint8)
    mask_preta = cv2.morphologyEx(mask_preta, cv2.MORPH_OPEN, kernel)
    
    # Foca só na metade inferior da imagem (onde a linha aparece)
    # Quando o obstáculo está colado, a linha fica na parte de baixo/lados
    linha_y_inicio = int(USB_H * 0.50)  # metade inferior
    
    # Metade ESQUERDA (excluindo a faixa central onde está o obstáculo)
    lado_esq = mask_preta[linha_y_inicio:, 0:int(USB_W * 0.35)]
    # Metade DIREITA
    lado_dir = mask_preta[linha_y_inicio:, int(USB_W * 0.65):]
    
    area_esq = int(USB_W * 0.35) * int(USB_H * 0.50)
    area_dir = int(USB_W * 0.35) * int(USB_H * 0.50)
    
    # Threshold: precisa de pelo menos 8% da área sendo linha preta
    THRESH_LINHA = 0.08
    
    tem_esq = (cv2.countNonZero(lado_esq) / area_esq) >= THRESH_LINHA
    tem_dir = (cv2.countNonZero(lado_dir) / area_dir) >= THRESH_LINHA
    
    if tem_esq and tem_dir:
        return "linha ambos"
    elif tem_esq:
        return "linha esquerda"
    elif tem_dir:
        return "linha direita"
    else:
        return "linha nenhum"

# ============ CALIBRAÇÃO INICIAL DO MPU6050 ============
offset_roll = 0.0
guinada_yaw = 0.0
tempo_anterior_mpu = time.time()
tempo_ultimo_print_mpu = time.time()

if mpu_ativo:
    print("\n[*] A calibrar a Rotação para começar em 0...")
    print("[!] MANTÉM O ROBÔ PARADO!")
    soma_roll = 0.0
    for _ in range(50):
        ay = ler_dados_mpu(ACCEL_YOUT) / 16384.0
        az = ler_dados_mpu(ACCEL_ZOUT) / 16384.0
        soma_roll += math.degrees(math.atan2(ay, az))
        time.sleep(0.02)
    offset_roll = soma_roll / 50.0
    print(f"[+] Calibração concluída! Offset de Rotação: {offset_roll:.2f}°\n")
    tempo_anterior_mpu = time.time()

# ============ ESTADO INICIAL ============
print("\n[+] SISTEMA DUAL-CAMERA (COM DVR) PRONTO [+]")
modo_atual = "linha"

# Inicia AMBAS as câmeras no modo linha
iniciar_imx500()
iniciar_imx179()  # <--- IMX179 já inicia junto no modo linha

try:
    while True:
        # ==========================================
        # 1. PROCESSAMENTO CONTÍNUO DO GIROSCÓPIO
        # ==========================================
        if mpu_ativo:
            tempo_atual_mpu = time.time()
            dt_mpu = tempo_atual_mpu - tempo_anterior_mpu
            tempo_anterior_mpu = tempo_atual_mpu
            accel_x = ler_dados_mpu(ACCEL_XOUT) / 16384.0
            accel_y = ler_dados_mpu(ACCEL_YOUT) / 16384.0
            accel_z = ler_dados_mpu(ACCEL_ZOUT) / 16384.0
            arfagem_pitch = -math.degrees(math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)))
            rotacao_roll = math.degrees(math.atan2(accel_y, accel_z)) - offset_roll
            gyro_z = ler_dados_mpu(GYRO_ZOUT) / 131.0
            if abs(gyro_z) > 1.0:
                guinada_yaw += gyro_z * dt_mpu
            if (tempo_atual_mpu - tempo_ultimo_print_mpu) > 0.5:
                str_mpu = f"MPU_Z:{guinada_yaw:.1f}\n"
                if ser: ser.write(str_mpu.encode())
                print(f"[MPU] Roll: {rotacao_roll:.1f}° | Pitch: {arfagem_pitch:.1f}° | Yaw: {guinada_yaw:.1f}°")
                tempo_ultimo_print_mpu = tempo_atual_mpu

        # ==========================================
        # 2. ESCUTAR O EV3
        # ==========================================
        if ser and ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip().lower()
            print(f"[EV3] -> '{cmd}'")

            if "linha" in cmd and modo_atual != "linha":
                # Ao voltar pro modo linha, garante que a IMX179 está ligada
                if cap_usb is None:
                    iniciar_imx179()
                iniciar_imx500()
                modo_atual = "linha"
                estado_obstaculo = "idle"

            elif ("bolas" in cmd or "resgate_on" in cmd) and modo_atual != "bolas":
                parar_imx500()
                # IMX179 continua ligada (já estava), só muda o modo
                modo_atual = "bolas"
                estado_obstaculo = "idle"

            elif "triangulo" in cmd and modo_atual != "triangulo":
                parar_imx500()
                modo_atual = "triangulo"
                estado_obstaculo = "idle"

            # -------------------------------------------------------
            # PROTOCOLO DE OBSTÁCULO: respostas do EV3
            # -------------------------------------------------------
            elif "confirma obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                # EV3 confirmou! Agora analisamos os lados da linha
                estado_obstaculo = "verificando_linha"
                print("[OBST] EV3 confirmou obstáculo! Analisando lados da linha...")

            elif "nega obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                # EV3 negou, volta pro idle
                estado_obstaculo = "idle"
                ultimo_aviso_obstaculo = time.time()
                print("[OBST] EV3 negou obstáculo. Voltando ao normal.")

        # ==========================================
        # 3. PROCESSAMENTO DE VISÃO
        # ==========================================
        start_time = time.time()
        msg_serial = None

        # ------------------------------------------
        # MODO LINHA: IMX500 (linha/verde) + IMX179 (obstáculo)
        # ------------------------------------------
        if modo_atual == "linha":

            # --- IMX500: lógica de linha e verde (igual antes) ---
            if picam2 is not None:
                frame = picam2.capture_array("main")
                frame = cv2.flip(frame, -1)
                comando_verde, hud_frame = processar_linha_vetorial(frame)
                if gravador_atual:
                    gravador_atual.write(hud_frame)
                if comando_verde != "frente":
                    if comando_verde != last_detection["cmd"] or (time.time() - last_detection["time"]) > 1.5:
                        msg_serial = f"{comando_verde}\n"
                        last_detection = {"time": time.time(), "side": None, "cmd": comando_verde}

            # --- IMX179: lógica de obstáculo ---
            if cap_usb is not None:
                cap_usb.grab()
                ret_usb, frame_usb = cap_usb.retrieve()

                if ret_usb:
                    if gravador_usb:
                        gravador_usb.write(frame_usb)

                    agora = time.time()

                    # ---- MÁQUINA DE ESTADOS DO OBSTÁCULO ----

                    if estado_obstaculo == "idle":
                        # Só detecta se passou o cooldown
                        if (agora - ultimo_aviso_obstaculo) > COOLDOWN_OBSTACULO:
                            tem_obst, pct = detectar_obstaculo(frame_usb)
                            if tem_obst:
                                # Manda aviso pro EV3 e muda de estado
                                msg_serial = "obstaculo detectado\n"
                                estado_obstaculo = "aguardando_confirmacao"
                                print(f"[OBST] Obstáculo detectado! ({pct*100:.1f}% preenchido). Aguardando EV3...")

                    elif estado_obstaculo == "aguardando_confirmacao":
                        # Fica esperando o EV3 responder (tratado no bloco serial acima)
                        # Timeout: se o EV3 não responder em 3s, volta pro idle
                        if (agora - ultimo_aviso_obstaculo) > 5.0 and ultimo_aviso_obstaculo > 0:
                            print("[OBST] Timeout aguardando EV3. Voltando ao idle.")
                            estado_obstaculo = "idle"
                            ultimo_aviso_obstaculo = agora

                    elif estado_obstaculo == "verificando_linha":
                        # Analisa os lados e manda o resultado pro EV3
                        resultado_linha = verificar_linha_lados_usb(frame_usb)
                        msg_serial = f"{resultado_linha}\n"
                        print(f"[OBST] Resultado da linha: {resultado_linha}")
                        estado_obstaculo = "idle"
                        ultimo_aviso_obstaculo = agora  # reseta cooldown

        # ------------------------------------------
        # MODO BOLAS
        # ------------------------------------------
        elif modo_atual == "bolas" and cap_usb is not None:
            cap_usb.grab()
            ret, frame = cap_usb.retrieve()
            if ret:
                hud_frame = frame.copy()
                results = yolo_ball(frame, imgsz=160, device='cpu', half=False, verbose=False, conf=0.80)[0]
                if results.boxes:
                    box = results.boxes[0]
                    conf = box.conf.item()
                    if conf > 0.90:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
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
                if gravador_usb:
                    gravador_usb.write(hud_frame)

        # ------------------------------------------
        # MODO TRIÂNGULO
        # ------------------------------------------
        elif modo_atual == "triangulo" and cap_usb is not None:
            cap_usb.grab()
            ret, frame = cap_usb.retrieve()
            if ret:
                hud_frame = frame.copy()
                hsv_resgate = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
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
                if gravador_usb:
                    gravador_usb.write(hud_frame)

        # ==========================================
        # 4. ENVIO SERIAL
        # ==========================================
        if msg_serial and ser is not None:
            ser.write(msg_serial.encode())
            print(f"[EV3] <- '{msg_serial.strip()}' | FPS: {1/(time.time()-start_time):.1f}")

except KeyboardInterrupt:
    print("\n[*] Encerrando sistema...")
finally:
    parar_imx500()
    parar_imx179()
    if ser is not None and ser.is_open:
        ser.close()
