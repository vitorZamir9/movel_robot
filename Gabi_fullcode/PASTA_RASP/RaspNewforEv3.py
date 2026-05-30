import time
import cv2
import serial
import os
import numpy as np
import math
import logging
from picamera2 import Picamera2
import smbus2
import dashboard_server as dash

# ============ CONFIGURAÇÃO RADICAL ANTI-TRAVAMENTO ============
os.environ['DISPLAY'] = ':0'
os.environ["YOLO_VERBOSE"] = "False"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from ultralytics import YOLO

cv2.setNumThreads(0)
Picamera2.set_logging(logging.ERROR)

# ============ CONFIGURAÇÃO DO GIROSCÓPIO (MPU6050) ============
MPU_ADDR   = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT = 0x3B
ACCEL_YOUT = 0x3D
ACCEL_ZOUT = 0x3F
GYRO_ZOUT  = 0x47

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
        high  = bus.read_byte_data(MPU_ADDR, registo)
        low   = bus.read_byte_data(MPU_ADDR, registo + 1)
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

# ============ MODELOS YOLO — RESGATE (ORIGINAL .PT) ============
print("[*] Carregando I.A. de Resgate (.pt original)...")
yolo_ball = YOLO("modelo/ball_detect_s.pt")

# ============ MODELO AI — PRATA (ORIGINAL .PT) ============
SILVER_MODEL_PATH     = "modelo/silver_classify_s.pt"
SILVER_INFER_INTERVALO = 7      
SILVER_AI_THRESHOLD   = 0.50   

_silver_infer_counter = 0
_silver_confianca     = 0.0    

try:
    yolo_silver       = YOLO(SILVER_MODEL_PATH)
    yolo_silver_ativo = True
    print(f"[+] Modelo silver carregado: {SILVER_MODEL_PATH}")
except Exception as _e:
    print(f"[AVISO] Modelo silver NÃO carregado: {_e}")
    yolo_silver_ativo = False
    yolo_silver       = None

# ============ CONSTANTES DA IMX500 ============
W, H     = 320, 240
CENTRO_X = W // 2
BASE_Y   = H

# ─── LINHA PRETA ───────────────────────────────────────────────
BLACK_MIN        = np.array([0,   0,   0])
BLACK_MAX_TOP    = np.array([180, 255, 55])   
BLACK_MAX_BOTTOM = np.array([180, 255, 70])   

# ─── VERDE ─────────────────────────────────────────────────────
GREEN_MIN = np.array([40, 80,  40])
GREEN_MAX = np.array([90, 255, 255])

# ─── PRATA REFLECTIVA (brilhante, foto 1) ──────────────────────
SILVER_REFLECT_HSV_MIN = np.array([0,   0,  170])
SILVER_REFLECT_HSV_MAX = np.array([180, 20, 255])
SILVER_REFLECT_MIN_AREA = 1500

# ─── CINZA FOSCO / NÃO-REFLECTIVO (foto 2) ─────────────────────
SILVER_MATTE_HSV_MIN   = np.array([0,   0,  80])
SILVER_MATTE_HSV_MAX   = np.array([180, 15, 185])
SILVER_MATTE_MIN_AREA  = 2500

SILVER_MIN_WIDTH_RATIO = 0.25
RESGATE_BLACK_MIN_AREA = 2000

# ══════════════════════════════════════════════════════════════════
#  CALIBRAÇÃO DE DETECÇÃO DE BOLAS
# ══════════════════════════════════════════════════════════════════
BALL_DEBUG        = True   # <-- DEIXEI TRUE PRA VOCÊ VER NO TERMINAL SE ELE DETECTA ALGO
BALL_CONF_MIN     = 0.45   # <-- BAIXEI UM POUCO PRA AJUDAR O .PT
BALL_AREA_MIN     = 1200   
BALL_AREA_MAX     = 70000  
BALL_PROP_MIN     = 0.40
BALL_PROP_MAX     = 1.80
BALL_MARGEM_BORDA = 0.10   

# ============ CONSTANTES DA IMX179 ============
USB_W = 160
USB_H = 120

OBST_X1   = int(USB_W * 0.20)
OBST_X2   = int(USB_W * 0.80)
OBST_Y1   = int(USB_H * 0.10)
OBST_Y2   = int(USB_H * 0.90)
OBST_AREA = (OBST_X2 - OBST_X1) * (OBST_Y2 - OBST_Y1)
OBST_THRESHOLD_PERCENT = 0.30
# GLOBAIS DE ESTABILIDADE
_contador_frames_prata = 0
_mask_obstaculo_acumulada = None
# ============ VARIÁVEIS DE CONTROLE ============
last_detection        = {"time": 0, "side": None, "cmd": None}
last_silver_send      = 0.0
SILVER_COOLDOWN       = 1.0
ultimo_aviso_fita_str = "—"
picam2                = None
cap_usb               = None

estado_obstaculo       = "idle"
ultimo_aviso_obstaculo = 0.0
COOLDOWN_OBSTACULO     = 3.0

rotacao_roll  = 0.0
arfagem_pitch = 0.0
guinada_yaw   = 0.0

LINE_CROP_RATIO = 0.50
x_last = float(CENTRO_X)
y_last = float(H // 2)

_last_send_resgate = {"prata": 0.0, "preta": 0.0}
RESGATE_COOLDOWN   = 0.8

# ══════════════════════════════════════════════════════════════════
#  GERENCIADORES DE CÂMERA E VÍDEO
# ══════════════════════════════════════════════════════════════════

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
#  DETECÇÃO DE PRATA — SISTEMA HÍBRIDO (AI + Visão)
# ══════════════════════════════════════════════════════════════════

def _mask_silver_visao(frame_bgr):
    blur = cv2.GaussianBlur(frame_bgr, (5, 5), 0)
    hsv  = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    mask_r = cv2.inRange(hsv, SILVER_REFLECT_HSV_MIN, SILVER_REFLECT_HSV_MAX)
    mask_m = cv2.inRange(hsv, SILVER_MATTE_HSV_MIN,   SILVER_MATTE_HSV_MAX)
    k3 = np.ones((3, 3), np.uint8)
    k9 = np.ones((9, 9), np.uint8)
    mask_r = cv2.erode(mask_r,  k3, iterations=2)
    mask_r = cv2.dilate(mask_r, k9, iterations=3)
    mask_m = cv2.subtract(mask_m, mask_r)
    mask_m = cv2.erode(mask_m,  k3, iterations=3)
    mask_m = cv2.dilate(mask_m, k9, iterations=4)
    return cv2.bitwise_or(mask_r, mask_m)

def _detectar_silver_visao(frame_bgr):
    blur = cv2.GaussianBlur(frame_bgr, (5, 5), 0)
    hsv  = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    k3 = np.ones((3, 3), np.uint8)
    k9 = np.ones((9, 9), np.uint8)
    mask_r = cv2.inRange(hsv, SILVER_REFLECT_HSV_MIN, SILVER_REFLECT_HSV_MAX)
    mask_r = cv2.erode(mask_r,  k3, iterations=2)
    mask_r = cv2.dilate(mask_r, k9, iterations=3)
    mask_r = cv2.erode(mask_r,  k3, iterations=1)
    mask_m = cv2.inRange(hsv, SILVER_MATTE_HSV_MIN, SILVER_MATTE_HSV_MAX)
    mask_m = cv2.subtract(mask_m, mask_r)
    mask_m = cv2.erode(mask_m,  k3, iterations=3)
    mask_m = cv2.dilate(mask_m, k9, iterations=4)
    mask_m = cv2.erode(mask_m,  k3, iterations=2)

    for mask, min_area, tipo in [
            (mask_r, SILVER_REFLECT_MIN_AREA, "reflectiva"),
            (mask_m, SILVER_MATTE_MIN_AREA,   "fosca")]:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) < min_area: continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w < (W * SILVER_MIN_WIDTH_RATIO): continue
            if h > 0 and float(w) / h < 1.5: continue
            return True, tipo
    return False, "nenhum"

_contador_frames_prata = 0
def detectar_prata(frame_bgr, hud=None):
    global _silver_infer_counter, _silver_confianca, _contador_frames_prata
    
    if frame_bgr is None or frame_bgr.size == 0:
        return False, 0.0, "nenhum"

    # 1. IA com Histerese (Filtro de estabilidade)
    prata_ai = False
    if yolo_silver_ativo and yolo_silver is not None:
        _silver_infer_counter += 1
        if _silver_infer_counter >= SILVER_INFER_INTERVALO:
            _silver_infer_counter = 0
            try:
                frame_96 = cv2.resize(frame_bgr, (96, 96))
                results = yolo_silver.predict(frame_96, imgsz=96, verbose=False, device='cpu')
                result = results[0]
                nome_classe = result.names[int(result.probs.top1)].lower()
                confianca = float(result.probs.top1conf)
                
                if ("prata" in nome_classe or "silver" in nome_classe) and confianca > SILVER_AI_THRESHOLD:
                    _silver_confianca = confianca
                    _contador_frames_prata += 1
                else:
                    _silver_confianca = 0.0
                    _contador_frames_prata = max(0, _contador_frames_prata - 1)
                
                prata_ai = (_contador_frames_prata >= 3)
            except: pass

    # 2. Visão Computacional (Backup imediato)
    prata_visao, tipo_visao = _detectar_silver_visao(frame_bgr)
    
    # 3. Decisão Final (Híbrido)
    prata_detectada = (prata_ai or prata_visao) if yolo_silver_ativo else prata_visao

    # 4. HUD
    if hud is not None and prata_detectada:
        cv2.rectangle(hud, (20, 20), (108, 108), (0, 255, 0), 2)
        cv2.putText(hud, "PRATA OK", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return prata_detectada, _silver_confianca, tipo_visao
# ══════════════════════════════════════════════════════════════════
#  HELPERS DE VISÃO — LINHA PRETA
# ══════════════════════════════════════════════════════════════════

def _mask_black_linha(frame_bgr):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask_bot = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_BOTTOM)
    mask_top = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_TOP)
    split = int(H * 0.40)
    mask_black = mask_bot.copy()
    mask_black[0:split, :] = mask_top[0:split, :]
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    mask_black = cv2.subtract(mask_black, mask_green)
    k = np.ones((3, 3), np.uint8)
    mask_black = cv2.erode(mask_black,  k, iterations=5)
    mask_black = cv2.dilate(mask_black, k, iterations=17)
    mask_black = cv2.erode(mask_black,  k, iterations=9)
    return mask_black

def _encontrar_melhor_contorno(contours_blk):
    global x_last, y_last
    if not contours_blk: return None, None
    candidatos = []
    for i, cnt in enumerate(contours_blk):
        box    = cv2.boxPoints(cv2.minAreaRect(cnt))
        box_s  = box[box[:, 1].argsort()[::-1]]
        bot_y  = box_s[0][1]
        box_xs = box[box[:, 0].argsort()]
        x_mean = (np.clip(box_xs[0][0], 0, W) + np.clip(box_xs[-1][0], 0, W)) / 2
        box_ys = box[box[:, 1].argsort()]
        y_mean = (np.clip(box_ys[0][1], 0, H) + np.clip(box_ys[-1][1], 0, H)) / 2
        dist   = abs(x_last - x_mean) + abs(y_last - y_mean)
        candidatos.append((i, bot_y, dist, x_mean, y_mean))
    candidatos.sort(key=lambda c: (-c[1], c[2]))
    melhor = candidatos[0]
    x_last = melhor[3]
    y_last = melhor[4]
    cnt_esc = contours_blk[melhor[0]]
    crop_y = int(H * LINE_CROP_RATIO)
    cnt_crop = cnt_esc[cnt_esc[:, 0, 1] >= crop_y]
    return cnt_esc, cnt_crop if len(cnt_crop) > 0 else cnt_esc

def _calcular_alvo(cnt_full, cnt_crop):
    M = cv2.moments(cnt_crop)
    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = CENTRO_X, H // 2
    top_y   = int(np.min(cnt_full[:, 0, 1]))
    top_pts = cnt_full[cnt_full[:, 0, 1] == top_y]
    top_x   = int(np.mean(top_pts[:, 0, 0]))
    return int(cx * 0.70 + top_x * 0.30), cy

# ══════════════════════════════════════════════════════════════════
#  PROCESSAMENTO PRINCIPAL — MODO LINHA (IMX500)
# ══════════════════════════════════════════════════════════════════

def processar_linha_vetorial(frame):
    hud = frame.copy()
    frame_blur = cv2.GaussianBlur(frame, (5, 5), 0)
    mask_black = _mask_black_linha(frame_blur)

    prata_detectada, silver_conf, silver_tipo = detectar_prata(frame_blur, hud=hud)

    mask_green = cv2.inRange(cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV), GREEN_MIN, GREEN_MAX)
    k5 = np.ones((5, 5), np.uint8)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, k5)
    k_dil = np.ones((15, 15), np.uint8)
    mask_black_dilated = cv2.dilate(mask_black, k_dil, iterations=1)

    cnts_grn, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens_brutos = []
    for cnt in cnts_grn:
        if cv2.contourArea(cnt) > 1000:
            x, y, w, h = cv2.boundingRect(cnt)
            prop = float(w) / h if h > 0 else 0
            solidez = cv2.contourArea(cnt) / (w * h) if w * h > 0 else 0
            if 0.5 <= prop <= 2.0 and solidez > 0.45:
                mask_g = np.zeros_like(mask_green)
                cv2.drawContours(mask_g, [cnt], -1, 255, -1)
                if cv2.countNonZero(cv2.bitwise_and(mask_black_dilated, mask_g)) > 0:
                    greens_brutos.append((x, y, w, h))
                    cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 0), 2)

    greens_validos = []
    if greens_brutos:
        greens_brutos.sort(key=lambda g: g[1], reverse=True)
        y_ref = greens_brutos[0][1]
        greens_validos = [g for g in greens_brutos if abs(g[1] - y_ref) < 40]
        greens_validos.sort(key=lambda g: g[0])

    cnts_blk, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnts_blk = [c for c in cnts_blk if cv2.contourArea(c) > 1500]

    alvo_x, alvo_y = CENTRO_X, H // 2
    comando_serial  = "frente"

    if cnts_blk:
        cnt_full, cnt_crop = _encontrar_melhor_contorno(cnts_blk)
        if cnt_full is not None:
            cv2.drawContours(hud, [cnt_full], -1, (255, 0, 0), 2)
            if cnt_crop is not None and len(cnt_crop) > 0:
                cv2.drawContours(hud, [cnt_crop], -1, (255, 255, 0), 2)
            alvo_x, alvo_y = _calcular_alvo(cnt_full, cnt_crop)

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

    cv2.line(hud, (CENTRO_X, BASE_Y), (alvo_x, alvo_y), (0, 0, 255), 2)
    cv2.circle(hud, (alvo_x, alvo_y), 5, (0, 0, 255), -1)
    cor_cmd = (0, 255, 255) if prata_detectada else (0, 255, 0)
    cv2.putText(hud, f"CMD:{comando_serial}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, cor_cmd, 1)

    return comando_serial, hud, prata_detectada

# ══════════════════════════════════════════════════════════════════
#  MONITORAMENTO DE FITAS — MODO RESGATE (IMX500 em paralelo)
# ══════════════════════════════════════════════════════════════════

def monitorar_fitas_resgate(frame):
    hud   = frame.copy()
    agora = time.time()
    msg   = None

    frame_blur = cv2.GaussianBlur(frame, (5, 5), 0)
    prata_ok, _, _ = detectar_prata(frame_blur, hud=hud)

    mask_black = _mask_black_linha(frame_blur)
    cnts_black, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    preta_ok = False
    for cnt in cnts_black:
        if cv2.contourArea(cnt) > RESGATE_BLACK_MIN_AREA:
            preta_ok = True
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 0, 0), 2)
            cv2.putText(hud, f"SAIDA ({cv2.contourArea(cnt):.0f}px)",
                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (50, 50, 255), 1)

    if prata_ok and (agora - _last_send_resgate["prata"]) > RESGATE_COOLDOWN:
        msg = "prata visivel\n"
        _last_send_resgate["prata"] = agora
        cv2.putText(hud, ">>> ENTRADA RESGATE <<<", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)

    elif preta_ok and not prata_ok and (agora - _last_send_resgate["preta"]) > RESGATE_COOLDOWN:
        msg = "preta visivel\n"
        _last_send_resgate["preta"] = agora
        cv2.putText(hud, ">>> SAIDA RESGATE <<<", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 255), 2)

    return msg, hud, prata_ok, preta_ok

# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE OBSTÁCULO (IMX179)
# ══════════════════════════════════════════════════════════════════

def detectar_obstaculo(frame_usb):
    gray = cv2.cvtColor(frame_usb, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges       = cv2.Canny(blur, 30, 100)
    cx1, cx2    = int(USB_W*0.25), int(USB_W*0.75)
    cy2         = int(USB_H*0.80)
    edges_c     = edges[0:cy2, cx1:cx2]
    proj_col    = np.sum(edges_c, axis=0)
    pico_max    = np.max(proj_col) if len(proj_col) > 0 else 0
    tem_bordas  = pico_max > (USB_H * 0.80 * 255 * 0.10)

    roi_s     = frame_usb[int(USB_H*0.55):USB_H, int(USB_W*0.20):int(USB_W*0.80)]
    hsv_s     = cv2.cvtColor(roi_s, cv2.COLOR_BGR2HSV)
    mask_s    = cv2.inRange(hsv_s, np.array([0,0,0]), np.array([180,255,60]))
    area_s    = roi_s.shape[0] * roi_s.shape[1]
    pct_s     = cv2.countNonZero(mask_s) / area_s if area_s > 0 else 0
    tem_sombra = pct_s >= 0.12

    roi_b   = frame_usb[int(USB_H*0.05):int(USB_H*0.75), int(USB_W*0.25):int(USB_W*0.75)]
    if roi_b.size > 0:
        std_b  = np.std(roi_b.astype(np.float32))
        mean_b = np.mean(roi_b)
        tem_bloco = (60 < mean_b < 220) and (std_b < 55)
    else:
        tem_bloco = False

    confirmacoes = int(tem_bordas) + int(tem_sombra) + int(tem_bloco)
    detectado    = confirmacoes >= 2
    pct_final    = (pct_s + (1.0 if tem_bordas else 0.0) + (1.0 if tem_bloco else 0.0)) / 3.0
    return detectado, pct_final

def processar_obstaculo_estavel(frame_bgr, hud=None):
    global _mask_obstaculo_acumulada
    
    # 1. Detecção original
    detectado, _ = detectar_obstaculo(frame_bgr) 
    
    # 2. Criação da máscara binária
    mask_atual = np.zeros(frame_bgr.shape[:2], dtype=np.uint8)
    if detectado:
        mask_atual[:] = 255
    
    # 3. Inicializa acumulador
    if _mask_obstaculo_acumulada is None:
        _mask_obstaculo_acumulada = np.zeros_like(mask_atual, dtype=np.float32)
    
    # 4. Filtro de estabilidade (Histerese)
    _mask_obstaculo_acumulada = cv2.addWeighted(_mask_obstaculo_acumulada, 0.85, 
                                                mask_atual.astype(np.float32), 0.15, 0)
    
    # 5. Threshold final
    _, mask_limpa = cv2.threshold(_mask_obstaculo_acumulada, 200, 255, cv2.THRESH_BINARY)
    mask_limpa = mask_limpa.astype(np.uint8)
    
    # 6. DESENHO NO HUD (A "Mancha" que você queria)
    if hud is not None:
        # Cria uma camada semi-transparente marrom apenas onde o obstáculo foi consolidado
        overlay = hud.copy()
        # Define a cor marrom (BGR: 50, 100, 150) na área da máscara
        overlay[mask_limpa > 0] = (50, 100, 150) 
        # Aplica com transparência
        cv2.addWeighted(overlay, 0.4, hud, 0.6, 0, hud)
        
        # Opcional: Texto de debug no HUD
        if cv2.countNonZero(mask_limpa) > 1000:
            cv2.putText(hud, "OBSTACULO DETECTADO", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return mask_limpa

def verificar_linha_lados_usb(frame_usb):
    gray  = cv2.cvtColor(frame_usb, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
    k     = np.ones((3, 3), np.uint8)
    mask  = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    yi    = int(USB_H * 0.50)
    esq   = mask[yi:, 0:int(USB_W*0.35)]
    dir_  = mask[yi:, int(USB_W*0.65):]
    a     = int(USB_W*0.35) * int(USB_H*0.50)
    te    = (cv2.countNonZero(esq)  / a) >= 0.08
    td    = (cv2.countNonZero(dir_) / a) >= 0.08
    if te and td:  return "linha ambos"
    elif te:       return "linha esquerda"
    elif td:       return "linha direita"
    else:          return "linha nenhum"

# ══════════════════════════════════════════════════════════════════
#  CALIBRAÇÃO MPU6050
# ══════════════════════════════════════════════════════════════════

offset_roll            = 0.0
guinada_yaw            = 0.0
tempo_anterior_mpu     = time.time()
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
        modo_atual = "linha"
    elif novo_modo == "bolas" and modo_atual != "bolas":
        if picam2 is None: iniciar_imx500()
        modo_atual = "bolas"
    elif novo_modo == "triangulo" and modo_atual != "triangulo":
        if picam2 is None: iniciar_imx500()
        modo_atual = "triangulo"
        
    estado_obstaculo = "idle"
    dash.atualizar_estado(obstaculo="idle", log={"msg": f"Modo → {novo_modo}", "tipo": "ok"})

def ao_emergencia():
    print("[WEB] PARADA DE EMERGÊNCIA!")
    if ser: ser.write(b"emergencia\n")
    dash.atualizar_estado(log={"msg": "EMERGÊNCIA!", "tipo": "warn"})

def ao_reset_gyro():
    global guinada_yaw
    guinada_yaw = 0.0
    dash.atualizar_estado(log={"msg": "Gyro resetado.", "tipo": "info"})

dash.registrar_callbacks(fn_modo=ao_mudar_modo, fn_emergencia=ao_emergencia, fn_reset_gyro=ao_reset_gyro)
dash.iniciar_servidor()

# ══════════════════════════════════════════════════════════════════
#  ESTADO INICIAL E LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════

print("\n[+] SISTEMA INICIADO [+]")
modo_atual = "linha"
iniciar_imx500()
iniciar_imx179()
dash.atualizar_estado(log={"msg": "Boot OK. IMX500+IMX179 ativos.", "tipo": "info"})

try:
    while True:
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
            if abs(gyro_z) > 1.0: guinada_yaw += gyro_z * dt_mpu
            if (now_mpu - tempo_ultimo_print_mpu) > 0.5:
                if ser: ser.write(f"MPU_Z:{guinada_yaw:.1f}\n".encode())
                tempo_ultimo_print_mpu = now_mpu
                dash.atualizar_estado(gyro_roll=round(rotacao_roll, 1), gyro_pitch=round(arfagem_pitch, 1), gyro_yaw=round(guinada_yaw, 1))

        if ser and ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip().lower()
            print(f"[EV3] → '{cmd}'")
            if "linha" in cmd and modo_atual != "linha":
                if cap_usb is None: iniciar_imx179()
                if picam2  is None: iniciar_imx500()
                modo_atual = "linha"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual, obstaculo="idle", log={"msg": "EV3: modo linha.", "tipo": "info"})
            elif ("bolas" in cmd or "resgate_on" in cmd) and modo_atual != "bolas":
                if picam2 is None: iniciar_imx500()
                modo_atual = "bolas"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual, obstaculo="idle", log={"msg": "EV3: modo bolas.", "tipo": "info"})
            elif "triangulo" in cmd and modo_atual != "triangulo":
                if picam2 is None: iniciar_imx500()
                modo_atual = "triangulo"; estado_obstaculo = "idle"
                dash.atualizar_estado(modo=modo_atual, obstaculo="idle", log={"msg": "EV3: modo triângulo.", "tipo": "info"})
            elif "confirma obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "verificando_linha"
                dash.atualizar_estado(obstaculo=estado_obstaculo, log={"msg": "EV3 confirmou obstáculo.", "tipo": "warn"})
            elif "nega obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "idle"
                ultimo_aviso_obstaculo = time.time()
                dash.atualizar_estado(obstaculo=estado_obstaculo, log={"msg": "EV3 negou obstáculo.", "tipo": "info"})

        start_time = time.time()
        msg_serial = None

        # ──────────────────────────────────────────────────────────
        # MODO LINHA
        # ──────────────────────────────────────────────────────────
        if modo_atual == "linha":
            if picam2 is not None:
                try:
                    frame = picam2.capture_array("main")
                    frame = cv2.flip(frame, -1)
                    comando_verde, hud_frame, prata_det = processar_linha_vetorial(frame)
                    if gravador_atual: gravador_atual.write(hud_frame)
                    dash.atualizar_frame_imx500(hud_frame)
                    agora = time.time()
                    if prata_det: ultimo_aviso_fita_str = "prata visivel"
                    dash.atualizar_estado(fita_prata=prata_det, fita_preta=False, ultimo_aviso_fita=ultimo_aviso_fita_str)
                    if prata_det and (agora - last_silver_send) > SILVER_COOLDOWN:
                        msg_serial = "prata visivel\n"
                        last_silver_send = agora
                        dash.atualizar_estado(log={"msg": f"Prata! AI:{_silver_confianca:.2f}", "tipo": "silver"})
                    elif comando_verde != "frente":
                        if (comando_verde != last_detection["cmd"] or (agora - last_detection["time"]) > 1.5):
                            msg_serial = f"{comando_verde}\n"
                            last_detection = {"time": agora, "side": None, "cmd": comando_verde}
                    dash.atualizar_estado(modo=modo_atual, cmd_camera=comando_verde, fps_imx500=round(1 / (time.time()-start_time+1e-4), 1), obstaculo=estado_obstaculo)
                except Exception as e:
                    pass

            if cap_usb is not None and cap_usb.isOpened():
                try:
                    cap_usb.grab()
                    ret_usb, frame_usb = cap_usb.retrieve()
                    if ret_usb and frame_usb is not None and frame_usb.size > 0:
                        if gravador_usb: gravador_usb.write(frame_usb)
                        dash.atualizar_frame_imx179(frame_usb)
                        dash.atualizar_estado(fps_imx179=round(1/(time.time()-start_time+1e-4), 1))
                        agora = time.time()
                        if estado_obstaculo == "idle":
                            if (agora - ultimo_aviso_obstaculo) > COOLDOWN_OBSTACULO:
                                tem, pct = detectar_obstaculo(frame_usb)
                                if tem:
                                    msg_serial = "obstaculo detectado\n"
                                    estado_obstaculo = "aguardando_confirmacao"
                                    dash.atualizar_estado(obstaculo=estado_obstaculo, log={"msg": f"Obstáculo! {pct*100:.1f}%", "tipo": "warn"})
                        elif estado_obstaculo == "aguardando_confirmacao":
                            if (agora - ultimo_aviso_obstaculo) > 5.0 and ultimo_aviso_obstaculo > 0:
                                estado_obstaculo = "idle"
                                ultimo_aviso_obstaculo = agora
                                dash.atualizar_estado(obstaculo=estado_obstaculo, log={"msg": "Timeout obstáculo.", "tipo": "warn"})
                        elif estado_obstaculo == "verificando_linha":
                            res = verificar_linha_lados_usb(frame_usb)
                            msg_serial = f"{res}\n"
                            estado_obstaculo = "idle"
                            ultimo_aviso_obstaculo = agora
                            dash.atualizar_estado(obstaculo=estado_obstaculo, log={"msg": f"Linha lados: {res}", "tipo": "ok"})
                except Exception as e:
                    pass

        # ──────────────────────────────────────────────────────────
        # MODO BOLAS (CORRIGIDO PARA .PT e IMGSZ=320)
        # ──────────────────────────────────────────────────────────
        elif modo_atual == "bolas":
            estado_obstaculo = "idle"

            if picam2 is not None:
                try:
                    frame_500 = picam2.capture_array("main")
                    frame_500 = cv2.flip(frame_500, -1)
                    msg_fita, hud_500, prata_ok, preta_ok = monitorar_fitas_resgate(frame_500)
                    if gravador_atual: gravador_atual.write(hud_500)
                    dash.atualizar_frame_imx500(hud_500)
                    if msg_fita:
                        ultimo_aviso_fita_str = msg_fita.strip()
                        dash.atualizar_estado(fita_prata=prata_ok, fita_preta=preta_ok, ultimo_aviso_fita=ultimo_aviso_fita_str)
                        msg_serial = msg_fita
                        dash.atualizar_estado(log={"msg": f"Fita: {msg_fita.strip()}", "tipo": "silver"})
                except Exception as e: pass

            if cap_usb is not None and cap_usb.isOpened():
                try:
                    cap_usb.grab()
                    ret, frame = cap_usb.retrieve()
                    if ret and frame is not None and frame.size > 0:
                        h_real, w_real = frame.shape[:2]
                        hud_frame      = frame.copy()

                        # ── AQUI ESTÁ A MÁGICA: imgsz=320 E conf=0.45 ──
                        results = yolo_ball.predict(frame, imgsz=320, device='cpu', half=False, verbose=False, conf=0.45)[0]

                        melhor_box  = None
                        melhor_conf = 0.0
                        melhor_area = 0

                        if results.boxes:
                            for b in results.boxes:
                                conf = b.conf.item()

                                x1n, y1n, x2n, y2n = b.xyxyn[0].tolist()
                                x1b = int(x1n * w_real)
                                y1b = int(y1n * h_real)
                                x2b = int(x2n * w_real)
                                y2b = int(y2n * h_real)

                                larg_b = x2b - x1b
                                alt_b  = y2b - y1b
                                area_b = larg_b * alt_b
                                prop   = float(larg_b) / alt_b if alt_b > 0 else 0
                                cx_b   = x1b + larg_b // 2
                                cy_b   = y1b + alt_b  // 2
                                
                                classe_str = yolo_ball.names[int(b.cls.item())]

                                if BALL_DEBUG:
                                    print(f"[DBG BALL] cls={classe_str} conf={conf:.2f} area={area_b} prop={prop:.2f} cx={cx_b} box=({x1b},{y1b},{x2b},{y2b})")
                                    cv2.rectangle(hud_frame,(x1b,y1b),(x2b,y2b),(80,80,80),1)
                                    cv2.putText(hud_frame, f"c:{conf:.2f} a:{area_b} p:{prop:.1f}", (x1b, max(y1b-4, 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.28,(200,200,0),1)

                                if conf < BALL_CONF_MIN: continue
                                if area_b < BALL_AREA_MIN: continue
                                if area_b > BALL_AREA_MAX: continue
                                if not (BALL_PROP_MIN <= prop <= BALL_PROP_MAX): continue
                                if x1b<=2 or y1b<=2 or x2b>=w_real-2 or y2b>=h_real-2: continue

                                mx = int(w_real * BALL_MARGEM_BORDA)
                                my = int(h_real * BALL_MARGEM_BORDA)
                                if (cx_b<mx or cx_b>w_real-mx or cy_b<my or cy_b>h_real-my): continue

                                if area_b > melhor_area:
                                    melhor_area = area_b
                                    melhor_conf = conf
                                    melhor_box  = b

                        if melhor_box is not None:
                            x1n, y1n, x2n, y2n = melhor_box.xyxyn[0].tolist()
                            x1 = int(x1n * w_real)
                            y1 = int(y1n * h_real)
                            x2 = int(x2n * w_real)
                            y2 = int(y2n * h_real)

                            larg    = x2 - x1
                            alt     = y2 - y1
                            area_px = larg * alt
                            cx      = x1 + larg // 2
                            cy      = y1 + alt  // 2
                            
                            side    = ("esquerda" if cx < (w_real // 3)
                                       else "direita" if cx > (2 * w_real // 3)
                                       else "meio")
                            
                            classe  = yolo_ball.names[int(melhor_box.cls.item())]
                            cor_box = (180, 180, 180) if "silver" in classe.lower() else (50,  50,  50 ) if "black"  in classe.lower() else (0, 0, 255)

                            cv2.rectangle(hud_frame, (x1, y1), (x2, y2), cor_box, 2)
                            cv2.circle(hud_frame, (cx, cy), 5, (255, 255, 255), -1)
                            cv2.putText(hud_frame, f"{classe} {side} {melhor_conf:.2f}", (x1, max(y1-6, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor_box, 1)

                            if (side != last_detection["side"] or (time.time()-last_detection["time"]) > 0.3):
                                if msg_serial is None:
                                    msg_serial = f"Detectado: {classe}\nArea: {area_px}px\nLado: {side}\n"
                                last_detection = {"time": time.time(), "side": side, "cmd": None}

                        if gravador_usb: gravador_usb.write(hud_frame)
                        dash.atualizar_frame_imx179(hud_frame)
                        dash.atualizar_estado(modo=modo_atual, fps_imx179=round(1/(time.time()-start_time+1e-4), 1))
                except Exception as e:
                    print(f"[BOLAS] Erro captura USB: {e}")

        # ──────────────────────────────────────────────────────────
        # MODO TRIÂNGULO
        # ──────────────────────────────────────────────────────────
        elif modo_atual == "triangulo":
            estado_obstaculo = "idle"
            
            if picam2 is not None:
                try:
                    frame_500 = picam2.capture_array("main")
                    frame_500 = cv2.flip(frame_500, -1)
                    msg_fita, hud_500, prata_ok, preta_ok = monitorar_fitas_resgate(frame_500)
                    if gravador_atual: gravador_atual.write(hud_500)
                    dash.atualizar_frame_imx500(hud_500)
                    if msg_fita:
                        ultimo_aviso_fita_str = msg_fita.strip()
                        dash.atualizar_estado(fita_prata=prata_ok, fita_preta=preta_ok, ultimo_aviso_fita=ultimo_aviso_fita_str)
                        msg_serial = msg_fita
                        dash.atualizar_estado(log={"msg": f"Fita: {msg_fita.strip()}", "tipo": "silver"})
                except: pass

            if cap_usb is not None and cap_usb.isOpened():
                try:
                    cap_usb.grab()
                    ret, frame = cap_usb.retrieve()
                    if ret and frame is not None and frame.size > 0:
                        hud_frame  = frame.copy()
                        h_t, w_t   = frame.shape[:2]

                        roi_y_ini  = int(h_t * 0.45)
                        roi_frame  = frame[roi_y_ini:, :]
                        hsv_r      = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)

                        mr1        = cv2.inRange(hsv_r, np.array([0,   150, 60]),  np.array([10,  255, 255]))
                        mr2        = cv2.inRange(hsv_r, np.array([170, 150, 60]),  np.array([180, 255, 255]))
                        mask_red   = cv2.bitwise_or(mr1, mr2)
                        mask_grnr  = cv2.inRange(hsv_r, np.array([40, 120, 40]),   np.array([90, 255, 255]))

                        k = np.ones((5, 5), np.uint8)
                        mask_red   = cv2.morphologyEx(mask_red,  cv2.MORPH_CLOSE, k)
                        mask_grnr  = cv2.morphologyEx(mask_grnr, cv2.MORPH_CLOSE, k)
                        mask_all   = cv2.bitwise_or(mask_red, mask_grnr)

                        cnts, _    = cv2.findContours(mask_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        for cnt in cnts:
                            area_cnt = cv2.contourArea(cnt)
                            if area_cnt < 1200: continue
                            x, y, w, h = cv2.boundingRect(cnt)
                            if h == 0: continue
                            prop_t = float(w) / h
                            if not (3.0 <= prop_t <= 10.0): continue
                            if w < int(w_t * 0.20): continue

                            y_full  = y + roi_y_ini
                            cx2     = x + w // 2
                            cx_full = cx2 
                            cy_roi  = y + h // 2
                            cor     = "Vermelho" if mask_red[cy_roi, cx2] > 0 else "Verde"
                            side    = "esquerda" if cx_full < (w_t // 3) else ("direita" if cx_full > (2 * w_t // 3) else "meio")

                            cor_rect = (0, 0, 200) if cor == "Vermelho" else (0, 180, 0)
                            cv2.rectangle(hud_frame, (x, y_full), (x+w, y_full+h), (0, 255, 255), 2)
                            cv2.rectangle(hud_frame, (x+2, y_full+2), (x+w-2, y_full+h-2), cor_rect, -1)
                            cv2.putText(hud_frame, f"{cor} {side}", (x, max(y_full-5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

                            if (side != last_detection["side"] or (time.time()-last_detection["time"]) > 0.3):
                                if msg_serial is None:
                                    msg_serial = f"Area: {cor}\nCentro: {cx_full}\nLado: {side}\n"
                                last_detection = {"time": time.time(), "side": side, "cmd": None}

                        if gravador_usb: gravador_usb.write(hud_frame)
                        dash.atualizar_frame_imx179(hud_frame)
                        dash.atualizar_estado(modo=modo_atual, fps_imx179=round(1/(time.time()-start_time+1e-4), 1))
                except Exception as e:
                    print(f"[TRIANGULO] Erro captura USB: {e}")

        if msg_serial and ser is not None:
            ser.write(msg_serial.encode())
            fps_a = round(1/(time.time()-start_time+1e-4), 1)
            print(f"[EV3] ← '{msg_serial.strip()}' | FPS:{fps_a}")
            dash.atualizar_estado(log={"msg": f"EV3 ← {msg_serial.strip()}", "tipo": "ok"})

except KeyboardInterrupt:
    print("\n[*] Encerrando...")
finally:
    parar_imx500()
    parar_imx179()
    if ser and ser.is_open: ser.close()