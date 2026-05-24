from flask import Flask, Response, render_template_string, jsonify, request
import threading
import time

app = Flask(__name__)
_lock = threading.Lock()

_estado = {
    "modo": "linha",
    "cmd_camera": "frente",
    "obstaculo": "idle",
    "previsao_verde": "—",
    "bumper": "livre",
    "gyro_roll": 0.0,
    "gyro_pitch": 0.0,
    "gyro_yaw": 0.0,
    "fps_imx500": 0.0,
    "fps_imx179": 0.0,
    # ── NOVOS: fitas ──────────────────────────────────────────────
    "fita_prata": False,   # True quando prata visível (qualquer modo)
    "fita_preta": False,   # True quando preta visível no modo resgate
    "ultimo_aviso_fita": "—",  # última string de fita recebida
    # ─────────────────────────────────────────────────────────────
    "log": [],
    "uptime_start": time.time(),
    "ev3_conectado": True,
}

_frame_imx500 = None
_frame_imx179 = None

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
    _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 65])
    with _lock:
        _frame_imx500 = buf.tobytes()

def atualizar_frame_imx179(frame_bgr):
    global _frame_imx179
    import cv2
    _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 65])
    with _lock:
        _frame_imx179 = buf.tobytes()

def _gen_stream(get_fn):
    while True:
        f = get_fn()
        if f:
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + f + b'\r\n'
        time.sleep(0.05)

@app.route('/stream/imx500')
def stream_imx500():
    return Response(_gen_stream(lambda: _frame_imx500),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream/imx179')
def stream_imx179():
    return Response(_gen_stream(lambda: _frame_imx179),
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
        novo = data.get("modo", "linha")
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
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0c14;font-family:'Segoe UI',system-ui,sans-serif;color:#e2e8f0;min-height:100vh}

/* ── topbar ── */
.topbar{background:#0f1220;border-bottom:1px solid #1e2440;padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between}
.topbar-l{display:flex;align-items:center;gap:12px}
.live-dot{width:9px;height:9px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes scan{0%{top:0}100%{top:100%}}
@keyframes blink-silver{0%,100%{opacity:1;box-shadow:0 0 8px #c0c0c060}50%{opacity:.5;box-shadow:none}}
@keyframes blink-black{0%,100%{opacity:1;box-shadow:0 0 8px #ef444460}50%{opacity:.4;box-shadow:none}}
.logo{font-size:15px;font-weight:700;color:#f1f5f9;letter-spacing:.5px}
.logo-sub{font-size:11px;color:#334155;margin-left:2px}
.topbar-r{display:flex;align-items:center;gap:20px;font-size:12px;color:#475569}
.chip{color:#7dd3fc;font-family:monospace}

/* ── layout ── */
.main{padding:14px;display:grid;gap:12px}

/* ── mode bar ── */
.mode-bar{background:#0f1220;border:1px solid #1e2440;border-radius:12px;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.mlabel{font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.mbtns{display:flex;gap:8px}
.mbtn{padding:7px 20px;border-radius:8px;border:1px solid #1e2440;background:transparent;color:#475569;font-size:13px;cursor:pointer;transition:all .18s;font-weight:500}
.mbtn:hover{border-color:#334155;color:#94a3b8;background:#151929}
.ml{background:#0ea5e918;border-color:#0ea5e9;color:#38bdf8}
.mb{background:#f59e0b18;border-color:#f59e0b;color:#fbbf24}
.mt{background:#a855f718;border-color:#a855f7;color:#c084fc}
.pill{padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700}
.pl{background:#0ea5e918;color:#38bdf8;border:1px solid #0ea5e940}
.pb{background:#f59e0b18;color:#fbbf24;border:1px solid #f59e0b40}
.pt{background:#a855f718;color:#c084fc;border:1px solid #a855f740}
.status-r{display:flex;align-items:center;gap:10px}
.ebtn{padding:7px 16px;border-radius:8px;border:1px solid #ef444440;background:#ef444410;color:#f87171;font-size:12px;cursor:pointer;font-weight:700;transition:all .18s}
.ebtn:hover{background:#ef444425}

/* ── câmeras ── */
.cams{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:600px){.cams,.bottom-grid{grid-template-columns:1fr}}
.cam-card{background:#0f1220;border:1px solid #1e2440;border-radius:12px;overflow:hidden;transition:border-color .3s}
.cam-card.silver-alert{border-color:#c0c0c0;box-shadow:0 0 12px #c0c0c025}
.cam-card.black-alert{border-color:#ef4444;box-shadow:0 0 12px #ef444425}
.cam-hdr{padding:9px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #1e2440}
.cam-t{font-size:11px;font-weight:600;color:#64748b;letter-spacing:.5px}
.badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700}
.b-on{background:#22c55e18;color:#4ade80;border:1px solid #22c55e30}
.b-silver{background:#c0c0c018;color:#d4d4d4;border:1px solid #c0c0c050;animation:blink-silver .8s infinite}
.b-black{background:#ef444418;color:#f87171;border:1px solid #ef444440;animation:blink-black .8s infinite}
.cam-screen{position:relative;background:#060810;overflow:hidden}
.cam-screen img{width:100%;height:auto;display:block;min-height:120px;object-fit:cover}
.scanline{position:absolute;width:100%;height:2px;top:0;pointer-events:none;animation:scan 2.5s linear infinite}
.sl-b{background:linear-gradient(90deg,transparent,#0ea5e930,transparent)}
.sl-a{background:linear-gradient(90deg,transparent,#f59e0b25,transparent)}
.sl-s{background:linear-gradient(90deg,transparent,#c0c0c040,transparent)}
.cam-hud{position:absolute;bottom:6px;left:8px;right:8px;display:flex;justify-content:space-between;pointer-events:none}
.hud-txt{font-size:10px;font-family:monospace;color:#0ea5e980}
.hud-txt-a{color:#f59e0b80}
.fita-overlay{position:absolute;top:0;left:0;right:0;padding:4px 8px;font-size:11px;font-weight:700;font-family:monospace;text-align:center;display:none}
.fita-overlay.silver{background:#c0c0c030;color:#e2e2e2;border-bottom:1px solid #c0c0c050;display:block}
.fita-overlay.black{background:#ef444420;color:#f87171;border-bottom:1px solid #ef444440;display:block}

/* ── fita banner (barra de alerta de fita) ── */
.fita-bar{display:none;border-radius:10px;padding:10px 16px;align-items:center;gap:10px;font-size:13px;font-weight:600}
.fita-bar.show{display:flex}
.fita-bar.silver{background:#c0c0c012;border:1px solid #c0c0c040;color:#d4d4d4}
.fita-bar.black-fita{background:#ef444412;border:1px solid #ef444440;color:#f87171}
.fita-bar-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}

/* ── grid inferior ── */
.bottom-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.card{background:#0f1220;border:1px solid #1e2440;border-radius:12px;padding:14px}
.card-t{font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.cdot{width:6px;height:6px;border-radius:50%;flex-shrink:0}

/* ── giroscópio ── */
.gyro-row{display:flex;align-items:center;margin-bottom:9px;gap:8px}
.gyro-lbl{font-size:11px;color:#475569;width:40px}
.gyro-track{flex:1;height:3px;background:#1a1f35;border-radius:2px;overflow:hidden}
.gyro-fill{height:100%;border-radius:2px;transition:width .5s}
.gyro-val{font-size:12px;font-family:monospace;min-width:50px;text-align:right}
.fps-row{display:flex;gap:8px;margin-top:10px}
.fps-chip{flex:1;background:#060810;border-radius:8px;padding:8px;text-align:center}
.fps-n{font-size:17px;font-weight:700;font-family:monospace;color:#38bdf8}
.fps-s{font-size:10px;color:#334155;margin-top:1px}

/* ── estado ── */
.cmd-row{background:#060810;border-radius:8px;padding:8px 12px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center}
.cmd-k{font-size:11px;color:#334155}
.cmd-v{font-size:12px;font-family:monospace;font-weight:600}
.cv-ok{color:#22c55e}
.cv-idle{color:#334155}
.cv-warn{color:#f59e0b;animation:pulse .8s infinite}
.cv-silver{color:#c0c0c0;animation:blink-silver .8s infinite}
.cv-black{color:#f87171;animation:blink-black .8s infinite}

/* ── fita indicadores no card de estado ── */
.fita-pills{display:flex;gap:8px;margin-bottom:7px}
.fita-pill{flex:1;border-radius:8px;padding:7px 8px;text-align:center;font-size:11px;font-weight:700;border:1px solid;transition:all .3s}
.fp-silver-off{background:#1a1f35;border-color:#1e2440;color:#334155}
.fp-silver-on{background:#c0c0c018;border-color:#c0c0c050;color:#d4d4d4;animation:blink-silver .8s infinite}
.fp-black-off{background:#1a1f35;border-color:#1e2440;color:#334155}
.fp-black-on{background:#ef444418;border-color:#ef444440;color:#f87171;animation:blink-black .8s infinite}

/* ── controles ── */
.ctrl-btn{width:100%;padding:9px;border-radius:8px;border:1px solid #1e2440;background:transparent;color:#64748b;font-size:12px;cursor:pointer;transition:all .18s;font-weight:500;margin-bottom:7px;text-align:center}
.ctrl-btn:hover{border-color:#334155;color:#94a3b8;background:#151929}
.ctrl-btn-warn{border-color:#f59e0b30;color:#f59e0b}
.ctrl-btn-warn:hover{background:#f59e0b10}

/* ── log ── */
.log-full{grid-column:1/-1}
.log-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.log-wrap{background:#060810;border-radius:8px;padding:8px;max-height:110px;overflow-y:auto}
.log-line{font-size:11px;font-family:monospace;display:flex;gap:8px;padding:2px 0;border-bottom:1px solid #0f1220}
.log-line:last-child{border:none}
.log-ts{color:#1e2440;min-width:52px}
.log-ok{color:#22c55e}
.log-warn{color:#f59e0b}
.log-info{color:#38bdf8}
.log-silver{color:#c0c0c0}
.log-def{color:#334155}
.conn-line{display:flex;align-items:center;gap:6px;font-size:11px;color:#22c55e;margin-top:10px}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-l">
    <div class="live-dot"></div>
    <span class="logo">OBR Dashboard</span>
    <span class="logo-sub">Raspberry Pi 4</span>
  </div>
  <div class="topbar-r">
    <span>IP: <span class="chip" id="ip-addr">carregando...</span></span>
    <span>Uptime: <span class="chip" id="uptime">—</span></span>
    <span id="conn-status" style="color:#22c55e">● conectado</span>
  </div>
</div>

<div class="main">

  <!-- ── MODO BAR ── -->
  <div class="mode-bar">
    <div>
      <div class="mlabel">Modo de operação</div>
      <div class="mbtns">
        <button class="mbtn" id="btn-linha"     onclick="enviarModo('linha')">Linha</button>
        <button class="mbtn" id="btn-bolas"     onclick="enviarModo('bolas')">Bolas</button>
        <button class="mbtn" id="btn-triangulo" onclick="enviarModo('triangulo')">Triângulo</button>
      </div>
    </div>
    <div class="status-r">
      <div class="live-dot"></div>
      <span class="pill" id="mode-pill">—</span>
      <button class="ebtn" onclick="enviarEmergencia()">Parada de emergência</button>
    </div>
  </div>

  <!-- ── BANNER DE FITA (aparece quando detecta) ── -->
  <div class="fita-bar" id="fita-bar">
    <div class="fita-bar-dot" id="fita-bar-dot"></div>
    <span id="fita-bar-txt">—</span>
  </div>

  <!-- ── CÂMERAS ── -->
  <div class="cams">
    <div class="cam-card" id="cam-imx500">
      <div class="cam-hdr">
        <span class="cam-t" id="cam500-titulo">IMX500 — Seguidor de linha</span>
        <span class="badge b-on" id="cam500-badge">AO VIVO</span>
      </div>
      <div class="cam-screen">
        <div class="fita-overlay" id="fita-overlay-500"></div>
        <img src="/stream/imx500" alt="IMX500" onerror="this.style.minHeight='130px'">
        <div class="scanline sl-b" id="scan500"></div>
        <div class="cam-hud">
          <span class="hud-txt" id="hud-cmd">CMD: —</span>
          <span class="hud-txt" id="hud-fps0">— fps</span>
        </div>
      </div>
    </div>

    <div class="cam-card" id="cam-imx179">
      <div class="cam-hdr">
        <span class="cam-t">IMX179 — Obstáculo / Resgate</span>
        <span class="badge b-on">AO VIVO</span>
      </div>
      <div class="cam-screen">
        <img src="/stream/imx179" alt="IMX179" onerror="this.style.minHeight='130px'">
        <div class="scanline sl-a"></div>
        <div class="cam-hud">
          <span class="hud-txt hud-txt-a" id="hud-obst">OBST: idle</span>
          <span class="hud-txt hud-txt-a" id="hud-fps1">— fps</span>
        </div>
      </div>
    </div>
  </div>

  <!-- ── GRID INFERIOR ── -->
  <div class="bottom-grid">

    <!-- Giroscópio -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:#7dd3fc"></div>Giroscópio MPU6050</div>
      <div class="gyro-row">
        <span class="gyro-lbl">Roll X</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfx" style="background:#0ea5e9;width:50%"></div></div>
        <span class="gyro-val" id="gvx" style="color:#38bdf8">0.0°</span>
      </div>
      <div class="gyro-row">
        <span class="gyro-lbl">Pitch Y</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfy" style="background:#22c55e;width:50%"></div></div>
        <span class="gyro-val" id="gvy" style="color:#4ade80">0.0°</span>
      </div>
      <div class="gyro-row">
        <span class="gyro-lbl">Yaw Z</span>
        <div class="gyro-track"><div class="gyro-fill" id="gfz" style="background:#a855f7;width:50%"></div></div>
        <span class="gyro-val" id="gvz" style="color:#c084fc">0.0°</span>
      </div>
      <div class="fps-row">
        <div class="fps-chip"><div class="fps-n" id="fps0">—</div><div class="fps-s">IMX500 fps</div></div>
        <div class="fps-chip"><div class="fps-n" id="fps1">—</div><div class="fps-s">IMX179 fps</div></div>
      </div>
    </div>

    <!-- Estado do sistema -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:#f87171"></div>Estado do sistema</div>

      <!-- Pills de fita -->
      <div class="fita-pills">
        <div class="fita-pill fp-silver-off" id="pill-prata">⬜ PRATA (entrada)</div>
        <div class="fita-pill fp-black-off"  id="pill-preta">⬛ PRETA (saída)</div>
      </div>

      <div class="cmd-row"><span class="cmd-k">Cmd câmera</span><span class="cmd-v cv-ok"  id="s-cmd">—</span></div>
      <div class="cmd-row"><span class="cmd-k">Obstáculo</span><span class="cmd-v cv-idle" id="s-obst">idle</span></div>
      <div class="cmd-row"><span class="cmd-k">Última fita</span><span class="cmd-v"        id="s-fita" style="color:#c0c0c0">—</span></div>
      <div class="cmd-row"><span class="cmd-k">Previsão verde</span><span class="cmd-v cv-ok" id="s-verde">—</span></div>
      <div class="cmd-row"><span class="cmd-k">Bumper</span><span class="cmd-v cv-idle"     id="s-bumper">livre</span></div>
      <div class="conn-line">
        <div style="width:6px;height:6px;border-radius:50%;background:#22c55e"></div>
        <span id="s-ev3">EV3 conectado via serial</span>
      </div>
    </div>

    <!-- Controles rápidos -->
    <div class="card">
      <div class="card-t"><div class="cdot" style="background:#22c55e"></div>Controles rápidos</div>
      <button class="ctrl-btn" onclick="enviarModo('linha')">Enviar modo: Linha</button>
      <button class="ctrl-btn" onclick="enviarModo('bolas')">Enviar modo: Bolas</button>
      <button class="ctrl-btn" onclick="enviarModo('triangulo')">Enviar modo: Triângulo</button>
      <button class="ctrl-btn ctrl-btn-warn" onclick="enviarResetGyro()">Reset giroscópio</button>
    </div>

    <!-- Log -->
    <div class="card log-full">
      <div class="log-hdr">
        <div class="card-t" style="margin:0">
          <div class="cdot" style="background:#334155"></div>Log de eventos
        </div>
        <button class="ctrl-btn"
          style="width:auto;padding:3px 12px;margin:0;font-size:11px"
          onclick="document.getElementById('log-wrap').innerHTML=''">Limpar</button>
      </div>
      <div class="log-wrap" id="log-wrap"></div>
    </div>

  </div>
</div>

<script>
const PILL    = {linha:['pl','Linha ativo'],bolas:['pb','Bolas ativo'],triangulo:['pt','Triângulo ativo']};
const MBTN_CLS= {linha:'ml',bolas:'mb',triangulo:'mt'};
const CAM500_TITULO = {
  linha:    'IMX500 — Seguidor de linha',
  bolas:    'IMX500 — Monitor de fitas (resgate)',
  triangulo:'IMX500 — Monitor de fitas (resgate)',
};

let modoAtual  = '';
let prataPrev  = false;
let pretaPrev  = false;
let fitaClearTimer = null;

function atualizarFitas(d) {
  const prata = d.fita_prata;
  const preta = d.fita_preta;
  const bar   = document.getElementById('fita-bar');
  const barTxt= document.getElementById('fita-bar-txt');
  const barDot= document.getElementById('fita-bar-dot');
  const ov500 = document.getElementById('fita-overlay-500');
  const pillS = document.getElementById('pill-prata');
  const pillN = document.getElementById('pill-preta');
  const cam500= document.getElementById('cam-imx500');
  const scan  = document.getElementById('scan500');
  const sfita = document.getElementById('s-fita');

  // Atualiza última fita recebida
  if (d.ultimo_aviso_fita && d.ultimo_aviso_fita !== '—') {
    sfita.textContent = d.ultimo_aviso_fita;
    sfita.style.color = d.ultimo_aviso_fita.includes('prata') ? '#c0c0c0' : '#f87171';
  }

  // Pill prata
  pillS.className = 'fita-pill ' + (prata ? 'fp-silver-on' : 'fp-silver-off');

  // Pill preta
  pillN.className = 'fita-pill ' + (preta ? 'fp-black-on' : 'fp-black-off');

  // Banner + overlay na câmera
  if (prata) {
    bar.className   = 'fita-bar show silver';
    barDot.style.background = '#c0c0c0';
    barTxt.textContent = '⬜  FITA PRATA detectada — ENTRADA DO RESGATE';
    ov500.className = 'fita-overlay silver';
    ov500.textContent = '★ ENTRADA RESGATE — PRATA DETECTADA';
    cam500.className = 'cam-card silver-alert';
    scan.className   = 'scanline sl-s';
  } else if (preta) {
    bar.className   = 'fita-bar show black-fita';
    barDot.style.background = '#f87171';
    barTxt.textContent = '⬛  FITA PRETA detectada — SAÍDA DO RESGATE';
    ov500.className = 'fita-overlay black';
    ov500.textContent = '✖ SAÍDA RESGATE — PRETA DETECTADA';
    cam500.className = 'cam-card black-alert';
    scan.className   = 'scanline sl-a';
  } else {
    bar.className   = 'fita-bar';
    ov500.className = 'fita-overlay';
    cam500.className= 'cam-card';
    scan.className  = 'scanline sl-b';
  }
}

function atualizarUI(d) {
  // ── Modo ──
  if (d.modo !== modoAtual) {
    modoAtual = d.modo;
    ['linha','bolas','triangulo'].forEach(m => {
      document.getElementById('btn-'+m).className =
        'mbtn' + (m === modoAtual ? ' '+MBTN_CLS[m] : '');
    });
    const p = document.getElementById('mode-pill');
    const [cls, txt] = PILL[modoAtual] || ['pl', modoAtual];
    p.className = 'pill '+cls;
    p.textContent = txt;
    // Atualiza título da câmera IMX500 conforme o modo
    document.getElementById('cam500-titulo').textContent =
      CAM500_TITULO[modoAtual] || 'IMX500';
  }

  // ── Giroscópio ──
  const gyr = v => Math.min(100, (Math.abs(v)/180)*100 + 50);
  const fmt = v => (v>=0?'+':'')+parseFloat(v).toFixed(1)+'°';
  document.getElementById('gvx').textContent  = fmt(d.gyro_roll);
  document.getElementById('gvy').textContent  = fmt(d.gyro_pitch);
  document.getElementById('gvz').textContent  = fmt(d.gyro_yaw);
  document.getElementById('gfx').style.width  = gyr(d.gyro_roll)+'%';
  document.getElementById('gfy').style.width  = gyr(d.gyro_pitch)+'%';
  document.getElementById('gfz').style.width  = gyr(d.gyro_yaw)+'%';

  // ── FPS ──
  document.getElementById('fps0').textContent     = parseFloat(d.fps_imx500).toFixed(1);
  document.getElementById('fps1').textContent     = parseFloat(d.fps_imx179).toFixed(1);
  document.getElementById('hud-fps0').textContent = parseFloat(d.fps_imx500).toFixed(1)+' fps';
  document.getElementById('hud-fps1').textContent = parseFloat(d.fps_imx179).toFixed(1)+' fps';

  // ── Estado geral ──
  document.getElementById('s-cmd').textContent    = d.cmd_camera;
  document.getElementById('s-verde').textContent  = d.previsao_verde || '—';
  document.getElementById('s-bumper').textContent = d.bumper || 'livre';
  document.getElementById('hud-cmd').textContent  = 'CMD: '+d.cmd_camera;

  const obstEl  = document.getElementById('s-obst');
  const obstHud = document.getElementById('hud-obst');
  obstEl.textContent  = d.obstaculo;
  obstHud.textContent = 'OBST: '+d.obstaculo;
  obstEl.className = 'cmd-v '+(d.obstaculo==='idle'?'cv-idle':'cv-warn');

  // ── Uptime ──
  const up=d.uptime||0;
  const hh=String(Math.floor(up/3600)).padStart(2,'0');
  const mm=String(Math.floor((up%3600)/60)).padStart(2,'0');
  const ss=String(up%60).padStart(2,'0');
  document.getElementById('uptime').textContent = hh+':'+mm+':'+ss;

  // ── Log ──
  if (d.log && d.log.length) {
    const CLS = {ok:'log-ok',warn:'log-warn',info:'log-info',silver:'log-silver'};
    document.getElementById('log-wrap').innerHTML =
      d.log.slice().reverse().map(l =>
        `<div class="log-line"><span class="log-ts">${l.t}</span>`+
        `<span class="${CLS[l.tipo]||'log-def'}">${l.msg}</span></div>`
      ).join('');
  }

  // ── Fitas ──
  atualizarFitas(d);
}

async function poll() {
  try {
    const r = await fetch('/api/estado');
    if (r.ok) {
      const d = await r.json();
      document.getElementById('ip-addr').textContent   = location.host;
      document.getElementById('conn-status').textContent = '● conectado';
      document.getElementById('conn-status').style.color = '#22c55e';
      atualizarUI(d);
    }
  } catch(e) {
    document.getElementById('conn-status').textContent = '● sem conexão';
    document.getElementById('conn-status').style.color = '#ef4444';
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
    print("[+] Dashboard: http://<IP_DA_RASP>:5000")
