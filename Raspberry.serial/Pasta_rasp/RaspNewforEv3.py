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
import dashboard_server as dash

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
        low  = bus.read_byte_data(MPU_ADDR, registo + 1)
        valor = (high << 8) | low
        if valor > 32768: valor -= 65536
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
gravador_usb   = None

# ============ MODELOS YOLO ============
print("[*] Carregando I.A. de Resgate...")
device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
yolo_ball = YOLO("programacao_rasp4/modelo/ball_detect_s.pt")
yolo_ball.to(device)
yolo_ball.fuse()
yolo_ball.conf = 0.55
yolo_ball.iou  = 0.45

# ============ CONSTANTES DA IMX500 ============
W, H     = 320, 240
CENTRO_X = W // 2
BASE_Y   = H

# ─── LINHA PRETA ───────────────────────────────────────────────
# Região inferior usa threshold mais permissivo (mais pixels = mais sinal)
BLACK_MIN             = np.array([0,   0,   0  ])
BLACK_MAX_TOP         = np.array([180, 255, 55 ])   # topo — mais restritivo
BLACK_MAX_BOTTOM      = np.array([180, 255, 70 ])   # base — mais permissivo

# ─── VERDE ─────────────────────────────────────────────────────
GREEN_MIN = np.array([40, 80,  40 ])
GREEN_MAX = np.array([90, 255, 255])

# ─── PRATA / CINZA ─────────────────────────────────────────────
# Fita prata reflectiva: alta luminosidade, saturação muito baixa
# Fita cinza não-reflectiva: luminosidade média-alta, saturação baixa
# Usamos BGR direto (não HSV) para prata pois HSV perde precisão em áreas brancas/cinzas
SILVER_BGR_MIN = np.array([130, 130, 130])   # cinza/prata escuro
SILVER_BGR_MAX = np.array([255, 255, 255])   # branco/prata claro
# Filtro extra no HSV para separar prata de superfícies brancas do chão:
# saturação baixa (≤ 40) e valor alto (≥ 130)
SILVER_HSV_SAT_MAX  = 50
SILVER_HSV_VAL_MIN  = 120
SILVER_MIN_AREA     = 1200   # pixels — contorno mínimo para ser prata

# ─── FITA PRETA NO MODO RESGATE ────────────────────────────────
# Igual à linha preta normal; reutilizamos as mesmas constantes
RESGATE_BLACK_MIN_AREA = 2000

# ============ CONSTANTES DA IMX179 ============
USB_W = 160
USB_H = 120

OBST_X1   = int(USB_W * 0.20)
OBST_X2   = int(USB_W * 0.80)
OBST_Y1   = int(USB_H * 0.10)
OBST_Y2   = int(USB_H * 0.90)
OBST_AREA = (OBST_X2 - OBST_X1) * (OBST_Y2 - OBST_Y1)
OBST_THRESHOLD_PERCENT = 0.30

# ============ VARIÁVEIS DE CONTROLE ============
last_detection   = {"time": 0, "side": None, "cmd": None}
last_silver_send = 0.0       # cooldown do aviso de prata
SILVER_COOLDOWN  = 1.0       # s — manda no máx 1 aviso/s
picam2   = None
cap_usb  = None

# ============ ESTADO DO OBSTÁCULO ============
estado_obstaculo       = "idle"
ultimo_aviso_obstaculo = 0.0
COOLDOWN_OBSTACULO     = 3.0

# ============ GIROSCÓPIO ============
rotacao_roll  = 0.0
arfagem_pitch = 0.0
guinada_yaw   = 0.0

# ============ PARÂMETROS AVANÇADOS DE LINHA (inspirados no segundo código) ============
# Crop dinâmico: ignora a parte superior da imagem ao calcular o contorno da linha
# para evitar que curvas à frente "puxem" o ângulo antes da hora.
LINE_CROP_RATIO   = 0.50    # usa só os 50% inferiores para calcular direção
x_last            = float(CENTRO_X)
y_last            = float(H // 2)

# ============ GERENCIADORES DE CÂMERA E VÍDEO ============
def iniciar_imx500():
    global picam2, gravador_atual
    if picam2 is None:
        print("\n[*] LIGANDO IMX500...")
        picam2 = Picamera2()
        config = picam2.create_video_configuration(
            main={"format": "BGR888", "size": (W, H)})
        picam2.configure(config)
        picam2.start()
        nome   = time.strftime("%Y%m%d_%H%M%S")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_atual = cv2.VideoWriter(
            f"{DEBUG_DIR}/imx500_{nome}.avi", fourcc, 20.0, (W, H))
        time.sleep(1)

def parar_imx500():
    global picam2, gravador_atual
    if picam2 is not None:
        print("\n[*] DESLIGANDO IMX500...")
        picam2.stop(); picam2.close(); picam2 = None
        if gravador_atual: gravador_atual.release(); gravador_atual = None

def iniciar_imx179():
    global cap_usb, gravador_usb
    if cap_usb is None:
        print("\n[*] LIGANDO IMX179 USB...")
        cap_usb = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap_usb.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        cap_usb.set(cv2.CAP_PROP_FRAME_WIDTH,  USB_W)
        cap_usb.set(cv2.CAP_PROP_FRAME_HEIGHT, USB_H)
        cap_usb.set(cv2.CAP_PROP_FPS, 20)
        cap_usb.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        rw = int(cap_usb.get(cv2.CAP_PROP_FRAME_WIDTH))
        rh = int(cap_usb.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[*] IMX179 resolução: {rw}x{rh}")
        nome   = time.strftime("%Y%m%d_%H%M%S")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_usb = cv2.VideoWriter(
            f"{DEBUG_DIR}/imx179_{nome}.avi", fourcc, 20.0, (rw, rh))
        time.sleep(1)

def parar_imx179():
    global cap_usb, gravador_usb
    if cap_usb is not None:
        print("\n[*] DESLIGANDO IMX179 USB...")
        cap_usb.release(); cap_usb = None
        if gravador_usb: gravador_usb.release(); gravador_usb = None

# ══════════════════════════════════════════════════════════════════
#  HELPERS DE VISÃO
# ══════════════════════════════════════════════════════════════════

def _mask_silver(frame_bgr):
    """
    Retorna máscara binária dos pixels que parecem prata/cinza.
    Combina:
      1. Threshold BGR (pixels claros)
      2. Threshold HSV (saturação baixa + valor alto) para separar
         prata do chão branco/amarelado ou de objetos coloridos claros.
    """
    mask_bgr = cv2.inRange(frame_bgr, SILVER_BGR_MIN, SILVER_BGR_MAX)

    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    # Saturação baixa E valor alto = cinza/prata
    mask_hsv = cv2.inRange(hsv,
        np.array([0,  0,               SILVER_HSV_VAL_MIN]),
        np.array([180, SILVER_HSV_SAT_MAX, 255]))

    # Interseção: pixel tem que passar nos dois filtros
    mask = cv2.bitwise_and(mask_bgr, mask_hsv)

    # Limpeza morfológica
    k3 = np.ones((3, 3), np.uint8)
    k7 = np.ones((7, 7), np.uint8)
    mask = cv2.erode(mask,  k3, iterations=2)
    mask = cv2.dilate(mask, k7, iterations=3)
    mask = cv2.erode(mask,  k3, iterations=1)
    return mask


def _mask_black_linha(frame_bgr):
    """
    Máscara de linha preta com calibração diferente para topo e base
    (inspirado no segundo código).
    Subtrai verde para não confundir com sombras das marcações.
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    mask_bottom = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_BOTTOM)
    mask_top    = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_TOP)

    # Região de corte: 40% superior usa threshold restritivo
    split = int(H * 0.40)
    mask_black = mask_bottom.copy()
    mask_black[0:split, :] = mask_top[0:split, :]

    # Remove verde da máscara de preto
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    mask_black = cv2.subtract(mask_black, mask_green)

    # Morfologia (valores testados no segundo código)
    k = np.ones((3, 3), np.uint8)
    mask_black = cv2.erode(mask_black,  k, iterations=5)
    mask_black = cv2.dilate(mask_black, k, iterations=17)
    mask_black = cv2.erode(mask_black,  k, iterations=9)
    return mask_black


def _encontrar_melhor_contorno(contours_blk):
    """
    Sistema de candidatos inspirado no segundo código:
    escolhe o contorno de linha mais provável baseado em:
      - posição Y mais baixa (mais próxima do robô)
      - distância ao último ponto conhecido (continuidade)
    Retorna o contorno escolhido e seu crop inferior.
    """
    global x_last, y_last

    if not contours_blk:
        return None, None

    candidatos = []
    for i, cnt in enumerate(contours_blk):
        box    = cv2.boxPoints(cv2.minAreaRect(cnt))
        box_s  = box[box[:, 1].argsort()[::-1]]   # ordena por Y decrescente
        bot_y  = box_s[0][1]
        box_xs = box[box[:, 0].argsort()]
        x_mean = (np.clip(box_xs[0][0], 0, W) + np.clip(box_xs[-1][0], 0, W)) / 2
        box_ys = box[box[:, 1].argsort()]
        y_mean = (np.clip(box_ys[0][1], 0, H) + np.clip(box_ys[-1][1], 0, H)) / 2
        dist   = abs(x_last - x_mean) + abs(y_last - y_mean)
        candidatos.append((i, bot_y, dist, x_mean, y_mean))

    # Prioriza: mais abaixo na imagem; desempate por proximidade ao último ponto
    candidatos.sort(key=lambda c: (-c[1], c[2]))
    melhor = candidatos[0]

    x_last = melhor[3]
    y_last = melhor[4]

    cnt_escolhido = contours_blk[melhor[0]]

    # Crop: mantém só a parte inferior do contorno (LINE_CROP_RATIO)
    crop_y = int(H * LINE_CROP_RATIO)
    cnt_crop = cnt_escolhido[cnt_escolhido[:, 0, 1] >= crop_y]

    return cnt_escolhido, cnt_crop if len(cnt_crop) > 0 else cnt_escolhido


def _calcular_alvo(cnt_full, cnt_crop):
    """
    Calcula o ponto-alvo (POI) para seguir a linha.
    Usa o contorno cropado para direção imediata;
    usa o topo do contorno completo para antecipar curvas.
    Retorna (alvo_x, alvo_y).
    """
    # Centroide do crop (direção imediata)
    M = cv2.moments(cnt_crop)
    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = CENTRO_X, H // 2

    # Ponto mais alto do contorno completo (antevisão)
    top_y   = int(np.min(cnt_full[:, 0, 1]))
    top_pts = cnt_full[cnt_full[:, 0, 1] == top_y]
    top_x   = int(np.mean(top_pts[:, 0, 0]))

    # Mistura 70% crop (imediato) + 30% topo (antevisão)
    alvo_x = int(cx * 0.70 + top_x * 0.30)
    alvo_y = cy
    return alvo_x, alvo_y

# ══════════════════════════════════════════════════════════════════
#  PROCESSAMENTO PRINCIPAL — MODO LINHA (IMX500)
# ══════════════════════════════════════════════════════════════════

def processar_linha_vetorial(frame):
    """
    Versão avançada com:
      - Calibração diferenciada topo/base para preto
      - Sistema de candidatos + crop dinâmico
      - Detecção de prata/cinza (entrada do resgate)
      - Detecção de verde (marcações de curva)
    Retorna (comando_serial, hud_frame, prata_detectada)
    """
    hud = frame.copy()

    # ── 1. Máscaras ──────────────────────────────────────────────
    frame_blur = cv2.GaussianBlur(frame, (5, 5), 0)

    mask_black  = _mask_black_linha(frame_blur)
    mask_silver = _mask_silver(frame_blur)
    mask_green  = cv2.inRange(
        cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV), GREEN_MIN, GREEN_MAX)

    k5 = np.ones((5, 5), np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, k5)

    # ── 2. Detecção de PRATA ──────────────────────────────────────
    prata_detectada = False
    contours_silver, _ = cv2.findContours(
        mask_silver, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours_silver:
        if cv2.contourArea(cnt) > SILVER_MIN_AREA:
            prata_detectada = True
            x, y, w, h = cv2.boundingRect(cnt)
            # HUD: retângulo prateado
            cv2.rectangle(hud, (x, y), (x+w, y+h), (200, 200, 200), 2)
            cv2.putText(hud, "PRATA", (x, y-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    # ── 3. Detecção de VERDE ──────────────────────────────────────
    k_dil = np.ones((15, 15), np.uint8)
    mask_black_dilated = cv2.dilate(mask_black, k_dil, iterations=1)

    contours_grn, _ = cv2.findContours(
        mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_brutos = []
    for cnt in contours_grn:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            prop    = float(w) / h if h > 0 else 0
            solidez = cv2.contourArea(cnt) / (w * h) if w * h > 0 else 0
            if 0.5 <= prop <= 2.0 and solidez > 0.45:
                mask_g = np.zeros_like(mask_green)
                cv2.drawContours(mask_g, [cnt], -1, 255, -1)
                if cv2.countNonZero(
                        cv2.bitwise_and(mask_black_dilated, mask_g)) > 0:
                    greens_brutos.append((x, y, w, h))
                    cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Filtra verdes válidos (mesma linha horizontal)
    greens_validos = []
    if greens_brutos:
        greens_brutos.sort(key=lambda g: g[1], reverse=True)
        y_ref = greens_brutos[0][1]
        greens_validos = [g for g in greens_brutos if abs(g[1] - y_ref) < 40]
        greens_validos.sort(key=lambda g: g[0])

    # ── 4. Linha PRETA — candidatos + crop ───────────────────────
    contours_blk, _ = cv2.findContours(
        mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # Filtra contornos pequenos (ruído)
    contours_blk = [c for c in contours_blk if cv2.contourArea(c) > 1500]

    alvo_x, alvo_y   = CENTRO_X, H // 2
    comando_serial    = "frente"

    if contours_blk:
        cnt_full, cnt_crop = _encontrar_melhor_contorno(contours_blk)
        if cnt_full is not None:
            cv2.drawContours(hud, [cnt_full], -1, (255, 0, 0), 2)
            if cnt_crop is not None and len(cnt_crop) > 0:
                cv2.drawContours(hud, [cnt_crop], -1, (255, 255, 0), 2)
            alvo_x, alvo_y = _calcular_alvo(cnt_full, cnt_crop)

    # ── 5. Árvore de decisão verde ───────────────────────────────
    if greens_validos:
        cy_verde = sum(g[1] + g[3]//2 for g in greens_validos) / len(greens_validos)
        verde_depois = cy_verde < (alvo_y - 10)
        if verde_depois:
            comando_serial = "verde depois"
        elif len(greens_validos) >= 2:
            comando_serial = "dois verdes"
        else:
            gx, gy, gw, gh = greens_validos[0]
            cx_verde = gx + gw // 2
            comando_serial = "esquerda antes" if cx_verde < alvo_x else "direita antes"

    # ── 6. HUD ───────────────────────────────────────────────────
    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    cv2.circle(hud, (alvo_x, alvo_y), 5, (0, 0, 255), -1)
    cor_cmd = (0, 255, 255) if prata_detectada else (0, 255, 0)
    cv2.putText(hud, f"CMD:{comando_serial}", (5, 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, cor_cmd, 1)
    if prata_detectada:
        cv2.putText(hud, "*** PRATA ***", (CENTRO_X - 50, H//2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    return comando_serial, hud, prata_detectada


# ══════════════════════════════════════════════════════════════════
#  MONITORAMENTO DE FITAS — MODO RESGATE (IMX500 em paralelo)
# ══════════════════════════════════════════════════════════════════

# Cooldown independente para cada tipo de fita no modo resgate
_last_send_resgate = {"prata": 0.0, "preta": 0.0}
RESGATE_COOLDOWN   = 0.8   # s — evita flood serial

def monitorar_fitas_resgate(frame):
    """
    Chamada quando o modo é 'bolas' ou 'triangulo'.
    A IMX500 analisa o frame em busca de:
      - Fita PRATA/CINZA  → entrada do resgate → manda 'prata visivel'
      - Fita PRETA        → saída  do resgate  → manda 'preta visivel'
    Retorna (msg_fita, hud_frame) onde msg_fita pode ser None.
    """
    hud  = frame.copy()
    agora = time.time()
    msg  = None

    frame_blur = cv2.GaussianBlur(frame, (5, 5), 0)

    # ── Prata ─────────────────────────────────────────────────────
    mask_silver = _mask_silver(frame_blur)
    cnts_silver, _ = cv2.findContours(
        mask_silver, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    prata_ok = False
    for cnt in cnts_silver:
        if cv2.contourArea(cnt) > SILVER_MIN_AREA:
            prata_ok = True
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(hud, (x, y), (x+w, y+h), (200, 200, 200), 2)
            cv2.putText(hud, f"ENTRADA ({cv2.contourArea(cnt):.0f}px)",
                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

    # ── Preta ─────────────────────────────────────────────────────
    mask_black = _mask_black_linha(frame_blur)
    cnts_black, _ = cv2.findContours(
        mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    preta_ok = False
    for cnt in cnts_black:
        if cv2.contourArea(cnt) > RESGATE_BLACK_MIN_AREA:
            preta_ok = True
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 0, 0), 2)
            cv2.putText(hud, f"SAIDA ({cv2.contourArea(cnt):.0f}px)",
                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (50, 50, 255), 1)

    # ── Decide o que mandar (prata tem prioridade sobre preta) ────
    if prata_ok and (agora - _last_send_resgate["prata"]) > RESGATE_COOLDOWN:
        msg = "prata visivel\n"
        _last_send_resgate["prata"] = agora
        cv2.putText(hud, ">>> ENTRADA RESGATE <<<", (5, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)

    elif preta_ok and not prata_ok and \
            (agora - _last_send_resgate["preta"]) > RESGATE_COOLDOWN:
        msg = "preta visivel\n"
        _last_send_resgate["preta"] = agora
        cv2.putText(hud, ">>> SAIDA RESGATE <<<", (5, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 255), 2)

    return msg, hud


# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE OBSTÁCULO (IMX179)
# ══════════════════════════════════════════════════════════════════

def detectar_obstaculo(frame_usb):
    roi  = frame_usb[OBST_Y1:OBST_Y2, OBST_X1:OBST_X2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 4)
    k = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k)
    pct = cv2.countNonZero(thresh) / OBST_AREA
    return pct >= OBST_THRESHOLD_PERCENT, pct

def verificar_linha_lados_usb(frame_usb):
    gray = cv2.cvtColor(frame_usb, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
    k = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    yi   = int(USB_H * 0.50)
    esq  = mask[yi:, 0:int(USB_W*0.35)]
    dir_ = mask[yi:, int(USB_W*0.65):]
    a    = int(USB_W*0.35) * int(USB_H*0.50)
    te   = (cv2.countNonZero(esq) / a) >= 0.08
    td   = (cv2.countNonZero(dir_) / a) >= 0.08
    if te and td:   return "linha ambos"
    elif te:        return "linha esquerda"
    elif td:        return "linha direita"
    else:           return "linha nenhum"


# ══════════════════════════════════════════════════════════════════
#  CALIBRAÇÃO MPU6050
# ══════════════════════════════════════════════════════════════════

offset_roll         = 0.0
guinada_yaw         = 0.0
tempo_anterior_mpu  = time.time()
tempo_ultimo_print_mpu = time.time()

if mpu_ativo:
    print("\n[*] Calibrando MPU6050... ROBÔ PARADO!")
    soma = 0.0
    for _ in range(50):
        ay = ler_dados_mpu(ACCEL_YOUT) / 16384.0
        az = ler_dados_mpu(ACCEL_ZOUT) / 16384.0
        soma += math.degrees(math.atan2(ay, az))
        time.sleep(0.02)
    offset_roll = soma / 50.0
    print(f"[+] Offset Roll: {offset_roll:.2f}°\n")
    tempo_anterior_mpu = time.time()


# ══════════════════════════════════════════════════════════════════
#  CALLBACKS DO DASHBOARD
# ══════════════════════════════════════════════════════════════════

def ao_mudar_modo(novo_modo):
    global modo_atual, estado_obstaculo
    print(f"[WEB] Modo → {novo_modo}")
    if novo_modo == "linha" and modo_atual != "linha":
        parar_imx179(); iniciar_imx500(); iniciar_imx179()
        modo_atual = "linha"; estado_obstaculo = "idle"
    elif novo_modo == "bolas" and modo_atual != "bolas":
        # IMX500 FICA LIGADA no modo bolas (monitora fitas)
        if picam2 is None: iniciar_imx500()
        modo_atual = "bolas"; estado_obstaculo = "idle"
    elif novo_modo == "triangulo" and modo_atual != "triangulo":
        if picam2 is None: iniciar_imx500()
        modo_atual = "triangulo"; estado_obstaculo = "idle"
    dash.atualizar_estado(log={"msg": f"Modo → {novo_modo}", "tipo": "ok"})

def ao_emergencia():
    print("[WEB] PARADA DE EMERGÊNCIA!")
    if ser: ser.write(b"emergencia\n")
    dash.atualizar_estado(log={"msg": "EMERGÊNCIA!", "tipo": "warn"})

def ao_reset_gyro():
    global guinada_yaw
    guinada_yaw = 0.0
    dash.atualizar_estado(log={"msg": "Gyro resetado.", "tipo": "info"})

dash.registrar_callbacks(
    fn_modo=ao_mudar_modo,
    fn_emergencia=ao_emergencia,
    fn_reset_gyro=ao_reset_gyro)
dash.iniciar_servidor()


# ══════════════════════════════════════════════════════════════════
#  ESTADO INICIAL
# ══════════════════════════════════════════════════════════════════

print("\n[+] SISTEMA INICIADO [+]")
modo_atual = "linha"
iniciar_imx500()
iniciar_imx179()
dash.atualizar_estado(log={"msg": "Boot OK. IMX500+IMX179 ativos.", "tipo": "info"})

# cooldown de envio de prata no modo LINHA
last_silver_send = 0.0

try:
    while True:
        # ══════════════════════════════════════════════════════════
        # 1. GIROSCÓPIO
        # ══════════════════════════════════════════════════════════
        if mpu_ativo:
            now_mpu = time.time()
            dt_mpu  = now_mpu - tempo_anterior_mpu
            tempo_anterior_mpu = now_mpu

            ax = ler_dados_mpu(ACCEL_XOUT) / 16384.0
            ay = ler_dados_mpu(ACCEL_YOUT) / 16384.0
            az = ler_dados_mpu(ACCEL_ZOUT) / 16384.0

            arfagem_pitch = -math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
            rotacao_roll  =  math.degrees(math.atan2(ay, az)) - offset_roll
            gyro_z = ler_dados_mpu(GYRO_ZOUT) / 131.0
            if abs(gyro_z) > 1.0:
                guinada_yaw += gyro_z * dt_mpu

            if (now_mpu - tempo_ultimo_print_mpu) > 0.5:
                if ser: ser.write(f"MPU_Z:{guinada_yaw:.1f}\n".encode())
                print(f"[MPU] Roll:{rotacao_roll:.1f}° Pitch:{arfagem_pitch:.1f}° Yaw:{guinada_yaw:.1f}°")
                tempo_ultimo_print_mpu = now_mpu
                dash.atualizar_estado(
                    gyro_roll=round(rotacao_roll, 1),
                    gyro_pitch=round(arfagem_pitch, 1),
                    gyro_yaw=round(guinada_yaw, 1))

        # ══════════════════════════════════════════════════════════
        # 2. ESCUTAR EV3
        # ══════════════════════════════════════════════════════════
        if ser and ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip().lower()
            print(f"[EV3] → '{cmd}'")

            if "linha" in cmd and modo_atual != "linha":
                if cap_usb is None: iniciar_imx179()
                if picam2  is None: iniciar_imx500()
                modo_atual = "linha"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual,
                    log={"msg": "EV3: modo linha.", "tipo": "info"})

            elif ("bolas" in cmd or "resgate_on" in cmd) and modo_atual != "bolas":
                # IMX500 NÃO é desligada — monitora fitas
                if picam2 is None: iniciar_imx500()
                modo_atual = "bolas"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual,
                    log={"msg": "EV3: modo bolas. IMX500 monitorando fitas.", "tipo": "info"})

            elif "triangulo" in cmd and modo_atual != "triangulo":
                if picam2 is None: iniciar_imx500()
                modo_atual = "triangulo"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual,
                    log={"msg": "EV3: modo triângulo. IMX500 monitorando fitas.", "tipo": "info"})

            elif "confirma obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "verificando_linha"
                dash.atualizar_estado(obstaculo=estado_obstaculo,
                    log={"msg": "EV3 confirmou obstáculo.", "tipo": "warn"})

            elif "nega obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "idle"
                ultimo_aviso_obstaculo = time.time()
                dash.atualizar_estado(obstaculo=estado_obstaculo,
                    log={"msg": "EV3 negou obstáculo.", "tipo": "info"})

        # ══════════════════════════════════════════════════════════
        # 3. PROCESSAMENTO DE VISÃO
        # ══════════════════════════════════════════════════════════
        start_time = time.time()
        msg_serial = None

        # ──────────────────────────────────────────────────────────
        # MODO LINHA  →  IMX500 (linha+verde+prata) + IMX179 (obstáculo)
        # ──────────────────────────────────────────────────────────
        if modo_atual == "linha":

            if picam2 is not None:
                frame = picam2.capture_array("main")
                frame = cv2.flip(frame, -1)

                # Processamento avançado (preta + verde + prata)
                comando_verde, hud_frame, prata_det = processar_linha_vetorial(frame)
                
                if gravador_atual:
                    gravador_atual.write(hud_frame)
                dash.atualizar_frame_imx500(hud_frame)

                agora = time.time()

                # Avisa prata (com cooldown para não travar a serial)
                if prata_det and (agora - last_silver_send) > SILVER_COOLDOWN:
                    msg_serial = "prata visivel\n"
                    last_silver_send = agora
                    dash.atualizar_estado(
                        log={"msg": "Prata detectada no modo linha!", "tipo": "warn"})

                # Avisa verde (apenas se não está mandando prata agora)
                elif comando_verde != "frente":
                    if (comando_verde != last_detection["cmd"] or
                            (agora - last_detection["time"]) > 1.5):
                        msg_serial = f"{comando_verde}\n"
                        last_detection = {"time": agora, "side": None,
                                          "cmd": comando_verde}

                dash.atualizar_estado(
                    modo=modo_atual,
                    cmd_camera=comando_verde,
                    fps_imx500=round(1 / (time.time()-start_time+1e-4), 1),
                    obstaculo=estado_obstaculo)

            # IMX179 — obstáculo
            if cap_usb is not None:
                cap_usb.grab()
                ret_usb, frame_usb = cap_usb.retrieve()
                if ret_usb:
                    if gravador_usb: gravador_usb.write(frame_usb)
                    dash.atualizar_frame_imx179(frame_usb)
                    dash.atualizar_estado(
                        fps_imx179=round(1/(time.time()-start_time+1e-4), 1))

                    agora = time.time()
                    if estado_obstaculo == "idle":
                        if (agora - ultimo_aviso_obstaculo) > COOLDOWN_OBSTACULO:
                            tem, pct = detectar_obstaculo(frame_usb)
                            if tem:
                                msg_serial = "obstaculo detectado\n"
                                estado_obstaculo = "aguardando_confirmacao"
                                dash.atualizar_estado(obstaculo=estado_obstaculo,
                                    log={"msg": f"Obstáculo! {pct*100:.1f}%",
                                         "tipo": "warn"})

                    elif estado_obstaculo == "aguardando_confirmacao":
                        if (agora - ultimo_aviso_obstaculo) > 5.0 \
                                and ultimo_aviso_obstaculo > 0:
                            estado_obstaculo = "idle"
                            ultimo_aviso_obstaculo = agora
                            dash.atualizar_estado(obstaculo=estado_obstaculo,
                                log={"msg": "Timeout obstáculo.", "tipo": "warn"})

                    elif estado_obstaculo == "verificando_linha":
                        res = verificar_linha_lados_usb(frame_usb)
                        msg_serial = f"{res}\n"
                        estado_obstaculo = "idle"
                        ultimo_aviso_obstaculo = agora
                        dash.atualizar_estado(obstaculo=estado_obstaculo,
                            log={"msg": f"Linha lados: {res}", "tipo": "ok"})

        # ──────────────────────────────────────────────────────────
        # MODO BOLAS  →  IMX179 (YOLO bolas) + IMX500 (fitas resgate)
        # ──────────────────────────────────────────────────────────
        elif modo_atual == "bolas":

            # IMX500 monitora fitas (prata/preta)
            if picam2 is not None:
                frame_500 = picam2.capture_array("main")
                frame_500 = cv2.flip(frame_500, -1)
                msg_fita, hud_500 = monitorar_fitas_resgate(frame_500)
                if gravador_atual: gravador_atual.write(hud_500)
                dash.atualizar_frame_imx500(hud_500)
                if msg_fita:
                    msg_serial = msg_fita
                    dash.atualizar_estado(
                        log={"msg": f"Fita: {msg_fita.strip()}", "tipo": "warn"})

            # IMX179 — YOLO bolas
            if cap_usb is not None:
                cap_usb.grab()
                ret, frame = cap_usb.retrieve()
                if ret:
                    hud_frame = frame.copy()
                    results = yolo_ball(frame, imgsz=160, device='cpu',
                                        half=False, verbose=False, conf=0.80)[0]
                    if results.boxes:
                        box = results.boxes[0]
                        if box.conf.item() > 0.90:
                            x1,y1,x2,y2 = map(int, box.xyxy[0].tolist())
                            larg = x2-x1; alt = y2-y1
                            area_px = larg*alt
                            cx = x1 + larg//2
                            side  = ("esquerda" if cx < 53
                                     else "direita" if cx > 106 else "meio")
                            classe = yolo_ball.names[int(box.cls.item())]
                            cv2.rectangle(hud_frame,(x1,y1),(x2,y2),(0,0,255),2)
                            cv2.putText(hud_frame,
                                f"{classe} {side} ({area_px}px)",
                                (x1,y1-5), cv2.FONT_HERSHEY_SIMPLEX,
                                0.4, (0,0,255), 1)
                            if (side != last_detection["side"] or
                                    (time.time()-last_detection["time"]) > 0.3):
                                # Só manda bola se não acabou de mandar fita
                                if msg_serial is None:
                                    msg_serial = (f"Detectado: {classe}\n"
                                                  f"Area: {area_px}px\n"
                                                  f"Lado: {side}\n")
                                last_detection = {"time": time.time(),
                                                  "side": side, "cmd": None}
                    if gravador_usb: gravador_usb.write(hud_frame)
                    dash.atualizar_frame_imx179(hud_frame)
                    dash.atualizar_estado(
                        modo=modo_atual,
                        fps_imx179=round(1/(time.time()-start_time+1e-4),1))

        # ──────────────────────────────────────────────────────────
        # MODO TRIÂNGULO  →  IMX179 (áreas cor) + IMX500 (fitas resgate)
        # ──────────────────────────────────────────────────────────
        elif modo_atual == "triangulo":

            # IMX500 monitora fitas
            if picam2 is not None:
                frame_500 = picam2.capture_array("main")
                frame_500 = cv2.flip(frame_500, -1)
                msg_fita, hud_500 = monitorar_fitas_resgate(frame_500)
                if gravador_atual: gravador_atual.write(hud_500)
                dash.atualizar_frame_imx500(hud_500)
                if msg_fita:
                    msg_serial = msg_fita
                    dash.atualizar_estado(
                        log={"msg": f"Fita: {msg_fita.strip()}", "tipo": "warn"})

            # IMX179 — detecção de triângulos coloridos
            if cap_usb is not None:
                cap_usb.grab()
                ret, frame = cap_usb.retrieve()
                if ret:
                    hud_frame = frame.copy()
                    hsv_r = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mr1 = cv2.inRange(hsv_r,
                        np.array([0,120,70]),  np.array([10,255,255]))
                    mr2 = cv2.inRange(hsv_r,
                        np.array([170,120,70]),np.array([180,255,255]))
                    mask_red  = cv2.bitwise_or(mr1, mr2)
                    mask_grnr = cv2.inRange(hsv_r, GREEN_MIN, GREEN_MAX)
                    mask_all  = cv2.bitwise_or(mask_red, mask_grnr)
                    cnts, _ = cv2.findContours(
                        mask_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in cnts:
                        if cv2.contourArea(cnt) > 800:
                            x,y,w,h = cv2.boundingRect(cnt)
                            if h > 0 and 4.5 <= float(w)/h <= 7.5:
                                cx2 = x + w//2
                                cor = ("Vermelho"
                                       if mask_red[y+h//2, cx2] > 0
                                       else "Verde")
                                side = ("esquerda" if cx2 < 53
                                        else "direita" if cx2 > 106 else "meio")
                                cv2.rectangle(hud_frame,(x,y),(x+w,y+h),
                                              (0,255,255),2)
                                cv2.putText(hud_frame,
                                    f"{cor} {side}", (x,y-5),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
                                if (side != last_detection["side"] or
                                        (time.time()-last_detection["time"])>0.3):
                                    if msg_serial is None:
                                        msg_serial = (f"Area: {cor}\n"
                                                      f"Centro: {cx2}\n"
                                                      f"Lado: {side}\n")
                                    last_detection = {"time": time.time(),
                                                      "side": side, "cmd": None}
                    if gravador_usb: gravador_usb.write(hud_frame)
                    dash.atualizar_frame_imx179(hud_frame)
                    dash.atualizar_estado(
                        modo=modo_atual,
                        fps_imx179=round(1/(time.time()-start_time+1e-4),1))

        # ══════════════════════════════════════════════════════════
        # 4. ENVIO SERIAL
        # ══════════════════════════════════════════════════════════
        if msg_serial and ser is not None:
            ser.write(msg_serial.encode())
            fps_a = round(1/(time.time()-start_time+1e-4), 1)
            print(f"[EV3] ← '{msg_serial.strip()}' | FPS:{fps_a}")
            dash.atualizar_estado(
                log={"msg": f"EV3 ← {msg_serial.strip()}", "tipo": "ok"})

except KeyboardInterrupt:
    print("\n[*] Encerrando...")
finally:
    parar_imx500()
    parar_imx179()
    if ser and ser.is_open: ser.close()