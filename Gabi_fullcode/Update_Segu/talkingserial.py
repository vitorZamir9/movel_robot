#!/usr/bin/env pybricks-micropython
# =============================================================================
#  talkingserial.py — Comunicação serial centralizada EV3 ↔ Raspberry
# =============================================================================
#
#  MENSAGENS QUE A RASPBERRY MANDA (e esta classe parseia):
#  ─────────────────────────────────────────────────────────
#  MPU_Z:{yaw}\n                                    → só yaw (formato simples)
#  [MPU] Roll: X° Pitch: Y° Yaw: Z°\n              → 3 eixos completos
#  obstaculo detectado\n                            → câmera viu obstáculo
#  linha esquerda / direita / ambos / nenhum\n      → lados livres do obstáculo
#  esquerda antes / direita antes\n                 → previsão verde câmera
#  dois verdes\n                                    → beco sem saída
#  verde depois\n                                   → verde após a curva
#  Detected: {cls}\nArea: {area}px\nLado: {lado}\n → bola detectada (YOLO)
#  Area: {cor}\nCentro: {cx}\nLado: {lado}\n        → triângulo detectado
#  frente\n                                         → keepalive (ignorado)
#
#  COMANDOS QUE O EV3 MANDA:
#  ─────────────────────────
#  ts.enviar("bolas")              → b'bolas\r\n'
#  ts.enviar("triangulo")          → b'triangulo\r\n'
#  ts.enviar("obstaculo")          → b'obstaculo\r\n'
#  ts.confirmar_obstaculo()        → b'confirma obstaculo\n'
#  ts.negar_obstaculo()            → b'nega obstaculo\n'
#  ts.set_modo("bolas")            → valida e chama enviar()
#
#  NOMES DOS EIXOS DO GIROSCÓPIO (batem com o código principal):
#  ─────────────────────────────────────────────────────────────
#  ts.gyro_x  → Roll   (inclinação lateral)
#  ts.gyro_y  → Pitch  (inclinação frente/trás — usado para rampa)
#  ts.gyro_z  → Yaw    (rotação horizontal — usado para girar_graus)
#
# =============================================================================

from pybricks.tools import wait


class TalkingSerial:
    """
    Gerencia toda a comunicação serial com a Raspberry Pi.

    ── Uso no loop principal do EV3 (substitui o bloco 1.2 do main): ──────────

        ts = TalkingSerial(ser)
        ts.set_modo("obstaculo")      # avisa a Rasp qual modo ativar

        previsao_camera = None

        while True:
            ev = ts.drenar_principal()       # lê tudo, devolve o que mudou

            gyro_y          = ts.gyro_y      # pitch — usa direto no main
            gyro_z          = ts.gyro_z      # yaw   — usa direto no main

            if ev["obstaculo_pendente"]:     # câmera avisou obstáculo
                ts.confirmar_obstaculo()

            if ev["resultado_linha"]:        # lados disponíveis
                lado = ev["resultado_linha"]

            if ev["previsao_camera"]:        # câmera viu verde no futuro
                previsao_camera = ev["previsao_camera"]

    ── Uso dentro do resgate (Silver, etc.): ──────────────────────────────────

        ts.enviar("bolas")
        ts.limpar()

        while True:
            frame = ts.ler_frame()
            if frame:
                print(frame["detected"], frame["confianca"],
                      frame["lado"], frame["area"])

            ts.girar_graus(180, motorB, motorC)  # usa gyro_z internamente
    """

    # ── Modos reconhecidos ────────────────────────────────────────────────────
    MODOS = ("bolas", "triangulo", "obstaculo")

    def __init__(self, ser, debug=False):
        """
        ser   : UARTDevice do pybricks já configurado
        debug : se True imprime cada linha recebida no console do EV3
        """
        self._ser   = ser
        self._debug = debug
        self._buf   = ""          # buffer de texto incompleto entre chamadas

        # ── Giroscópio — 3 eixos ─────────────────────────────────────────────
        # Nomes alinhados com gyro_rasp_x/y/z do código principal
        self.gyro_x = 0.0    # Roll   — inclinação lateral
        self.gyro_y = 0.0    # Pitch  — inclinação frente/trás (rampa)
        self.gyro_z = 0.0    # Yaw    — rotação horizontal (girar_graus)

        # Aliases para quem preferir os nomes descritivos
        # (são propriedades, atualizadas automaticamente)

        # ── Estado de obstáculo ───────────────────────────────────────────────
        self.obstaculo_pendente    = False   # câmera avisou, ainda não confirmamos
        self.aguardando_linha      = False   # EV3 confirmou, esperando os lados
        self.resultado_linha       = None    # "linha esquerda/direita/ambos/nenhum"

        # ── Previsão de verde (câmera olha à frente) ──────────────────────────
        # Valores possíveis: "esquerda" | "direita" | "beco" | "depois" | None
        self.previsao_camera = None

        # ── Frames de visão (bola / triângulo) ───────────────────────────────
        self._frame_bola      = None
        self._frame_triangulo = None

        # ── Buffer de linhas cruas para frames multi-linha ────────────────────
        self._linhas_raw = []

        # ── Eventos gerados no último drenar_principal() ──────────────────────
        # Resetados a cada chamada de drenar_principal()
        self._ev_obstaculo_pendente = False
        self._ev_resultado_linha    = None
        self._ev_previsao_camera    = None

    # =========================================================================
    #  ALIASES — gyro_x/y/z com nomes descritivos
    # =========================================================================

    @property
    def roll(self):
        """Alias: inclinação lateral (= gyro_x)."""
        return self.gyro_x

    @property
    def pitch(self):
        """Alias: inclinação frente/trás (= gyro_y). Usado para rampa."""
        return self.gyro_y

    @property
    def yaw(self):
        """Alias: rotação horizontal acumulada (= gyro_z). Usado em girar_graus."""
        return self.gyro_z

    # =========================================================================
    #  ENVIO — EV3 → Raspberry
    # =========================================================================

    def enviar(self, cmd):
        """
        Manda qualquer string para a Raspberry (adiciona \\r\\n).

        Exemplos:
            ts.enviar("bolas")
            ts.enviar("triangulo")
            ts.enviar("confirma obstaculo")
        """
        self._ser.write((cmd.strip() + "\r\n").encode())

    def set_modo(self, modo):
        """
        Muda o modo de visão da Raspberry.
        modo: "bolas" | "triangulo" | "obstaculo"
        Valida o nome antes de enviar.
        """
        if modo not in self.MODOS:
            print("[TalkingSerial] Modo desconhecido:", modo)
            return
        self.enviar(modo)

    def confirmar_obstaculo(self):
        """EV3 confirma que também percebeu o obstáculo → Rasp envia os lados."""
        self._ser.write(b"confirma obstaculo\n")
        self.aguardando_linha = True
        self.obstaculo_pendente = False

    def negar_obstaculo(self):
        """EV3 informa que não há obstáculo → Rasp volta para idle."""
        self._ser.write(b"nega obstaculo\n")
        self.obstaculo_pendente = False

    # =========================================================================
    #  LEITURA INTERNA — parseia cada linha recebida
    # =========================================================================

    def _parsear_linha(self, linha):
        """Processa uma linha stripped e atualiza o estado interno."""
        if not linha or linha == "frente":
            return

        if self._debug:
            print("[RX]", linha)

        # ── Formato simples: MPU_Z:{yaw} ─────────────────────────────────────
        if linha.startswith("MPU_Z:"):
            try:
                self.gyro_z = float(linha[6:])
            except ValueError:
                pass
            return

        # ── Formato completo: [MPU] Roll: X° Pitch: Y° Yaw: Z° ───────────────
        if "[MPU]" in linha:
            try:
                self.gyro_x = float(linha.split("Roll: ")[1].split("°")[0])
                self.gyro_y = float(linha.split("Pitch: ")[1].split("°")[0])
                self.gyro_z = float(linha.split("Yaw: ")[1].split("°")[0])
            except (IndexError, ValueError):
                pass
            return

        # ── Obstáculo detectado pela câmera ───────────────────────────────────
        if "obstaculo detectado" in linha:
            self.obstaculo_pendente = True
            self._ev_obstaculo_pendente = True
            print("[TalkingSerial] Câmera: obstáculo detectado!")
            return

        # ── Resultado dos lados da linha ──────────────────────────────────────
        # Só aceita se o EV3 estava aguardando (evita falso positivo)
        if linha.startswith("linha ") and self.aguardando_linha:
            self.resultado_linha    = linha   # "linha esquerda/direita/ambos/nenhum"
            self._ev_resultado_linha = linha
            self.aguardando_linha   = False
            print("[TalkingSerial] Resultado linha:", linha)
            return

        # ── Previsão de verde (câmera olha à frente) ──────────────────────────
        if "esquerda antes" in linha:
            self.previsao_camera    = "esquerda"
            self._ev_previsao_camera = "esquerda"
            print("[TalkingSerial] Previsão câmera: esquerda")
            return
        if "direita antes" in linha:
            self.previsao_camera    = "direita"
            self._ev_previsao_camera = "direita"
            print("[TalkingSerial] Previsão câmera: direita")
            return
        if "dois verdes" in linha:
            self.previsao_camera    = "beco"
            self._ev_previsao_camera = "beco"
            print("[TalkingSerial] Previsão câmera: beco")
            return
        if "verde depois" in linha:
            self.previsao_camera    = "depois"
            self._ev_previsao_camera = "depois"
            print("[TalkingSerial] Previsão câmera: depois")
            return

        # ── Linhas cruas para frames multi-linha (bola / triângulo) ──────────
        self._linhas_raw.append(linha)
        self._tentar_montar_frame()

    def _tentar_montar_frame(self):
        """
        Tenta montar um frame de bola ou triângulo a partir das linhas cruas.
        Remove as linhas consumidas do buffer quando monta com sucesso.
        """
        raw = self._linhas_raw

        # ── Frame de BOLA: Detected / Area(px) / Lado ────────────────────────
        idx_d = idx_a = idx_l = -1
        det_ln = area_ln = lado_ln = None

        for i, ln in enumerate(raw):
            if ln.startswith("Detected:") and idx_d < 0:
                idx_d = i;  det_ln  = ln
            elif ln.startswith("Area:") and "px" in ln and idx_a < 0:
                idx_a = i;  area_ln = ln
            elif ln.startswith("Lado:") and idx_l < 0:
                idx_l = i;  lado_ln = ln

        if det_ln and area_ln and lado_ln:
            try:
                cls_name  = det_ln.split("Detected:")[1].strip()
                area_val  = int(area_ln.split("Area:")[1].replace("px", "").strip())
                lado_val  = lado_ln.split("Lado:")[1].strip()
                confianca = 100.0   # formato antigo da Rasp não envia confiança
            except (IndexError, ValueError):
                cls_name  = ""
                area_val  = 0
                lado_val  = "meio"
                confianca = 0.0

            self._frame_bola = {
                "detected":  cls_name,
                "confianca": confianca,
                "lado":      lado_val,
                "area":      area_val,
            }
            for i in sorted([idx_d, idx_a, idx_l], reverse=True):
                raw.pop(i)
            return

        # ── Frame de TRIÂNGULO: Area(cor) / Centro / Lado ─────────────────────
        idx_c = idx_cen = idx_tl = -1
        cor_ln = cen_ln = tl_ln = None

        for i, ln in enumerate(raw):
            if ln.startswith("Area:") and "px" not in ln and idx_c < 0:
                idx_c = i;   cor_ln = ln
            elif ln.startswith("Centro:") and idx_cen < 0:
                idx_cen = i; cen_ln = ln
            elif ln.startswith("Lado:") and idx_tl < 0:
                idx_tl = i;  tl_ln  = ln

        if cor_ln and cen_ln and tl_ln:
            try:
                cor    = cor_ln.split("Area:")[1].strip()
                centro = int(cen_ln.split("Centro:")[1].strip())
                lado   = tl_ln.split("Lado:")[1].strip()
            except (IndexError, ValueError):
                cor    = "desconhecido"
                centro = 0
                lado   = "meio"

            self._frame_triangulo = {
                "cor":    cor,      # "Vermelho" | "Verde"
                "centro": centro,   # pixel X do centro na imagem
                "lado":   lado,     # "esquerda" | "meio" | "direita"
            }
            for i in sorted([idx_c, idx_cen, idx_tl], reverse=True):
                raw.pop(i)

        # Proteção contra acúmulo infinito de linhas não montadas
        if len(raw) > 20:
            self._linhas_raw = raw[-10:]

    # =========================================================================
    #  API PRINCIPAL
    # =========================================================================

    def drenar(self):
        """
        Lê TUDO que chegou na serial sem bloquear e atualiza o estado interno.
        Chamar a cada iteração de qualquer loop (movimento, giro, etc.).
        Não retorna nada — consulte os atributos após chamar.
        """
        data = self._ser.read_all()
        if not data:
            return
        try:
            self._buf += data.decode("utf-8", "ignore")
        except Exception:
            return

        while "\n" in self._buf:
            linha, self._buf = self._buf.split("\n", 1)
            self._parsear_linha(linha.strip())

    def drenar_principal(self):
        """
        Versão para o loop principal do EV3.

        Substitui o bloco 1.2 inteiro do main.py. Além de drenar a serial,
        devolve um dict com os EVENTOS ocorridos NESTE ciclo — ou seja,
        o que chegou de novo desde a última chamada.

        Retorno:
            {
                "obstaculo_pendente": bool,   → câmera acabou de detectar obstáculo
                "resultado_linha":    str|None, → "linha esquerda/direita/ambos/nenhum"
                "previsao_camera":    str|None, → "esquerda"|"direita"|"beco"|"depois"
            }

        Uso no main:
            ev = ts.drenar_principal()
            gyro_y = ts.gyro_y            # pitch — rampa

            if ev["obstaculo_pendente"]:
                ts.confirmar_obstaculo()
                ...
            if ev["resultado_linha"]:
                resultado = ev["resultado_linha"]
                ...
            if ev["previsao_camera"]:
                previsao_camera = ev["previsao_camera"]
        """
        # Reseta eventos do ciclo anterior
        self._ev_obstaculo_pendente = False
        self._ev_resultado_linha    = None
        self._ev_previsao_camera    = None

        # Processa o que chegou
        self.drenar()

        return {
            "obstaculo_pendente": self._ev_obstaculo_pendente,
            "resultado_linha":    self._ev_resultado_linha,
            "previsao_camera":    self._ev_previsao_camera,
        }

    def ler_frame(self):
        """
        Drena a serial e retorna o frame de visão mais recente (bola ou triângulo).
        Consome o frame — próxima chamada retorna None até chegar um novo.

        Para BOLAS:
            {
                "tipo":      "bola",
                "detected":  "Silver Ball" | "Black Ball" | ...,
                "confianca": float (0–100),
                "lado":      "esquerda" | "meio" | "direita",
                "area":      int (pixels²),
            }

        Para TRIÂNGULOS:
            {
                "tipo":   "triangulo",
                "cor":    "Vermelho" | "Verde",
                "centro": int,
                "lado":   "esquerda" | "meio" | "direita",
            }

        Retorna None se não houver frame novo.
        """
        self.drenar()

        if self._frame_bola is not None:
            frame = dict(self._frame_bola)
            frame["tipo"] = "bola"
            self._frame_bola = None
            return frame

        if self._frame_triangulo is not None:
            frame = dict(self._frame_triangulo)
            frame["tipo"] = "triangulo"
            self._frame_triangulo = None
            return frame

        return None

    def limpar(self):
        """
        Descarta todo o buffer acumulado e reseta frames pendentes.
        Usar ao entrar em um novo modo ou logo após enviar um comando,
        para não processar dados velhos.
        Não apaga o estado do giroscópio nem as flags de obstáculo.
        """
        try:
            self._ser.read_all()
        except Exception:
            pass
        self._buf             = ""
        self._linhas_raw      = []
        self._frame_bola      = None
        self._frame_triangulo = None

    # =========================================================================
    #  PROPRIEDADES DE CONVENIÊNCIA
    # =========================================================================

    @property
    def vendo_bola(self):
        """True se há um frame de bola não consumido disponível."""
        return self._frame_bola is not None

    @property
    def vendo_triangulo(self):
        """True se há um frame de triângulo não consumido disponível."""
        return self._frame_triangulo is not None

    @property
    def lado_bola(self):
        """Lado da última bola não consumida ou None."""
        return self._frame_bola["lado"] if self._frame_bola else None

    @property
    def tipo_bola(self):
        """Classe da última bola não consumida ou None."""
        return self._frame_bola["detected"] if self._frame_bola else None

    @property
    def lado_triangulo(self):
        """Lado do último triângulo não consumido ou None."""
        return self._frame_triangulo["lado"] if self._frame_triangulo else None

    @property
    def cor_triangulo(self):
        """Cor do último triângulo não consumido ou None."""
        return self._frame_triangulo["cor"] if self._frame_triangulo else None

    # =========================================================================
    #  HELPERS BLOQUEANTES
    # =========================================================================

    def aguardar_resultado_linha(self, timeout_ms=3000):
        """
        Bloqueia até receber o resultado dos lados da linha (após confirmar
        um obstáculo) ou até o timeout expirar.

        Retorna: "linha esquerda" | "linha direita" | "linha ambos" |
                 "linha nenhum" | None (timeout)
        """
        elapsed = 0
        while elapsed < timeout_ms:
            self.drenar()
            if self.resultado_linha is not None:
                res = self.resultado_linha
                self.resultado_linha = None
                return res
            wait(50)
            elapsed += 50
        return None

    def aguardar_lado_bola(self, tipo_alvo, timeout_ms=5000):
        """
        Bloqueia até receber um frame de bola que contenha tipo_alvo.
        Retorna o frame ou None (timeout).

        tipo_alvo: substring do cls_name, ex: "Silver" ou "Black"
        """
        elapsed = 0
        while elapsed < timeout_ms:
            frame = self.ler_frame()
            if frame and frame.get("tipo") == "bola":
                if tipo_alvo in frame.get("detected", ""):
                    return frame
            wait(50)
            elapsed += 50
        return None

    def girar_graus(self, angulo, motorB, motorC):
        """
        Gira o robô usando gyro_z (Yaw) da Raspberry como referência.
        Para quando girou abs(angulo) graus a partir da posição atual.

        angulo : graus a girar (positivo = sentido que a Rasp acumula yaw)
        motorB : Motor B (recebe dc(100))
        motorC : Motor C (recebe dc(100))
        """
        # Drena para ter o gyro_z mais recente antes de tarar
        self.drenar()
        yaw_inicio = self.gyro_z

        motorB.dc(100)
        motorC.dc(100)

        while True:
            self.drenar()
            giro_atual = self.gyro_z - yaw_inicio
            if giro_atual >= abs(angulo):
                motorB.stop()
                motorC.stop()
                print("[TalkingSerial] girar_graus OK:", giro_atual)
                break