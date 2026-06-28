import time
import cv2
import serial
import os
import numpy as np
import math
import threading
import queue
import dashboard_server as dash

# ── env anti-travamento ──────────────────────────────────────────
os.environ["YOLO_VERBOSE"]         = "False"
os.environ["OMP_NUM_THREADS"]      = "1"
os.environ["MKL_NUM_THREADS"]      = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
cv2.setNumThreads(0)

from picamera2 import Picamera2
import smbus2

# ── caminhos de modelo ───────────────────────────────────────────
BALL_PT_PATH   = "modelo/ball_detect_s.pt"
SILVER_PT_PATH = "modelo/silver_classify_s.pt"

# ══════════════════════════════════════════════════════════════════
#  YOLO CPU — modelo de bolas
# ══════════════════════════════════════════════════════════════════
yolo_ball_cpu = None
try:
    from ultralytics import YOLO
    print(f"[*] CPU: carregando {BALL_PT_PATH}...")
    yolo_ball_cpu = YOLO(BALL_PT_PATH)
    print("[+] YOLO CPU (bolas): carregado ✓")
except Exception as _e:
    print(f"[AVISO] Sem modelo de bolas: {_e}")

# ── modelo prata (classificação, CPU leve) ───────────────────────
yolo_silver       = None
yolo_silver_ativo = False
try:
    from ultralytics import YOLO as _YOLO
    yolo_silver       = _YOLO(SILVER_PT_PATH)
    yolo_silver_ativo = True
    print(f"[+] Silver classify: {SILVER_PT_PATH} ✓")
except Exception as _e:
    print(f"[AVISO] Modelo silver não carregado: {_e}")

# ══════════════════════════════════════════════════════════════════
#  MPU6050 (GIROSCÓPIO)
# ══════════════════════════════════════════════════════════════════
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
    print("[+] MPU6050 via I2C ✓")
except Exception as e:
    print(f"[AVISO] MPU6050 não encontrado: {e}")
    mpu_ativo = False

def ler_mpu(reg):
    if not mpu_ativo: return 0.0
    try:
        h = bus.read_byte_data(MPU_ADDR, reg)
        l = bus.read_byte_data(MPU_ADDR, reg + 1)
        v = (h << 8) | l
        if v > 32768: v -= 65536
        return float(v)
    except:
        return 0.0

# ══════════════════════════════════════════════════════════════════
#  SERIAL EV3
# ══════════════════════════════════════════════════════════════════
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    print("[+] Serial EV3 ✓")
except Exception as e:
    print(f"[AVISO] Serial não disponível: {e}")
    ser = None

# ══════════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES DE CÂMERA E VISÃO
# ══════════════════════════════════════════════════════════════════
W, H     = 320, 240
CENTRO_X = W // 2

# ── Cores ────────────────────────────────────────────────────────
BLACK_MIN        = np.array([0,   0,   0])
BLACK_MAX_BOTTOM = np.array([180, 255, 70])
BLACK_MAX_TOP    = np.array([180, 255, 55])
GREEN_MIN        = np.array([40,  80,  40])
GREEN_MAX        = np.array([90,  255, 255])

SILVER_REFLECT_HSV_MIN  = np.array([0,   0,  170])
SILVER_REFLECT_HSV_MAX  = np.array([180, 20, 255])
SILVER_REFLECT_MIN_AREA = 1500
SILVER_MATTE_HSV_MIN    = np.array([0,   0,   80])
SILVER_MATTE_HSV_MAX    = np.array([180, 15,  185])
SILVER_MATTE_MIN_AREA   = 2500
SILVER_MIN_WIDTH_RATIO  = 0.25
RESGATE_BLACK_MIN_AREA  = 2000

# ── Bolas (CPU) ──────────────────────────────────────────────────
BALL_CONF_MIN     = 0.55
BALL_AREA_MIN     = 400
BALL_AREA_MAX     = 20000
BALL_PROP_MIN     = 0.35
BALL_PROP_MAX     = 2.50
BALL_MARGEM_BORDA = 0.05
BALL_DEBUG        = True
DEBUG_FILTROS     = True

# ── Silver AI ────────────────────────────────────────────────────
SILVER_INFER_INTERVALO = 7
SILVER_AI_THRESHOLD    = 0.50

# ══════════════════════════════════════════════════════════════════
#  GRAVAÇÃO DVR
# ══════════════════════════════════════════════════════════════════
DEBUG_DIR = "debug_videos"
os.makedirs(DEBUG_DIR, exist_ok=True)
gravador_500 = None

# ══════════════════════════════════════════════════════════════════
#  CÂMERA IMX500 — RGB888 (cores corretas, vermelho = vermelho)
# ══════════════════════════════════════════════════════════════════
picam2 = None

def iniciar_imx500():
    global picam2, gravador_500
    if picam2 is not None:
        return
    print("[*] Ligando câmera IMX500 (RGB888, sem NPU)...")
    try:
        picam2 = Picamera2()
        cfg = picam2.create_video_configuration(
            main={"format": "RGB888", "size": (W, H)})
        picam2.configure(cfg)
        picam2.start()
        nome   = time.strftime("%Y%m%d_%H%M%S")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        gravador_500 = cv2.VideoWriter(
            f"{DEBUG_DIR}/imx500_{nome}.avi", fourcc, 20.0, (W, H))
        time.sleep(1)
        print("[+] Câmera IMX500 ativa (RGB888, CPU inference) ✓")
    except Exception as e:
        print(f"[ERRO] IMX500: {e}")
        picam2 = None

def parar_imx500():
    global picam2, gravador_500
    if picam2:
        print("[*] Desligando câmera...")
        try: picam2.stop(); picam2.close()
        except: pass
        picam2 = None
    if gravador_500:
        try: gravador_500.release()
        except: pass
        gravador_500 = None

# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE PRATA — mantida para uso futuro
# ══════════════════════════════════════════════════════════════════
_silver_counter        = 0
_silver_confianca      = 0.0
_contador_frames_prata = 0

def _detectar_silver_visao(frame_bgr):
    blur = cv2.GaussianBlur(frame_bgr, (5, 5), 0)
    hsv  = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    k3   = np.ones((3, 3), np.uint8)
    k9   = np.ones((9, 9), np.uint8)
    mask_r = cv2.inRange(hsv, SILVER_REFLECT_HSV_MIN, SILVER_REFLECT_HSV_MAX)
    mask_r = cv2.erode(mask_r,  k3, iterations=2)
    mask_r = cv2.dilate(mask_r, k9, iterations=3)
    mask_r = cv2.erode(mask_r,  k3, iterations=1)
    mask_m = cv2.inRange(hsv, SILVER_MATTE_HSV_MIN, SILVER_MATTE_HSV_MAX)
    mask_m = cv2.subtract(mask_m, mask_r)
    mask_m = cv2.erode(mask_m,  k3, iterations=3)
    mask_m = cv2.dilate(mask_m, k9, iterations=4)
    mask_m = cv2.erode(mask_m,  k3, iterations=2)
    for mask, min_area in [(mask_r, SILVER_REFLECT_MIN_AREA), (mask_m, SILVER_MATTE_MIN_AREA)]:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) < min_area: continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w < (W * SILVER_MIN_WIDTH_RATIO): continue
            if h > 0 and float(w) / h < 1.5: continue
            return True
    return False

def detectar_prata(frame_bgr):
    global _silver_counter, _silver_confianca, _contador_frames_prata
    if frame_bgr is None or frame_bgr.size == 0:
        return False
    prata_ai = False
    if yolo_silver_ativo and yolo_silver is not None:
        _silver_counter += 1
        if _silver_counter >= SILVER_INFER_INTERVALO:
            _silver_counter = 0
            try:
                f96  = cv2.resize(frame_bgr, (96, 96))
                res  = yolo_silver.predict(f96, imgsz=96, verbose=False, device='cpu')
                nome = res[0].names[int(res[0].probs.top1)].lower()
                conf = float(res[0].probs.top1conf)
                if ("prata" in nome or "silver" in nome) and conf > SILVER_AI_THRESHOLD:
                    _silver_confianca = conf
                    _contador_frames_prata += 1
                else:
                    _silver_confianca = 0.0
                    _contador_frames_prata = max(0, _contador_frames_prata - 1)
                prata_ai = (_contador_frames_prata >= 3)
            except:
                pass
    prata_visao = _detectar_silver_visao(frame_bgr)
    return prata_ai or prata_visao

# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE OBSTÁCULO (ROI central, visão computacional)
# ══════════════════════════════════════════════════════════════════
_obst_acum = None

def detectar_obstaculo(frame_bgr):
    """Detecta obstáculos usando bordas, sombra e textura homogênea."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges    = cv2.Canny(blur, 30, 100)
    cx1, cx2 = int(W * 0.25), int(W * 0.75)
    cy2      = int(H * 0.80)
    proj     = np.sum(edges[0:cy2, cx1:cx2], axis=0)
    tem_bordas = (np.max(proj) if len(proj) else 0) > (H * 0.80 * 255 * 0.10)
    roi_s  = frame_bgr[int(H*0.55):H, int(W*0.20):int(W*0.80)]
    hsv_s  = cv2.cvtColor(roi_s, cv2.COLOR_BGR2HSV)
    mask_s = cv2.inRange(hsv_s, np.array([0, 0, 0]), np.array([180, 255, 60]))
    area_s = roi_s.shape[0] * roi_s.shape[1]
    tem_sombra = (cv2.countNonZero(mask_s) / area_s if area_s > 0 else 0) >= 0.12
    roi_b = frame_bgr[int(H*0.05):int(H*0.75), int(W*0.25):int(W*0.75)]
    if roi_b.size > 0:
        std_b  = np.std(roi_b.astype(np.float32))
        mean_b = np.mean(roi_b)
        tem_bloco = (60 < mean_b < 220) and (std_b < 55)
    else:
        tem_bloco = False
    score = int(tem_bordas) + int(tem_sombra) + int(tem_bloco)
    return score >= 2, score / 3.0


def processar_obstaculo_com_hud(frame_bgr, hud):
    """Aplica histerese e desenha overlay no hud."""
    global _obst_acum
    detectado, pct = detectar_obstaculo(frame_bgr)
    mask_atual = np.full(frame_bgr.shape[:2], 255 if detectado else 0, dtype=np.uint8)
    if _obst_acum is None:
        _obst_acum = np.zeros_like(mask_atual, dtype=np.float32)
    _obst_acum = cv2.addWeighted(_obst_acum, 0.85,
                                  mask_atual.astype(np.float32), 0.15, 0)
    _, mask_limpa = cv2.threshold(_obst_acum, 200, 255, cv2.THRESH_BINARY)
    mask_limpa = mask_limpa.astype(np.uint8)
    if cv2.countNonZero(mask_limpa) > 500:
        overlay = hud.copy()
        overlay[mask_limpa > 0] = (40, 90, 180)
        cv2.addWeighted(overlay, 0.35, hud, 0.65, 0, hud)
        cv2.putText(hud, "OBSTACULO", (10, H - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 100, 255), 1)
    return cv2.countNonZero(mask_limpa) > 500, pct

# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE FITAS — mantida para uso futuro
# ══════════════════════════════════════════════════════════════════
_last_send_resgate = {"prata": 0.0, "preta": 0.0}
RESGATE_COOLDOWN   = 0.8

def _mask_black(frame_bgr):
    mask_bot = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_BOTTOM)
    mask_top = cv2.inRange(frame_bgr, BLACK_MIN, BLACK_MAX_TOP)
    split = int(H * 0.40)
    mask  = mask_bot.copy()
    mask[0:split, :] = mask_top[0:split, :]
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, GREEN_MIN, GREEN_MAX)
    mask = cv2.subtract(mask, mask_green)
    k = np.ones((3, 3), np.uint8)
    mask = cv2.erode(mask,  k, iterations=5)
    mask = cv2.dilate(mask, k, iterations=17)
    mask = cv2.erode(mask,  k, iterations=9)
    return mask

def monitorar_fitas_resgate(frame_bgr):
    """Mantida para uso futuro — não chamada nos modos ativos."""
    hud   = frame_bgr.copy()
    agora = time.time()
    msg   = None
    blur     = cv2.GaussianBlur(frame_bgr, (5, 5), 0)
    prata_ok = detectar_prata(blur)
    mask_black = _mask_black(blur)
    cnts_black, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    preta_ok = False
    for cnt in cnts_black:
        if cv2.contourArea(cnt) > RESGATE_BLACK_MIN_AREA:
            preta_ok = True
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 0, 0), 2)
    if prata_ok and (agora - _last_send_resgate["prata"]) > RESGATE_COOLDOWN:
        msg = "prata visivel\n"
        _last_send_resgate["prata"] = agora
    elif preta_ok and not prata_ok and (agora - _last_send_resgate["preta"]) > RESGATE_COOLDOWN:
        msg = "preta visivel\n"
        _last_send_resgate["preta"] = agora
    return msg, hud, prata_ok, preta_ok

# ══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE BOLAS — YOLO .pt na CPU
# ══════════════════════════════════════════════════════════════════

def _parse_cpu_detections(frame_bgr, frame_w, frame_h):
    """Parse com debug detalhado de cada rejeição."""
    dets = []
    if yolo_ball_cpu is None:
        return dets
    try:
        results = yolo_ball_cpu.predict(frame_bgr, imgsz=160,
                                        device='cpu', half=False,
                                        verbose=False, conf=BALL_CONF_MIN)[0]
        if not results.boxes:
            if DEBUG_FILTROS:
                print(f"[YOLO] Nenhuma detecção acima de conf {BALL_CONF_MIN}")
            return dets

        for idx, b in enumerate(results.boxes):
            conf = b.conf.item()
            x1n, y1n, x2n, y2n = b.xyxyn[0].tolist()
            x1 = int(x1n * frame_w); y1 = int(y1n * frame_h)
            x2 = int(x2n * frame_w); y2 = int(y2n * frame_h)
            cls_id   = int(b.cls.item())
            cls_name = yolo_ball_cpu.names[cls_id]

            dets.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                         "conf": conf, "cls_id": cls_id, "cls_name": cls_name})

            if DEBUG_FILTROS:
                print(f"[YOLO] Det #{idx}: {cls_name} conf={conf:.3f} bbox=({x1},{y1},{x2},{y2})")
    except Exception as _e:
        print(f"[CPU DET ERROR] {_e}")
    return dets


def filtrar_melhor_bola(dets, frame_w, frame_h):
    """Filtra com debug detalhado de por que cada detecção é rejeitada."""
    melhor      = None
    melhor_area = 0

    if not dets and DEBUG_FILTROS:
        print(f"[FILTER] Nenhuma detecção para filtrar")
        return None

    for d_idx, d in enumerate(dets):
        larg = d["x2"] - d["x1"]
        alt = d["y2"] - d["y1"]
        area = larg * alt
        prop = float(larg) / alt if alt > 0 else 0

        if DEBUG_FILTROS:
            print(f"[FILTER] Det #{d_idx} {d['cls_name']}: area={area}, prop={prop:.2f}")

        if area < BALL_AREA_MIN or area > BALL_AREA_MAX:
            if DEBUG_FILTROS:
                print(f"  ✗ REJEITADO: área fora do range [{BALL_AREA_MIN}, {BALL_AREA_MAX}]")
            continue

        if not (BALL_PROP_MIN <= prop <= BALL_PROP_MAX):
            if DEBUG_FILTROS:
                print(f"  ✗ REJEITADO: proporção {prop:.2f} fora do range [{BALL_PROP_MIN}, {BALL_PROP_MAX}]")
            continue

        if d["x1"] <= 2 or d["y1"] <= 2:
            if DEBUG_FILTROS:
                print(f"  ✗ REJEITADO: muito perto da borda superior/esquerda")
            continue
        if d["x2"] >= frame_w - 2 or d["y2"] >= frame_h - 2:
            if DEBUG_FILTROS:
                print(f"  ✗ REJEITADO: muito perto da borda inferior/direita")
            continue

        mx = int(frame_w * BALL_MARGEM_BORDA)
        my = int(frame_h * BALL_MARGEM_BORDA)
        cx = d["x1"] + larg // 2
        cy = d["y1"] + alt // 2
        if cx < mx or cx > frame_w - mx or cy < my or cy > frame_h - my:
            if DEBUG_FILTROS:
                print(f"  ✗ REJEITADO: fora da margem central")
            continue

        if DEBUG_FILTROS:
            print(f"  ✓ ACEITO! Será candidato (área={area})")

        if area > melhor_area:
            melhor_area = area
            melhor = d

    if melhor and DEBUG_FILTROS:
        print(f"[FILTER] ✓ MELHOR BOLA SELECIONADA: {melhor['cls_name']} (área={melhor_area})")
    elif DEBUG_FILTROS:
        print(f"[FILTER] ✗ NENHUMA BOLA PASSOU NOS FILTROS")

    return melhor

# ══════════════════════════════════════════════════════════════════
#  THREAD DE INFERÊNCIA YOLO
# ══════════════════════════════════════════════════════════════════
_fila_frames    = queue.Queue(maxsize=1)
_fila_resultado = queue.Queue(maxsize=1)

def _worker_yolo():
    while True:
        try:
            frame = _fila_frames.get(timeout=1.0)
        except queue.Empty:
            continue
        try:
            dets   = _parse_cpu_detections(frame, frame.shape[1], frame.shape[0])
            melhor = filtrar_melhor_bola(dets, frame.shape[1], frame.shape[0])
            try:
                _fila_resultado.get_nowait()
            except queue.Empty:
                pass
            _fila_resultado.put((dets, melhor))
        except Exception as e:
            print(f"[YOLO WORKER] {e}")

_thread_yolo = threading.Thread(target=_worker_yolo, daemon=True)
_thread_yolo.start()
print("[+] Thread YOLO iniciada ✓")

# ══════════════════════════════════════════════════════════════════
#  CALIBRAÇÃO MPU6050
# ══════════════════════════════════════════════════════════════════
offset_roll        = 0.0
guinada_yaw        = 0.0
rotacao_roll       = 0.0
arfagem_pitch      = 0.0
tempo_anterior_mpu = time.time()
tempo_ultimo_print = time.time()

if mpu_ativo:
    print("[*] Calibrando MPU6050...")
    soma = 0.0
    for _ in range(50):
        ay = ler_mpu(ACCEL_YOUT) / 16384.0
        az = ler_mpu(ACCEL_ZOUT) / 16384.0
        soma += math.degrees(math.atan2(ay, az))
        time.sleep(0.02)
    offset_roll = soma / 50.0
    print(f"[+] Offset Roll: {offset_roll:.2f}°")

# ══════════════════════════════════════════════════════════════════
#  MODO LINHA_GAP — CONFIGURAÇÕES DO ROI CIRCULAR
# ══════════════════════════════════════════════════════════════════
LINHA_GAP_RAIO     = int(min(W, H) * 0.36)
LINHA_GAP_CX       = W // 2
LINHA_GAP_CY       = int(H * 0.70)
LINHA_GAP_AREA_MIN = 800
LINHA_GAP_DESVIO   = W * 0.12

_linha_gap_historico: list = []

def processar_linha_gap(frame_rgb):
    """
    Detecta contorno da linha preta dentro de ROI circular.
    Quando gap detectado, calcula ângulo da borda superior da linha
    para reposicionamento (técnica minAreaRect, como no PDF de referência).

    Retorna
    -------
    cmd : str
        'linha centro' | 'linha esquerda' | 'linha direita' |
        'gap' | 'gap angulo <graus>'
    hud : np.ndarray
        Frame anotado (RGB).
    gap_estavel : bool
        True quando linha sumiu por >= 5 dos últimos 8 frames.
    angulo_gap : float | None
        Ângulo em graus da borda superior da linha antes do gap.
        None se não disponível.
    """
    global _linha_gap_historico

    hud   = frame_rgb.copy()
    h_f, w_f = frame_rgb.shape[:2]

    # ── 1. Máscara circular ───────────────────────────────────────
    mask_circulo = np.zeros((h_f, w_f), dtype=np.uint8)
    cv2.circle(mask_circulo, (LINHA_GAP_CX, LINHA_GAP_CY),
               LINHA_GAP_RAIO, 255, -1)

    # ── 2. Threshold de preto ─────────────────────────────────────
    blur = cv2.GaussianBlur(frame_rgb, (5, 5), 0)
    hsv  = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)
    split = int(h_f * 0.40)
    mask_bot = cv2.inRange(hsv, np.array([0, 0,  0]), np.array([180, 255, 70]))
    mask_top = cv2.inRange(hsv, np.array([0, 0,  0]), np.array([180, 255, 55]))
    mask_preta = mask_bot.copy()
    mask_preta[0:split, :] = mask_top[0:split, :]

    # ── 3. Morfologia ─────────────────────────────────────────────
    k = np.ones((3, 3), np.uint8)
    mask_preta = cv2.erode (mask_preta, k, iterations=3)
    mask_preta = cv2.dilate(mask_preta, k, iterations=5)
    mask_preta = cv2.erode (mask_preta, k, iterations=2)

    # ── 4. ROI circular ───────────────────────────────────────────
    mask_preta = cv2.bitwise_and(mask_preta, mask_circulo)

    # ── 5. Contornos ──────────────────────────────────────────────
    cnts, _ = cv2.findContours(mask_preta, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

    gap_detectado = True
    cmd           = "gap"
    angulo_gap    = None          # ângulo calculado via minAreaRect

    if cnts:
        maior = max(cnts, key=cv2.contourArea)
        area  = cv2.contourArea(maior)

        if area >= LINHA_GAP_AREA_MIN:
            gap_detectado = False

            # ── minAreaRect → ângulo da linha ─────────────────────
            rect        = cv2.minAreaRect(maior)
            centro_rect = (int(rect[0][0]), int(rect[0][1]))
            (rw, rh)    = rect[1]
            angulo_raw  = rect[2]          # OpenCV: -90 a 0

            # Normaliza: ângulo do lado LONGO do retângulo vs horizontal
            if rw < rh:
                angulo_norm = angulo_raw + 90.0   # lado longo é o eixo "altura"
            else:
                angulo_norm = angulo_raw           # lado longo já é horizontal

            # Centraliza em -90..+90  →  negativo = inclinado esq, positivo = dir
            if angulo_norm > 90:
                angulo_norm -= 180.0

            angulo_gap = round(angulo_norm, 1)

            # Desenha minAreaRect em azul (RGB: 100, 180, 255)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(hud, [box], 0, (100, 180, 255), 2)

            # Contorno em amarelo
            cv2.drawContours(hud, [maior], -1, (255, 220, 0), 1)

            # Linha do eixo do retângulo (mostra ângulo visualmente)
            # Pega os 2 pontos do topo do box (menor y)
            box_sorted = sorted(box, key=lambda p: p[1])
            p1, p2 = tuple(box_sorted[0]), tuple(box_sorted[1])
            cv2.line(hud, p1, p2, (0, 80, 255), 2)   # azul escuro = borda superior

            # Centróide para decisão lateral
            M = cv2.moments(maior)
            if M["m00"] > 0:
                alvo_x = int(M["m10"] / M["m00"])
                alvo_y = int(M["m01"] / M["m00"])
                cv2.circle(hud, (alvo_x, alvo_y), 6, (255, 255, 0), -1)
                cv2.line(hud,
                         (LINHA_GAP_CX, LINHA_GAP_CY),
                         (alvo_x, alvo_y), (255, 60, 60), 2)

                desvio = alvo_x - LINHA_GAP_CX
                if   desvio < -LINHA_GAP_DESVIO: cmd = "linha esquerda"
                elif desvio >  LINHA_GAP_DESVIO: cmd = "linha direita"
                else:                             cmd = "linha centro"

            # Exibe ângulo no HUD
            cv2.putText(hud, f"{angulo_gap:.1f}deg",
                        (centro_rect[0] - 30, centro_rect[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)

    # ── 6. Histórico de gap ───────────────────────────────────────
    _linha_gap_historico.append(0 if gap_detectado else 1)
    if len(_linha_gap_historico) > 8:
        _linha_gap_historico.pop(0)
    gap_estavel = (len(_linha_gap_historico) >= 5 and
                   sum(_linha_gap_historico) < 3)

    # ── 7. Escurece fora do círculo ───────────────────────────────
    outside   = cv2.bitwise_not(mask_circulo)
    hud_float = hud.astype(np.float32)
    hud_float[outside > 0] = (hud_float[outside > 0] * 0.28)
    hud = np.clip(hud_float, 0, 255).astype(np.uint8)

    # ── 8. Círculo ROI ────────────────────────────────────────────
    cor_circulo = (255, 60, 60) if gap_estavel else (60, 255, 100)
    cv2.circle(hud, (LINHA_GAP_CX, LINHA_GAP_CY),
               LINHA_GAP_RAIO, cor_circulo, 2)
    tam_cruz = 8
    cv2.line(hud,
             (LINHA_GAP_CX - tam_cruz, LINHA_GAP_CY),
             (LINHA_GAP_CX + tam_cruz, LINHA_GAP_CY), cor_circulo, 1)
    cv2.line(hud,
             (LINHA_GAP_CX, LINHA_GAP_CY - tam_cruz),
             (LINHA_GAP_CX, LINHA_GAP_CY + tam_cruz), cor_circulo, 1)

    # ── 9. Status text ────────────────────────────────────────────
    if gap_estavel:
        status_txt = f"GAP! ang={angulo_gap}deg" if angulo_gap is not None else "GAP!"
    else:
        status_txt = cmd.upper()
    cv2.putText(hud, status_txt, (10, h_f - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, cor_circulo, 2)

    # ── 10. Comando serial final ──────────────────────────────────
    if gap_estavel:
        if angulo_gap is not None:
            cmd_final = f"gap angulo {angulo_gap}"
        else:
            cmd_final = "gap"
    else:
        cmd_final = cmd

    return cmd_final, hud, gap_estavel, angulo_gap

# ══════════════════════════════════════════════════════════════════
#  VARIÁVEIS DE CONTROLE GLOBAL
# ══════════════════════════════════════════════════════════════════
modo_atual             = "bolas"
estado_obstaculo       = "idle"
last_detection         = {"time": 0.0, "side": None, "cmd": None}
ultimo_aviso_obstaculo = 0.0
COOLDOWN_OBSTACULO     = 3.0

# ══════════════════════════════════════════════════════════════════
#  CALLBACKS DASHBOARD
# ══════════════════════════════════════════════════════════════════

def ao_mudar_modo(novo_modo):
    global modo_atual, estado_obstaculo, _obst_acum, _linha_gap_historico
    print(f"[WEB] Modo → {novo_modo}")
    modo_atual = novo_modo
    estado_obstaculo = "idle"
    _obst_acum = None
    _linha_gap_historico = []   # limpa histórico ao trocar de modo
    dash.atualizar_estado(modo=modo_atual, obstaculo="idle",
                          log={"msg": f"Modo → {novo_modo}", "tipo": "ok"})

def ao_emergencia():
    print("[WEB] EMERGÊNCIA!")
    if ser: ser.write(b"emergencia\n")

def ao_reset_gyro():
    global guinada_yaw
    guinada_yaw = 0.0
    dash.atualizar_estado(log={"msg": "Gyro resetado.", "tipo": "info"})

dash.registrar_callbacks(fn_modo=ao_mudar_modo,
                         fn_emergencia=ao_emergencia,
                         fn_reset_gyro=ao_reset_gyro)
dash.iniciar_servidor()

dash.atualizar_estado(
    npu_ativo=False,
    npu_modelo=os.path.basename(BALL_PT_PATH),
)

# ══════════════════════════════════════════════════════════════════
#  INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════════
print("[+] SISTEMA INICIADO")
print("[!] DEBUG_FILTROS ativo - verifique os logs para detecções")
iniciar_imx500()
dash.atualizar_estado(
    modo=modo_atual,
    log={"msg": "Boot OK. IMX500 ativa (RGB888). Modos: bolas | triangulo | obstaculo | linha_gap | nadapross", "tipo": "info"}
)

# ══════════════════════════════════════════════════════════════════
#  LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════
try:
    while True:
        loop_start = time.time()
        msg_serial = None

        # ── MPU6050 ────────────────────────────────────────────
        if mpu_ativo:
            now_mpu = time.time()
            dt_mpu  = now_mpu - tempo_anterior_mpu
            tempo_anterior_mpu = now_mpu
            ax = ler_mpu(ACCEL_XOUT) / 16384.0
            ay = ler_mpu(ACCEL_YOUT) / 16384.0
            az = ler_mpu(ACCEL_ZOUT) / 16384.0
            arfagem_pitch = -math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
            rotacao_roll  =  math.degrees(math.atan2(ay, az)) - offset_roll
            gz = ler_mpu(GYRO_ZOUT) / 131.0
            if abs(gz) > 1.0: guinada_yaw += gz * dt_mpu
            if (now_mpu - tempo_ultimo_print) > 0.5:
                if ser: ser.write(f"MPU_Z:{guinada_yaw:.1f}\n".encode())
                if ser: ser.write(f"MPU_Y:{arfagem_pitch:.1f}\n".encode())
                if ser: ser.write(f"MPU_X:{rotacao_roll:.1f}\n".encode())
                tempo_ultimo_print = now_mpu
                dash.atualizar_estado(
                    gyro_roll=round(rotacao_roll, 1),
                    gyro_pitch=round(arfagem_pitch, 1),
                    gyro_yaw=round(guinada_yaw, 1))

        # ── Recebe comandos do EV3 via serial ──────────────────
        if ser and ser.in_waiting:
            cmd = ser.read(ser.in_waiting).decode('ascii', 'ignore').strip().lower()
            print(f"[EV3] → '{cmd}'")
            if "bolas" in cmd or "resgate_on" in cmd:
                if modo_atual != "bolas":
                    ao_mudar_modo("bolas")
                    dash.atualizar_estado(log={"msg": "EV3: modo bolas.", "tipo": "info"})
            elif "triangulo" in cmd:
                if modo_atual != "triangulo":
                    ao_mudar_modo("triangulo")
                    dash.atualizar_estado(log={"msg": "EV3: modo triângulo.", "tipo": "info"})
            elif "linha_gap" in cmd:
                if modo_atual != "linha_gap":
                    ao_mudar_modo("linha_gap")
                    dash.atualizar_estado(log={"msg": "EV3: modo linha_gap.", "tipo": "info"})
            elif "nadapross" in cmd:
                if modo_atual != "nadapross":
                    ao_mudar_modo("nadapross")
                    dash.atualizar_estado(log={"msg": "EV3: modo nadapross.", "tipo": "info"})
            elif "obstaculo" in cmd and "confirma" not in cmd and "nega" not in cmd:
                if modo_atual != "obstaculo":
                    ao_mudar_modo("obstaculo")
                    dash.atualizar_estado(log={"msg": "EV3: modo obstáculo.", "tipo": "info"})
            elif "confirma obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "verificando"
                dash.atualizar_estado(obstaculo=estado_obstaculo,
                                      log={"msg": "EV3 confirmou obstáculo.", "tipo": "warn"})
            elif "nega obstaculo" in cmd and estado_obstaculo == "aguardando_confirmacao":
                estado_obstaculo = "idle"
                ultimo_aviso_obstaculo = time.time()
                dash.atualizar_estado(obstaculo=estado_obstaculo,
                                      log={"msg": "EV3 negou obstáculo.", "tipo": "info"})

        # ── Captura IMX500 ─────────────────────────────────────
        if picam2 is None:
            time.sleep(0.05)
            continue

        try:
            frame = picam2.capture_array("main")
            frame = cv2.flip(frame, -1)
            # Picamera2 RGB888 entrega bytes BGR na memória — converte para RGB real
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hud   = frame.copy()
            h_f, w_f = frame.shape[:2]
        except Exception as e:
            print(f"[CAPTURA] {e}")
            time.sleep(0.05)
            continue

        # ══════════════════════════════════════════════════════
        # MODO BOLAS — YOLO assíncrono via thread
        # ══════════════════════════════════════════════════════
        if modo_atual == "bolas":
            try:
                _fila_frames.get_nowait()
            except queue.Empty:
                pass
            try:
                _fila_frames.put_nowait(frame.copy())
            except queue.Full:
                pass

            dets   = []
            melhor = None
            try:
                dets, melhor = _fila_resultado.get_nowait()
            except queue.Empty:
                pass

            if BALL_DEBUG and dets:
                for d in dets:
                    cv2.rectangle(hud, (d["x1"],d["y1"]), (d["x2"],d["y2"]), (80,80,80), 1)
                    cv2.putText(hud, f"{d['cls_name']} {d['conf']:.2f}",
                                (d["x1"], max(d["y1"]-3, 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.28, (200,200,0), 1)

            if melhor is not None:
                larg  = melhor["x2"] - melhor["x1"]
                alt   = melhor["y2"] - melhor["y1"]
                cx    = melhor["x1"] + larg // 2
                cy    = melhor["y1"] + alt  // 2
                area  = larg * alt
                side  = ("esquerda" if cx < (w_f // 3)
                         else "direita" if cx > (2 * w_f // 3)
                         else "meio")
                cls   = melhor["cls_name"]
                cor_b = (180,180,180) if "silver" in cls.lower() else (40,40,40)
                cv2.rectangle(hud, (melhor["x1"],melhor["y1"]),
                                   (melhor["x2"],melhor["y2"]), cor_b, 2)
                cv2.circle(hud, (cx, cy), 5, (255,255,255), -1)
                cv2.putText(hud, f"{cls} {side} {melhor['conf']:.2f}",
                            (melhor["x1"], max(melhor["y1"]-6,10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, cor_b, 1)
                agora = time.time()
                if (side != last_detection["side"] or (agora - last_detection["time"]) > 0.3):
                    msg_serial = f"Detected: {cls}\nArea: {area}px\nLado: {side}\n"
                    last_detection = {"time": agora, "side": side, "cmd": None}

        # ══════════════════════════════════════════════════════
        # MODO TRIÂNGULO
        # ══════════════════════════════════════════════════════
        elif modo_atual == "triangulo":
            r = frame[:, :, 0].astype(np.int16)
            g = frame[:, :, 1].astype(np.int16)
            b = frame[:, :, 2].astype(np.int16)

            mask_red = np.zeros(frame.shape[:2], dtype=np.uint8)
            mask_red[(r > 100) & (r > g + 30) & (r > b + 30)] = 255

            hsv_resgate = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            mask_green_resg = cv2.inRange(hsv_resgate, GREEN_MIN, GREEN_MAX)

            if int(loop_start * 10) % 10 == 0:
                px_r, px_g, px_b = r[h_f//2, w_f//2], g[h_f//2, w_f//2], b[h_f//2, w_f//2]
                roi_r = r[int(h_f*0.2):int(h_f*0.8), int(w_f*0.1):int(w_f*0.9)]
                roi_g = g[int(h_f*0.2):int(h_f*0.8), int(w_f*0.1):int(w_f*0.9)]
                roi_b = b[int(h_f*0.2):int(h_f*0.8), int(w_f*0.1):int(w_f*0.9)]
                print(f"[RGB] centro=R{px_r} G{px_g} B{px_b} | "
                      f"roi R:{roi_r.min()}-{roi_r.max()} "
                      f"G:{roi_g.min()}-{roi_g.max()} "
                      f"B:{roi_b.min()}-{roi_b.max()} | "
                      f"pixels_vermelhos={cv2.countNonZero(mask_red)}")

            mask_areas = cv2.bitwise_or(mask_red, mask_green_resg)
            contours, _ = cv2.findContours(mask_areas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if int(loop_start * 30) % 30 == 0:
                print(f"[TRI] {len(contours)} contornos encontrados")

            for cnt in contours:
                area_cnt = cv2.contourArea(cnt)
                if area_cnt < 300:
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                if h == 0:
                    continue
                proporcao = float(w) / h

                if area_cnt > 300:
                    print(f"[TRI] cnt area={area_cnt:.0f} w={w} h={h} prop={proporcao:.2f} pos=({x},{y})")

                if w < int(w_f * 0.08):
                    continue

                centro_x = x + (w // 2)
                centro_y = y + (h // 2)
                cor_nome = "Vermelho" if mask_red[centro_y, centro_x] > 0 else "Verde"

                side = ("esquerda" if centro_x < (w_f // 3)
                        else "direita" if centro_x > (2 * w_f // 3)
                        else "meio")

                cor_rect = (0, 0, 255) if cor_nome == "Vermelho" else (0, 255, 0)
                cv2.rectangle(hud, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.rectangle(hud, (x+2, y+2), (x+w-2, y+h-2), cor_rect, -1)
                cv2.putText(hud, f"{cor_nome} {side}",
                            (x, max(y-5, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

                print(f"[TRI] ✓ DETECTADO: {cor_nome} {side} prop={proporcao:.2f}")

                agora = time.time()
                if (side != last_detection["side"] or
                        (agora - last_detection["time"]) > 0.3):
                    if msg_serial is None:
                        msg_serial = f"Area: {cor_nome}\nCentro: {centro_x}\nLado: {side}\n"
                    last_detection = {"time": agora, "side": side, "cmd": None}

        # ══════════════════════════════════════════════════════
        # MODO OBSTÁCULO
        # ══════════════════════════════════════════════════════
        elif modo_atual == "obstaculo":
            agora = time.time()

            if estado_obstaculo == "idle":
                if (agora - ultimo_aviso_obstaculo) > COOLDOWN_OBSTACULO:
                    obst_det, pct = processar_obstaculo_com_hud(frame, hud)
                    dash.atualizar_estado(obst_pct=round(pct * 100, 1))
                    if obst_det:
                        msg_serial = "obstaculo detectado\n"
                        estado_obstaculo = "aguardando_confirmacao"
                        ultimo_aviso_obstaculo = agora
                        dash.atualizar_estado(
                            obstaculo=estado_obstaculo,
                            log={"msg": f"Obstáculo detectado! {pct*100:.0f}%", "tipo": "warn"})
                else:
                    processar_obstaculo_com_hud(frame, hud)

            elif estado_obstaculo == "aguardando_confirmacao":
                processar_obstaculo_com_hud(frame, hud)
                if (agora - ultimo_aviso_obstaculo) > 5.0:
                    estado_obstaculo = "idle"
                    ultimo_aviso_obstaculo = agora
                    dash.atualizar_estado(obstaculo=estado_obstaculo,
                                          log={"msg": "Timeout: sem confirmação EV3.", "tipo": "warn"})

            elif estado_obstaculo == "verificando":
                gray_v = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, mask_v = cv2.threshold(gray_v, 60, 255, cv2.THRESH_BINARY_INV)
                yi   = int(h_f * 0.50)
                esq  = mask_v[yi:, 0:int(w_f*0.35)]
                dir_ = mask_v[yi:, int(w_f*0.65):]
                a    = int(w_f*0.35) * int(h_f*0.50)
                te   = (cv2.countNonZero(esq)  / a) >= 0.08
                td   = (cv2.countNonZero(dir_) / a) >= 0.08
                if te and td:  res_lado = "linha ambos"
                elif te:       res_lado = "linha esquerda"
                elif td:       res_lado = "linha direita"
                else:          res_lado = "linha nenhum"
                msg_serial = f"{res_lado}\n"
                estado_obstaculo = "idle"
                ultimo_aviso_obstaculo = agora
                dash.atualizar_estado(
                    obstaculo=estado_obstaculo,
                    log={"msg": f"Verificação: {res_lado}", "tipo": "ok"})

        # ══════════════════════════════════════════════════════
        # MODO LINHA_GAP — contorno da linha preta + detecção de gap
        # ══════════════════════════════════════════════════════
        elif modo_atual == "linha_gap":
            cmd_linha, hud, gap, angulo = processar_linha_gap(frame)
            agora = time.time()

            if (cmd_linha != last_detection["cmd"] or
                    (agora - last_detection["time"]) > 0.3):
                msg_serial = f"{cmd_linha}\n"
                last_detection = {"time": agora, "side": None, "cmd": cmd_linha}
                print(f"[LINHA_GAP] cmd={cmd_linha} gap={gap} angulo={angulo}")

            dash.atualizar_estado(
                log={"msg": f"Linha: {cmd_linha}", "tipo": "warn" if gap else "ok"})
        # ══════════════════════════════════════════════════════
        # MODO NADAPROSS — câmera ligada, zero processamento
        # Útil para verificar visualmente a câmera sem enviar
        # nenhum comando ao EV3 e sem gastar CPU em visão.
        # ══════════════════════════════════════════════════════
        elif modo_atual == "nadapross":
            # Frame passa direto para o HUD sem qualquer análise.
            # Apenas exibe o label no canto para confirmar o modo.
            cv2.putText(hud, "NADAPROSS", (8, H - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)
            # msg_serial permanece None → nada é enviado ao EV3

        # ── Envia HUD para o dashboard ─────────────────────────
        if gravador_500:
            gravador_500.write(hud)
        dash.atualizar_frame_imx500(hud)

        fps = round(1.0 / (time.time() - loop_start + 1e-5), 1)
        dash.atualizar_estado(
            modo=modo_atual,
            fps_imx500=fps,
            obstaculo=estado_obstaculo)

        # ── Envia para EV3 ─────────────────────────────────────
        if msg_serial and ser is not None:
            ser.write(msg_serial.encode())
            print(f"[EV3] ← '{msg_serial.strip()}' | FPS:{fps}")
            dash.atualizar_estado(log={"msg": f"EV3 ← {msg_serial.strip()}", "tipo": "ok"})

except KeyboardInterrupt:
    print("\n[*] Encerrando...")
finally:
    parar_imx500()
    if ser and ser.is_open:
        ser.close()