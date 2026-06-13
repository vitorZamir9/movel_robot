from flask import Flask, Response, render_template_string, jsonify, request
import threading
import time

app = Flask(__name__)
_lock = threading.Lock()

_estado = {
    "modo": "bolas",
    "cmd_camera": "—",
    "obstaculo": "idle",
    "obst_pct": 0.0,          # percentual 0–100 do score de obstáculo
    "previsao_verde": "—",
    "bumper": "livre",
    "gyro_roll": 0.0,
    "gyro_pitch": 0.0,
    "gyro_yaw": 0.0,
    "fps_imx500": 0.0,
    # ── NPU ────────────────────────────────────────────────────
    "npu_ativo": False,
    "npu_modelo": "—",
    # ───────────────────────────────────────────────────────────
    "log": [],
    "uptime_start": time.time(),
    "ev3_conectado": True,
}

_frame_imx500 = None

_callback_modo       = None
_callback_emergencia = None
_callback_reset_gyro = None


def registrar_callbacks(fn_modo=None, fn_emergencia=None, fn_reset_gyro=None):
    global _callback_modo, _callback_emergencia, _callback_reset_gyro
    _callback_modo       = fn_modo
    _callback_emergencia = fn_emergencia
    _callback_reset_gyro = fn_reset_gyro


def atualizar_estado(**kwargs):
    with _lock:
        for k, v in kwargs.items():
            if k == "log":
                ts = time.strftime('%H:%M:%S')
                _estado["log"].append({"t": ts, "msg": v["msg"], "tipo": v.get("tipo", "info")})
                _estado["log"] = _estado["log"][-30:]
            else:
                _estado[k] = v


def atualizar_frame_imx500(frame_bgr):
    global _frame_imx500
    import cv2
    _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
    with _lock:
        _frame_imx500 = buf.tobytes()


def _gen_stream(get_fn):
    while True:
        f = get_fn()
        if f:
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + f + b'\r\n'
        time.sleep(0.04)


@app.route('/stream/imx500')
def stream_imx500():
    return Response(_gen_stream(lambda: _frame_imx500),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/estado')
def api_estado():
    with _lock:
        d = dict(_estado)
        d["uptime"] = int(time.time() - d["uptime_start"])
    return jsonify(d)


@app.route('/api/comando', methods=['POST'])
def api_comando():
    data = request.get_json()
    cmd  = data.get("cmd", "")

    if cmd == "modo" and _callback_modo:
        novo = data.get("modo", "bolas")
        _callback_modo(novo)
        atualizar_estado(log={"msg": f"Painel: modo → '{novo}'", "tipo": "ok"})
        return jsonify({"ok": True})

    if cmd == "emergencia" and _callback_emergencia:
        _callback_emergencia()
        atualizar_estado(log={"msg": "PARADA DE EMERGÊNCIA!", "tipo": "warn"})
        return jsonify({"ok": True})

    if cmd == "reset_gyro" and _callback_reset_gyro:
        _callback_reset_gyro()
        atualizar_estado(log={"msg": "Giroscópio resetado.", "tipo": "info"})
        return jsonify({"ok": True})

    return jsonify({"ok": False, "erro": "comando desconhecido"})


@app.route('/')
def index():
    return render_template_string(HTML)


# ══════════════════════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OBR Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

  :root {
    --bg:        #07090f;
    --bg2:       #0c0f1a;
    --bg3:       #111526;
    --border:    #1b2035;
    --border2:   #242b44;
    --txt:       #c8d6f0;
    --txt2:      #4a5578;
    --txt3:      #2a3050;
    --blue:      #3b82f6;
    --blue-dim:  #1d3a6e;
    --cyan:      #22d3ee;
    --green:     #22c55e;
    --amber:     #f59e0b;
    --red:       #ef4444;
    --silver:    #cbd5e1;
    --purple:    #a855f7;
    --orange:    #fb923c;
    --mono:      'Share Tech Mono', monospace;
    --sans:      'Rajdhani', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    font-family: var(--sans);
    color: var(--txt);
    min-height: 100vh;
    font-size: 14px;
  }

  body::after {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.06) 2px, rgba(0,0,0,.06) 4px);
    pointer-events: none;
    z-index: 9999;
  }

  /* ── topbar ── */
  .topbar {
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
    height: 48px;
    padding: 0 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
  }
  .topbar-l { display: flex; align-items: center; gap: 14px; }
  .logo { font-family: var(--mono); font-size: 14px; color: var(--cyan); letter-spacing: 2px; }
  .logo-sub { font-size: 11px; color: var(--txt3); font-family: var(--mono); }
  .topbar-r { display: flex; align-items: center; gap: 22px; font-family: var(--mono); font-size: 11px; color: var(--txt2); }
  .chip { color: var(--cyan); }

  .live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.25} }
  .live-dot { animation: pulse 2s infinite; }

  .npu-badge { font-family: var(--mono); font-size: 10px; padding: 3px 9px; border-radius: 4px; font-weight: 700; letter-spacing: 1px; }
  .npu-on  { background: #0d3320; color: #4ade80; border: 1px solid #16a34a50; }
  .npu-off { background: #2a1a06; color: #fbbf24; border: 1px solid #d9770630; }

  /* ── layout ── */
  .main { padding: 12px; display: grid; gap: 10px; }

  /* ── mode bar ── */
  .mode-bar {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 11px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }
  .mlabel { font-family: var(--mono); font-size: 9px; color: var(--txt3); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 7px; }
  .mbtns { display: flex; gap: 7px; flex-wrap: wrap; }
  .mbtn {
    padding: 6px 18px; border-radius: 6px; border: 1px solid var(--border2);
    background: transparent; color: var(--txt2);
    font-family: var(--sans); font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all .15s; letter-spacing: .5px;
  }
  .mbtn:hover { color: var(--txt); background: var(--bg3); }
  .mb  { background: #2a1a0610; border-color: var(--amber);  color: #fbbf24; }
  .mt  { background: #1a102a10; border-color: var(--purple); color: #c084fc; }
  .mo  { background: #1a0a0a10; border-color: var(--orange); color: #fb923c; }

  .pill { font-family: var(--mono); font-size: 11px; font-weight: 700; padding: 4px 14px; border-radius: 20px; letter-spacing: 1px; }
  .pb { background: #2a1a0618; color: #fbbf24; border: 1px solid #f59e0b40; }
  .pt { background: #1a102a18; color: #c084fc; border: 1px solid #a855f740; }
  .po { background: #1a0a0a18; color: #fb923c; border: 1px solid #fb923c40; }

  .status-r { display: flex; align-items: center; gap: 10px; }
  .ebtn {
    padding: 7px 14px; border-radius: 7px; border: 1px solid #ef444440;
    background: #ef444412; color: #f87171;
    font-family: var(--sans); font-size: 12px; font-weight: 700;
    cursor: pointer; letter-spacing: .5px; transition: all .15s;
  }
  .ebtn:hover { background: #ef444428; }

  /* ── câmera ── */
  .cam-wrap {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 10px; overflow: hidden;
    transition: border-color .3s, box-shadow .3s;
  }
  .cam-wrap.obst-alert { border-color: var(--orange); box-shadow: 0 0 20px #fb923c25; }
  .cam-hdr {
    padding: 8px 14px; display: flex; align-items: center;
    justify-content: space-between; border-bottom: 1px solid var(--border);
  }
  .cam-t { font-family: var(--mono); font-size: 10px; color: var(--txt2); letter-spacing: 1px; }
  .cam-screen { position: relative; background: #020408; overflow: hidden; }
  .cam-screen img { width: 100%; display: block; min-height: 180px; object-fit: cover; }

  @keyframes scan { 0%{top:-2px} 100%{top:100%} }
  .cam-scanline {
    position: absolute; width: 100%; height: 2px; top: 0; left: 0;
    pointer-events: none; animation: scan 3s linear infinite;
    background: linear-gradient(90deg, transparent, #22d3ee30, transparent);
  }
  .cam-scanline.orange { background: linear-gradient(90deg, transparent, #fb923c30, transparent); }

  .cam-hud {
    position: absolute; bottom: 6px; left: 8px; right: 8px;
    display: flex; justify-content: space-between; pointer-events: none;
  }
  .hud-txt { font-family: var(--mono); font-size: 10px; color: #22d3ee70; text-shadow: 0 0 6px #22d3ee40; }
  .hud-txt.amber  { color: #f59e0b70; text-shadow: 0 0 6px #f59e0b40; }
  .hud-txt.orange { color: #fb923c80; text-shadow: 0 0 6px #fb923c40; }

  /* ── seção obstáculo ── */
  .obst-section {
    display: none;
    background: var(--bg2);
    border: 1px solid #fb923c40;
    border-radius: 10px;
    padding: 14px 16px;
    gap: 12px;
  }
  .obst-section.visible { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media(max-width:500px) { .obst-section.visible { grid-template-columns: 1fr; } }

  .obst-section-title {
    grid-column: 1 / -1;
    font-family: var(--mono); font-size: 9px; color: var(--orange);
    letter-spacing: 2px; text-transform: uppercase;
    display: flex; align-items: center; gap: 8px;
  }
  .obst-big-indicator {
    grid-column: 1 / -1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    display: flex; align-items: center; gap: 14px;
  }
  .obst-status-txt {
    font-family: var(--mono); font-size: 18px; font-weight: 700;
    flex: 1;
  }
  .ost-idle   { color: var(--txt3); }
  .ost-detect { color: var(--orange); animation: pulse .7s infinite; }
  .ost-wait   { color: var(--amber);  animation: pulse .5s infinite; }
  .ost-verif  { color: var(--red);    animation: pulse .4s infinite; }

  .obst-pct-wrap {
    display: flex; flex-direction: column; align-items: flex-end; gap: 4px; min-width: 80px;
  }
  .obst-pct-num { font-family: var(--mono); font-size: 22px; font-weight: 700; color: var(--orange); }
  .obst-pct-lbl { font-family: var(--mono); font-size: 9px; color: var(--txt3); letter-spacing: 1px; }

  .obst-bar-big-wrap {
    grid-column: 1 / -1;
    background: var(--bg); border-radius: 6px; height: 8px;
    border: 1px solid var(--border); overflow: hidden;
  }
  .obst-bar-big-fill {
    height: 100%; border-radius: 6px;
    background: linear-gradient(90deg, #fb923c, #ef4444);
    transition: width .5s;
  }

  .obst-info-card {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 7px; padding: 10px 12px;
  }
  .oic-lbl { font-family: var(--mono); font-size: 9px; color: var(--txt3); letter-spacing: 1px; margin-bottom: 5px; }
  .oic-val { font-family: var(--mono); font-size: 13px; font-weight: 700; color: var(--txt); }

  /* ── grid inferior ── */
  .bottom-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
  @media(max-width:640px) { .bottom-grid { grid-template-columns: 1fr; } }

  .card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 10px; padding: 13px;
  }
  .card-t {
    font-family: var(--mono); font-size: 9px; color: var(--txt3);
    text-transform: uppercase; letter-spacing: 2px; margin-bottom: 11px;
    display: flex; align-items: center; gap: 7px;
  }
  .cdot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }

  /* ── giroscópio ── */
  .gyro-row { display: flex; align-items: center; margin-bottom: 8px; gap: 8px; }
  .gyro-lbl { font-family: var(--mono); font-size: 10px; color: var(--txt2); width: 44px; }
  .gyro-track { flex: 1; height: 2px; background: var(--bg3); border-radius: 2px; overflow: hidden; }
  .gyro-fill  { height: 100%; border-radius: 2px; transition: width .4s; }
  .gyro-val   { font-family: var(--mono); font-size: 11px; min-width: 52px; text-align: right; }
  .fps-row { display: flex; gap: 8px; margin-top: 10px; }
  .fps-chip { flex: 1; background: var(--bg); border-radius: 7px; padding: 8px; text-align: center; border: 1px solid var(--border); }
  .fps-n { font-family: var(--mono); font-size: 18px; font-weight: 700; color: var(--cyan); }
  .fps-s { font-family: var(--mono); font-size: 9px; color: var(--txt3); margin-top: 2px; letter-spacing: 1px; }

  /* ── status rows ── */
  .cmd-row {
    background: var(--bg); border-radius: 6px; padding: 7px 11px; margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
    border: 1px solid var(--border);
  }
  .cmd-k { font-family: var(--mono); font-size: 10px; color: var(--txt2); letter-spacing: .5px; }
  .cmd-v { font-family: var(--mono); font-size: 11px; font-weight: 700; }
  .cv-ok   { color: var(--green); }
  .cv-idle { color: var(--txt3); }
  .cv-warn { color: var(--amber); animation: pulse .8s infinite; }
  .cv-obst { color: var(--orange); animation: pulse .6s infinite; }

  /* ── controles ── */
  .ctrl-btn {
    width: 100%; padding: 8px; border-radius: 7px;
    border: 1px solid var(--border); background: transparent; color: var(--txt2);
    font-family: var(--sans); font-size: 12px; font-weight: 600;
    cursor: pointer; transition: all .15s; margin-bottom: 6px; text-align: center; letter-spacing: .5px;
  }
  .ctrl-btn:hover { border-color: var(--border2); color: var(--txt); background: var(--bg3); }
  .ctrl-btn-warn { border-color: #f59e0b30; color: var(--amber); }
  .ctrl-btn-warn:hover { background: #f59e0b10; }
  .ctrl-btn-red  { border-color: #ef444430; color: #f87171; }
  .ctrl-btn-red:hover  { background: #ef444410; }
  .ctrl-btn-obst { border-color: #fb923c30; color: #fb923c; }
  .ctrl-btn-obst:hover { background: #fb923c10; }

  /* ── log ── */
  .log-full { grid-column: 1 / -1; }
  .log-hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 9px; }
  .log-wrap {
    background: var(--bg); border: 1px solid var(--border); border-radius: 7px;
    padding: 7px; max-height: 105px; overflow-y: auto;
  }
  .log-wrap::-webkit-scrollbar { width: 4px; }
  .log-wrap::-webkit-scrollbar-track { background: transparent; }
  .log-wrap::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }
  .log-line {
    font-family: var(--mono); font-size: 10px;
    display: flex; gap: 8px; padding: 2px 0;
    border-bottom: 1px solid var(--bg3);
  }
  .log-line:last-child { border: none; }
  .log-ts   { color: var(--txt3); min-width: 52px; }
  .log-ok   { color: var(--green); }
  .log-warn { color: var(--amber); }
  .log-info { color: var(--cyan); }
  .log-def  { color: var(--txt2); }

  .conn-line { display: flex; align-items: center; gap: 6px; font-family: var(--mono); font-size: 10px; color: var(--green); margin-top: 9px; }
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-l">
    <div class="live-dot"></div>
    <span class="logo">OBR // IMX500</span>
    <span class="logo-sub">Raspberry Pi 4</span>
  </div>
  <div class="topbar-r">
    <span id="npu-badge" class="npu-badge npu-off">NPU OFF</span>
    <span>IP: <span class="chip" id="ip-addr">—</span></span>
    <span>UP: <span class="chip" id="uptime">—</span></span>
    <span id="conn-status" style="color:var(--green)">● online</span>
  </div>
</div>

<div class="main">

  <!-- ── MODO BAR ── -->
  <div class="mode-bar">
    <div>
      <div class="mlabel">Modo de operação</div>
      <div class="mbtns">
        <button class="mbtn" id="btn-bolas"     onclick="enviarModo('bolas')">Bolas</button>
        <button class="mbtn" id="btn-triangulo" onclick="enviarModo('triangulo')">Triângulo</button>
        <button class="mbtn" id="btn-obstaculo" onclick="enviarModo('obstaculo')">Obstáculo</button>
      </div>
    </div>
    <div class="status-r">
      <div class="live-dot"></div>
      <span class="pill" id="mode-pill">—</span>
      <button class="ebtn" onclick="enviarEmergencia()">⚠ EMERGÊNCIA</button>
    </div>
  </div>

  <!-- ── CÂMERA IMX500 ── -->
  <div class="cam-wrap" id="cam-imx500">
    <div class="cam-hdr">
      <span class="cam-t" id="cam500-titulo">IMX500 — AGUARDANDO</span>
      <span style="font-family:var(--mono);font-size:9px;color:var(--txt2)" id="cam500-fps-badge">0.0 fps</span>
    </div>
    <div class="cam-screen">
      <img src="/stream/imx500" alt="IMX500" onerror="this.style.minHeight='180px'">
      <div class="cam-scanline" id="cam-scan"></div>
      <div class="cam-hud">
        <span class="hud-txt" id="hud-modo">MODE: —</span>
        <span class="hud-txt orange" id="hud-obst">OBST: idle</span>
        <span class="hud-txt" id="hud-fps">— fps</span>
      </div>
    </div>
  </div>

  <!-- ══ SEÇÃO OBSTÁCULO — visível apenas no modo obstáculo ══ -->
  <div class="obst-section" id="obst-section">
    <div class="obst-section-title">
      <div style="width:6px;height:6px;border-radius:50%;background:var(--orange)"></div>
      Detecção de Obstáculo
    </div>

    <div class="obst-big-indicator">
      <span class="obst-status-txt ost-idle" id="obst-status-txt">IDLE</span>
      <div class="obst-pct-wrap">
        <span class="obst-pct-num" id="obst-pct-num">0</span>
        <span class="obst-pct-lbl">SCORE %</span>
      </div>
    </div>

    <div class="obst-bar-big-wrap">
      <div class="obst-bar-big-fill" id="obst-bar-big" style="width:0%"></div>
    </div>

    <div class="obst-info-card">
      <div class="oic-lbl">ESTADO</div>
      <div class="oic-val" id="oic-estado">idle</div>
    </div>
    <div class="obst-info-card">
      <div class="oic-lbl">ÚLTIMO RESULTADO</div>
      <div class="oic-val" id="oic-ultimo">—</div>
    </div>
  </div>

  <!-- ── GRID INFERIOR ── -->
  <div class="bottom-grid">

    <!-- Giroscópio -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:var(--cyan)"></div>Giroscópio MPU6050</div>
      <div class="gyro-row">
        <span class="gyro-lbl">Roll X</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfx" style="background:var(--blue);width:50%"></div></div>
        <span class="gyro-val" id="gvx" style="color:var(--cyan)">0.0°</span>
      </div>
      <div class="gyro-row">
        <span class="gyro-lbl">Pitch Y</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfy" style="background:var(--green);width:50%"></div></div>
        <span class="gyro-val" id="gvy" style="color:var(--green)">0.0°</span>
      </div>
      <div class="gyro-row">
        <span class="gyro-lbl">Yaw Z</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfz" style="background:var(--purple);width:50%"></div></div>
        <span class="gyro-val" id="gvz" style="color:var(--purple)">0.0°</span>
      </div>
      <div class="fps-row">
        <div class="fps-chip">
          <div class="fps-n" id="fps0">—</div>
          <div class="fps-s">IMX500 fps</div>
        </div>
        <div class="fps-chip">
          <div class="fps-n" id="fps0b" style="color:var(--amber)">—</div>
          <div class="fps-s">INFER fps</div>
        </div>
      </div>
    </div>

    <!-- Estado do sistema -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:#f87171"></div>Estado do sistema</div>
      <div class="cmd-row"><span class="cmd-k">Bumper</span><span class="cmd-v cv-idle" id="s-bumper">livre</span></div>
      <div class="cmd-row"><span class="cmd-k">Modelo NPU</span><span class="cmd-v cv-ok" id="s-modelo" style="font-size:9px;overflow:hidden;text-overflow:ellipsis;max-width:120px">—</span></div>
      <div class="cmd-row"><span class="cmd-k">Modo ativo</span><span class="cmd-v cv-ok" id="s-modo-ativo">—</span></div>
      <div class="conn-line">
        <div style="width:5px;height:5px;border-radius:50%;background:var(--green)"></div>
        <span id="s-ev3">EV3 serial</span>
      </div>
    </div>

    <!-- Controles rápidos -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:var(--green)"></div>Controles rápidos</div>
      <button class="ctrl-btn"       onclick="enviarModo('bolas')">→ Modo: Bolas</button>
      <button class="ctrl-btn"       onclick="enviarModo('triangulo')">→ Modo: Triângulo</button>
      <button class="ctrl-btn ctrl-btn-obst" onclick="enviarModo('obstaculo')">→ Modo: Obstáculo</button>
      <button class="ctrl-btn ctrl-btn-warn" onclick="enviarResetGyro()">Reset giroscópio</button>
      <button class="ctrl-btn ctrl-btn-red"  onclick="enviarEmergencia()">⚠ Parada de emergência</button>
    </div>

    <!-- Log -->
    <div class="card log-full">
      <div class="log-hdr">
        <div class="card-t" style="margin:0">
          <div class="cdot" style="background:var(--txt3)"></div>Log de eventos
        </div>
        <button class="ctrl-btn"
          style="width:auto;padding:2px 12px;margin:0;font-size:10px"
          onclick="document.getElementById('log-wrap').innerHTML=''">limpar</button>
      </div>
      <div class="log-wrap" id="log-wrap"></div>
    </div>

  </div>
</div>

<script>
const PILL     = { bolas:['pb','BOLAS'], triangulo:['pt','TRIÂNGULO'], obstaculo:['po','OBSTÁCULO'] };
const MBTN_CLS = { bolas:'mb', triangulo:'mt', obstaculo:'mo' };
const CAM_TITULO = {
  bolas:     'IMX500 — BOLAS',
  triangulo: 'IMX500 — TRIÂNGULO',
  obstaculo: 'IMX500 — OBSTÁCULO',
};
const OBST_LABELS = {
  idle:                   ['ost-idle',   'IDLE'],
  aguardando_confirmacao: ['ost-wait',   'AGUARDANDO EV3'],
  verificando:            ['ost-verif',  'VERIFICANDO LADOS'],
};

let modoAtual   = '';
let ultimoObst  = '—';

function atualizarUI(d) {
  // ── Modo ──
  if (d.modo !== modoAtual) {
    modoAtual = d.modo;
    ['bolas','triangulo','obstaculo'].forEach(m => {
      document.getElementById('btn-'+m).className =
        'mbtn' + (m === modoAtual ? ' '+MBTN_CLS[m] : '');
    });
    const p = document.getElementById('mode-pill');
    const [cls, txt] = PILL[modoAtual] || ['pb', modoAtual];
    p.className = 'pill ' + cls;
    p.textContent = txt;
    document.getElementById('cam500-titulo').textContent = CAM_TITULO[modoAtual] || 'IMX500';
    document.getElementById('hud-modo').textContent = 'MODE: ' + modoAtual.toUpperCase();
    document.getElementById('s-modo-ativo').textContent = modoAtual;

    // mostrar/ocultar seção obstáculo
    const sec = document.getElementById('obst-section');
    sec.className = modoAtual === 'obstaculo' ? 'obst-section visible' : 'obst-section';

    // cor scanline e borda câmera
    const cam  = document.getElementById('cam-imx500');
    const scan = document.getElementById('cam-scan');
    if (modoAtual === 'obstaculo') {
      cam.className  = 'cam-wrap obst-alert';
      scan.className = 'cam-scanline orange';
    } else {
      cam.className  = 'cam-wrap';
      scan.className = 'cam-scanline';
    }
  }

  // ── NPU badge ──
  const npuBadge = document.getElementById('npu-badge');
  npuBadge.textContent = d.npu_ativo ? 'NPU ON' : 'CPU fallback';
  npuBadge.className   = 'npu-badge ' + (d.npu_ativo ? 'npu-on' : 'npu-off');
  document.getElementById('s-modelo').textContent = d.npu_modelo || '—';

  // ── Giroscópio ──
  const fmt = v => (v>=0?'+':'')+parseFloat(v).toFixed(1)+'°';
  const gyr = v => Math.min(100, (Math.abs(v)/180)*100 + 50);
  document.getElementById('gvx').textContent = fmt(d.gyro_roll);
  document.getElementById('gvy').textContent = fmt(d.gyro_pitch);
  document.getElementById('gvz').textContent = fmt(d.gyro_yaw);
  document.getElementById('gfx').style.width = gyr(d.gyro_roll)+'%';
  document.getElementById('gfy').style.width = gyr(d.gyro_pitch)+'%';
  document.getElementById('gfz').style.width = gyr(d.gyro_yaw)+'%';

  // ── FPS ──
  const fps = parseFloat(d.fps_imx500).toFixed(1);
  document.getElementById('fps0').textContent         = fps;
  document.getElementById('fps0b').textContent        = fps;
  document.getElementById('hud-fps').textContent      = fps + ' fps';
  document.getElementById('cam500-fps-badge').textContent = fps + ' fps';

  // ── Seção obstáculo ──
  const pct      = parseFloat(d.obst_pct || 0);
  const estado   = d.obstaculo || 'idle';
  const hudObst  = document.getElementById('hud-obst');
  const oicEst   = document.getElementById('oic-estado');
  const oicUlt   = document.getElementById('oic-ultimo');
  const bigTxt   = document.getElementById('obst-status-txt');
  const bigBar   = document.getElementById('obst-bar-big');
  const pctNum   = document.getElementById('obst-pct-num');

  hudObst.textContent = 'OBST: ' + estado;
  oicEst.textContent  = estado;
  pctNum.textContent  = Math.round(pct);
  bigBar.style.width  = Math.min(100, pct) + '%';

  const [cls, label] = OBST_LABELS[estado] || ['ost-idle', estado.toUpperCase()];
  bigTxt.className  = 'obst-status-txt ' + cls;
  bigTxt.textContent = label;

  // guarda último resultado de verificação
  if (d.log && d.log.length) {
    const last = [...d.log].reverse().find(l => l.msg.startsWith('Verificação:'));
    if (last) oicUlt.textContent = last.msg.replace('Verificação: ', '');
  }

  // ── Estado geral ──
  document.getElementById('s-bumper').textContent = d.bumper || 'livre';

  // ── Uptime ──
  const up = d.uptime || 0;
  const hh = String(Math.floor(up/3600)).padStart(2,'0');
  const mm = String(Math.floor((up%3600)/60)).padStart(2,'0');
  const ss = String(up%60).padStart(2,'0');
  document.getElementById('uptime').textContent = hh+':'+mm+':'+ss;

  // ── Log ──
  if (d.log && d.log.length) {
    const CLS = {ok:'log-ok',warn:'log-warn',info:'log-info'};
    document.getElementById('log-wrap').innerHTML =
      d.log.slice().reverse().map(l =>
        `<div class="log-line"><span class="log-ts">${l.t}</span>`+
        `<span class="${CLS[l.tipo]||'log-def'}">${l.msg}</span></div>`
      ).join('');
  }
}

async function poll() {
  try {
    const r = await fetch('/api/estado');
    if (r.ok) {
      const d = await r.json();
      document.getElementById('ip-addr').textContent = location.host;
      document.getElementById('conn-status').textContent = '● online';
      document.getElementById('conn-status').style.color = 'var(--green)';
      atualizarUI(d);
    }
  } catch(e) {
    document.getElementById('conn-status').textContent = '● offline';
    document.getElementById('conn-status').style.color = 'var(--red)';
  }
}

async function enviarModo(modo) {
  await fetch('/api/comando',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cmd:'modo',modo})});
}
async function enviarEmergencia() {
  await fetch('/api/comando',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cmd:'emergencia'})});
}
async function enviarResetGyro() {
  await fetch('/api/comando',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cmd:'reset_gyro'})});
}

setInterval(poll, 400);
poll();
</script>
</body>
</html>
"""


def iniciar_servidor():
    t = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000,
                               threaded=True, use_reloader=False),
        daemon=True)
    t.start()
    print("[+] Dashboard: http://<IP>:5000")