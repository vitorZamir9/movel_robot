#!/usr/bin/env pybricks-micropython
# =============================================================================
#  silver.py — Módulo de resgate (Silver/Black Ball + Triângulos)
#  Melhorias aplicadas:
#   • enter()      → timeout na detecção do lado (não trava mais)
#   • _varredura() → confirmação em 3 frames antes de capturar
#   • captura      → câmera confirma entrada na garra + ultrad3 valida posse
#   • girar_graus  → corrigido no TalkingSerial (sentido pelo sinal do ângulo)
#   • triangulo()  → usa tanki.turn() com valores calibrados por cor
# =============================================================================

from pybricks.tools import wait
from talkingserial import TalkingSerial

# ── Constantes de ajuste (mude aqui sem tocar na lógica) ─────────────────────
GARRA_ULTRA_MIN   = 10    # ultrad3 mínimo para considerar vítima na garra
GARRA_ULTRA_MAX   = 40   # ultrad3 máximo para considerar vítima na garra
GARRA_CONFIRM_SUM = 100   # somatório de ticks até confirmar posse
ENTER_TIMEOUT_MS  = 3000  # timeout para detectar lado na entrada (ms)

TURN_TRIANGULO_VERDE    = -170   # graus tanki.turn() para depositar no verde
TURN_TRIANGULO_VERMELHO = -170   # graus tanki.turn() para depositar no vermelho


class Silver:
    def __init__(self, tanki, motorB, motorC, sensor1, multiplex1, ev3, ser, servosP):
        self.tanki      = tanki
        self.motorB     = motorB
        self.motorC     = motorC
        self.sensor1    = sensor1
        self.multiplex1 = multiplex1
        self.ev3        = ev3
        self.ser        = ser
        self.servosMove = servosP

        self.talk = TalkingSerial(ser, True)

        # Contadores de vítimas (persistem entre chamadas)
        self.vitimas      = 0
        self.vitimaBLACK  = 0
        self.vitimaSILVER = 0

        self._ler_ultras()

    # ── Leitura centralizada dos ultrassônicos ────────────────────────────────
    def _ler_ultras(self):
        retorno = self.multiplex1.read(0)
        self.ultra1  = retorno[0]   # frente
        self.ultra2  = retorno[1]   # direita
        self.ultrad3 = retorno[2]   # vítima na garra
        self.ultra4  = retorno[3]   # esquerda

    # =========================================================================
    # ENTER — Entrada no resgate, identifica lado da parede (com timeout)
    # =========================================================================
    def enter(self, esqgray1, mindgray1, dirgray1):
        self.tanki.turn(-70)
        self.ev3.speaker.beep(900, 600)
        self.ev3.speaker.beep()
        self.tanki.stop()

        self.talk.enviar("bolas")
        wait(500)

        if not (esqgray1 or mindgray1 or dirgray1):
            return None

        wait(10)
        if not (esqgray1 or mindgray1 or dirgray1):
            return None

        self.tanki.stop()
        print("resgate on")
        self.ev3.speaker.beep()

        # ── Ir para frente até perder a linha ────────────────────────────────
        self.motorB.run(300)
        self.motorC.run(-300)
        while True:
            retorno = self.sensor1.read(2)
            fora1 = retorno[3]
            meio1 = retorno[2]
            meio2 = retorno[1]
            fora2 = retorno[0]
            if fora1 > 90 and meio1 > 90 and meio2 > 90 and fora2 > 90:
                self.tanki.turn(-50)
                self.tanki.stop()
                break
            wait(100)

        # ── Recuar para a esquerda ────────────────────────────────────────────
        self.motorB.run(-300)
        self.motorC.run(0)
        while True:
            retorno = self.sensor1.read(2)
            meio1 = retorno[2]
            if meio1 < 70:
                self.tanki.stop()
                break
            wait(100)

        self.tanki.turn(30)
        self.tanki.stop()
        wait(100)
        print("recuar pra direita")

        # ── Recuar para a direita ─────────────────────────────────────────────
        self.motorB.run(0)
        self.motorC.run(300)
        while True:
            retorno = self.sensor1.read(2)
            meio2 = retorno[1]
            if meio2 > 30:
                self.tanki.stop()
                break
            wait(100)

        # ── Guinada de entrada ────────────────────────────────────────────────
        self.tanki.stop()
        self.tanki.settings(turn_rate=400, turn_acceleration=999)
        self.ev3.speaker.beep(400, 1000)
        self.ev3.speaker.beep(100)
        wait(200)
        self.tanki.turn(150)
        self.tanki.stop()
        wait(1000)

        self.tanki.settings(
            straight_speed=999999, straight_acceleration=999999,
            turn_rate=999999, turn_acceleration=99999
        )
        self.ev3.speaker.beep()
        self.tanki.stop()

        # ── Identificar lado de entrada COM TIMEOUT ───────────────────────────
        # Não trava mais: se não detectar em ENTER_TIMEOUT_MS, retorna None
        entradaR  = None
        elapsed   = 0
        PASSO     = 100   # ms por iteração

        while elapsed < ENTER_TIMEOUT_MS:
            self._ler_ultras()
            print(self.ultra4, self.ultra2)

            if self.ultra4 <= 150 and self.ultra2 >= 150:
                self.tanki.stop()
                print("parede esquerda")
                entradaR = "parede esquerda"
                self.tanki.straight(10)
                self.tanki.stop()
                break
            elif self.ultra4 >= 150 and self.ultra2 <= 150:
                self.tanki.stop()
                print("parede direita")
                entradaR = "parede direita"
                self.tanki.straight(-10)
                self.tanki.stop()
                break
            elif self.ultra4 > 150 and self.ultra2 > 150:
                self.tanki.stop()
                print("parede meeeio")
                entradaR = "parede meeeio"
                break

            wait(PASSO)
            elapsed += PASSO

        if entradaR is None:
            print("[enter] timeout — lado não identificado, continuando")

        wait(1000)
        self.tanki.stop()
        self.tanki.settings(
            straight_speed=999999, straight_acceleration=999999,
            turn_rate=999999, turn_acceleration=99999
        )
        return entradaR

    # =========================================================================
    # girar_graus — delegado ao TalkingSerial (já corrigido lá)
    # =========================================================================
    def girar_graus(self, angulo):
        self.talk.girar_graus(angulo, self.motorB, self.motorC)

    # =========================================================================
    # _alinhar_camera — Gira até a vítima ficar no meio
    # =========================================================================
    def _alinhar_camera(self, lapooo, vendoVITIMA):
        parado = 0
        while True:
            frame = self.talk.ler_frame()
            if frame:
                lado = frame["lado"]
                if lado == "meio":
                    print("Alinhado com a vítima!")
                    self.tanki.stop()
                    self.ev3.speaker.beep(800)
                    return True
                if lado == "esquerda":
                    self.motorB.dc(-90)
                    self.motorC.dc(-90)
                elif lado == "direita":
                    self.motorB.dc(90)
                    self.motorC.dc(90)
                wait(50)
                self.motorB.stop()
                self.motorC.stop()
            else:
                wait(300)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if parado > 10:
                    print("não está conseguindo ver vítima")
                    self.motorB.dc(-50)
                    self.motorC.dc(50)
                wait(300)
                if lapooo == "esquerda":
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(-90)
                    self.motorC.dc(-90)
                    while True:
                        wait(50)
                        if self.tanki.state()[3] < 20:
                            parado += 1
                        if self.tanki.state()[3] > 60:
                            parado = 0
                        if self.motorB.angle() <= -60 or parado > 20:
                            self.tanki.stop()
                            break
                    self.tanki.stop()
                elif lapooo == "direita":
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(90)
                    self.motorC.dc(90)
                    while True:
                        wait(50)
                        if self.tanki.state()[3] < 20:
                            parado += 1
                        if self.tanki.state()[3] > 60:
                            parado = 0
                        if self.motorB.angle() >= 60 or parado > 20:
                            self.tanki.stop()
                            break
                    self.tanki.stop()

    # =========================================================================
    # _confirmar_entrada_garra — câmera vê se a vítima entrou na área da garra
    # Retorna True se confirmou, False se não viu em TIMEOUT_MS
    # =========================================================================
    def _confirmar_entrada_garra(self, tipo, timeout_ms=3000):
        """
        Drena frames enquanto avança devagar.
        Retorna True quando a câmera confirma que a vítima está na área de captura
        (lado == 'meio' E área grande o suficiente) ou quando timeout esgota.
        """
        elapsed = 0
        PASSO   = 100
        while elapsed < timeout_ms:
            frame = self.talk.ler_frame()
            if frame and tipo in frame.get("detected", ""):
                lado = frame["lado"]
                area = frame["area"]
                print("[garra-cam] lado:", lado, "area:", area)
                # Vítima centralizada e grande → está na boca da garra
                if lado == "meio" and area >= 3000:
                    print("[garra-cam] vítima confirmada na área da garra!")
                    return True
            wait(PASSO)
            elapsed += PASSO
        print("[garra-cam] timeout — prosseguindo mesmo assim")
        return False

    # =========================================================================
    # _validar_posse_ultrad3 — somatório de ticks com vítima detectada
    # Retorna True se ultrad3 ficou dentro da janela por GARRA_CONFIRM_SUM ticks
    # =========================================================================
    def _validar_posse_ultrad3(self):
        soma  = 0
        TICKS = 150   # total de ticks de polling
        for _ in range(TICKS):
            self._ler_ultras()
            self.talk.drenar()
            print("[ultrad3]", self.ultrad3)
            if GARRA_ULTRA_MIN < self.ultrad3 < GARRA_ULTRA_MAX:
                soma += 1
            wait(20)
        print("[ultrad3] soma:", soma, "/ necessário:", GARRA_CONFIRM_SUM)
        return soma >= GARRA_CONFIRM_SUM

    # =========================================================================
    # _pegar_vitima — Sequência de garra para uma vítima
    # Inclui: confirmação por câmera + validação ultrad3 + retry se falhar
    # =========================================================================
    def _pegar_vitima(self, vitima, vendoVITIMA):
        MAX_TENTATIVAS = 5

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            print("[pegar] tentativa", tentativa)

            self.tanki.turn(-50)
            self.tanki.stop()

            # Abre a garra
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            self.servosMove.move(1, 250)
            self.servosMove.move(2, 0)
            self.servosMove.move(3, 60)
            wait(1000)

            # ── Avançar devagar enquanto câmera confirma entrada ──────────────
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.motorB.dc(60)
            self.motorC.dc(-60)

            cam_confirmou = False
            elapsed_cam   = 0
            while True:
                self.talk.drenar()
                wait(100)
                elapsed_cam += 100

                # Checa câmera para confirmar entrada na garra
                frame = self.talk.ler_frame()
                if frame and vendoVITIMA in frame.get("detected", ""):
                    lado = frame["lado"]
                    area = frame["area"]
                    print("[cam-avanco] lado:", lado, "area:", area)
                    if lado == "meio" and area >= 3000:
                        cam_confirmou = True
                        self.tanki.stop()
                        print("[cam-avanco] vítima na área — parando para fechar garra")
                        break

                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0

                # Limite por ângulo ou robô travado
                if self.motorB.angle() >= 200 or parado > 20:
                    self.tanki.stop()
                    break

            self.tanki.stop()

            # ── Fechar a garra ────────────────────────────────────────────────
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            self.servosMove.move(2, 60)
            self.servosMove.move(3, 0)
            wait(100)
            self.servosMove.move(4, 40)
            self.servosMove.move(1, 0)
            wait(500)
            self.tanki.turn(-80)
            self.tanki.stop()

            # ── Validar posse com ultrad3 ─────────────────────────────────────
            tem_vitima = self._validar_posse_ultrad3()

            if tem_vitima:
                print("[pegar] vítima confirmada pela garra!")
                break
            else:
                print("[pegar] vítima NÃO detectada pela garra — retry")
                # Abre a garra e recua para tentar de novo
                self.servosMove.move(1, 250)
                self.servosMove.move(3, 60)
                wait(500)
                self.tanki.turn(-60)   # recua abrindo espaço
                self.tanki.stop()
                wait(300)

                if tentativa == MAX_TENTATIVAS:
                    print("[pegar] máximo de tentativas atingido — desistindo")

        # ── Classificar e depositar ───────────────────────────────────────────
        if vendoVITIMA == "Black Ball":
            self._separar_black()
            self.vitimaBLACK += 1
            self.vitimas += 1
        elif vendoVITIMA == "Silver Ball":
            self._separar_silver()
            self.vitimaSILVER += 1
            self.vitimas += 1

        print("vitimas_final:", self.vitimas,
              "Black:", self.vitimaBLACK,
              "Silver:", self.vitimaSILVER)

    # =========================================================================
    # _separar_black — Deposita vítima morta (Black Ball)
    # =========================================================================
    def _separar_black(self):
        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        wait(500)
        self.servosMove.move(3, 60)
        self.servosMove.move(2, 45)
        wait(200)
        self.servosMove.move(2, 20)
        wait(200)
        self.servosMove.move(2, 60)
        wait(200)
        self.servosMove.move(2, 20)
        wait(200)
        self.servosMove.move(2, 60)
        wait(200)
        self.servosMove.move(2, 20)
        wait(200)
        self.servosMove.move(1, 5)
        wait(200)
        self.servosMove.move(2, 0)
        self.servosMove.move(3, 60) # abriu tudo pra
        wait(200)
        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        wait(200)
        self.servosMove.move(1, 10)
        wait(200)
        self.servosMove.move(1, 0)
        wait(200)
        self.servosMove.move(1, 5)
        self.servosMove.move(2, 0)
        self.servosMove.move(3, 60)
        wait(200)
        self.servosMove.move(1, 0)
        wait(200)

    # =========================================================================
    # _separar_silver — Deposita vítima viva (Silver Ball)
    # =========================================================================
    def _separar_silver(self):
        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        wait(500)
        self.servosMove.move(2, 0)
        self.servosMove.move(3, 15)
        wait(200)
        self.servosMove.move(3, 30)
        wait(200)
        self.servosMove.move(3, 0)
        wait(200)
        self.servosMove.move(3, 30)
        wait(200)
        self.servosMove.move(3, 0)
        wait(200)
        self.servosMove.move(3, 20)
        wait(200)
        self.servosMove.move(1, 5)
        wait(200)
        self.servosMove.move(2, 0)
        self.servosMove.move(3, 60) # abriu tudo
        wait(200)
        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        wait(200)
        self.servosMove.move(1, 10)
        wait(200)
        self.servosMove.move(1, 0)
        wait(200)
        self.servosMove.move(1, 5)
        self.servosMove.move(2, 0)
        self.servosMove.move(3, 60)
        wait(200)
        self.servosMove.move(1, 0)
        wait(200)


    # =========================================================================
    # _varredura — Loop de detecção, confirmação em 3 frames, coleta
    # tipo: "Silver Ball" | "Black Ball"
    # =========================================================================
    def _varredura(self, tipo):
        semvitima     = 0
        sairdoRESGATE = None

        self.talk.limpar()

        while True:
            print("vitimas_inicio:", self.vitimas,
                  "Black:", self.vitimaBLACK,
                  "Silver:", self.vitimaSILVER)

            # ── Condição de saída ─────────────────────────────────────────────
            if tipo == "Silver Ball" and self.vitimaSILVER >= 2:
                self.tanki.stop()
                sairdoRESGATE = 0
                break
            if tipo == "Black Ball" and self.vitimaBLACK >= 1:
                self.tanki.stop()
                sairdoRESGATE = 0
                break

            wait(500)
            self.talk.enviar("bolas")
            self.talk.limpar()
            wait(1000)

            # ── Loop: detectar vítima do tipo certo (FRAME 1) ─────────────────
            lapooo      = None
            vendoVITIMA = None
            pxvitima    = None

            vitima_encontrada = False

            while not vitima_encontrada:
                frame1 = self.talk.ler_frame()

                if frame1:
                    detected  = frame1.get("detected", "")
                    confianca = frame1.get("confianca", 0)
                    lado1     = frame1.get("lado", "")
                    area1     = frame1.get("area", 0)
                    print("FRAME1:", detected, confianca, lado1, area1)

                    if confianca > 50.0 and tipo in detected:
                        # ── PARA imediatamente ────────────────────────────────
                        self.tanki.stop()
                        self.ev3.speaker.beep(500 if "Black" in detected else 200)
                        print("[varredura] frame1 OK — aguardando confirmação")
                        wait(200)

                        # ── FRAME 2: confirmação ──────────────────────────────
                        self.talk.limpar()
                        wait(500)
                        frame2 = self.talk.ler_frame()
                        confirmado = False
                        if frame2 and tipo in frame2.get("detected", ""):
                            confirmado = True
                            lado2 = frame2.get("lado", lado1)
                            area2 = frame2.get("area", area1)
                            print("[varredura] frame2 confirmado:", lado2, area2)
                        else:
                            print("[varredura] frame2 não confirmou — continuando busca")
                            lado2 = lado1
                            area2 = area1

                        if not confirmado:
                            # Falso positivo — volta a buscar
                            continue

                        # ── FRAME 3: alinhamento fino ─────────────────────────
                        wait(500)
                        frame3 = self.talk.ler_frame()
                        if frame3 and tipo in frame3.get("detected", ""):
                            lado_final = frame3.get("lado", lado2)
                            area_final = frame3.get("area", area2)
                            print("[varredura] frame3 alinhamento:", lado_final, area_final)
                        else:
                            lado_final = lado2
                            area_final = area2
                            print("[varredura] frame3 ausente — usando frame2")

                        lapooo      = lado_final
                        vendoVITIMA = detected.split(',')[0] if ',' in detected else detected
                        pxvitima    = area_final
                        vitima_encontrada = True

                        # Ajuste fino de alinhamento com base no frame3
                        if lado_final == "esquerda":
                            self.motorB.dc(-60)
                            self.motorC.dc(-60)
                            wait(80)
                            self.tanki.stop()
                        elif lado_final == "direita":
                            self.motorB.dc(60)
                            self.motorC.dc(60)
                            wait(80)
                            self.tanki.stop()

                else:
                    # ── Sem detecção: gira um pouco e tenta de novo ───────────
                    wait(500)
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(100)
                    self.motorC.dc(100)
                    while True:
                        self.talk.drenar()
                        wait(50)
                        print(self.motorB.angle(), self.motorC.angle(), semvitima)
                        if self.motorB.angle() >= 35:
                            self.tanki.stop()
                            semvitima += 1
                            break
                    self.tanki.stop()

                    if semvitima == 75:
                        print("tentando ir no meio do resgate")
                        # tentar ir no meio do resgate
                        self.motorB.reset_angle(0)
                        self.motorC.reset_angle(0)
                        wait(100)
                        self.motorB.dc(60)
                        self.motorC.dc(-60)
                        while True:
                            self.talk.drenar()
                            retorno1  = self.multiplex1.read(0)
                            ChoqueESQ = retorno1[4]
                            ChoqueDIR = retorno1[7]
                            wait(50)
                            print(self.motorB.angle(), self.motorC.angle(), semvitima)
                            if self.motorB.angle() >= 400 or parado > 20:
                                self.tanki.stop()
                                semvitima += 1
                                break
                            if self.tanki.state()[3] < 20:
                                parado += 1
                            if self.tanki.state()[3] > 60:
                                parado = 0
                            if ChoqueDIR == 1:
                                self.tanki.stop()
                                self.tanki.straight(-90)
                                self.tanki.stop()
                            if ChoqueESQ == 1:
                                self.tanki.stop()
                                self.tanki.straight(90)
                                self.tanki.stop()
                        self.tanki.stop()
                    
                    if semvitima >= 150:
                        print("não tem vítima")
                        self.vitimas      = 10
                        self.vitimaBLACK  = 10
                        self.vitimaSILVER = 10
                        sairdoRESGATE     = 1
                        break

                    wait(500)

            if sairdoRESGATE == 1:
                self.exit()
                break

            # ── Alinhar câmera com a vítima (se necessário) ───────────────────
            self.tanki.stop()
            wait(500)
            self.ev3.speaker.beep()
            self.tanki.stop()
            wait(100)
            self.talk.limpar()
            self.tanki.settings(
                straight_speed=999999, straight_acceleration=9999999,
                turn_rate=9999999, turn_acceleration=99999999
            )
            wait(300)
            print("alinhar")

            if lapooo != "meio":
                self._alinhar_camera(lapooo, vendoVITIMA)

            # ── Aproximar da vítima usando ultra1 + pxvitima ─────────────────
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()

            # Define quanto avançar baseado nos px E na distância real
            self._ler_ultras()
            dist_frente = self.ultra1

            if pxvitima >= 2500 or dist_frente <= 80:
                # Já está perto o suficiente — vai direto para captura
                prafrente = 10
            elif dist_frente <= 150:
                prafrente = 100
            else:
                prafrente = 200

            print("[aprox] pxvitima:", pxvitima, "ultra1:", dist_frente,
                  "→ prafrente:", prafrente)

            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.motorB.dc(60)
            self.motorC.dc(-60)
            while True:
                self.talk.drenar()
                wait(100)
                self._ler_ultras()   # atualiza ultra1 durante o avanço
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                # Para se chegou perto o suficiente pelo ultrassônico
                if self.ultra1 <= 60:
                    self.tanki.stop()
                    print("[aprox] ultra1 ≤ 60 — parando")
                    break
                if self.motorB.angle() >= prafrente or parado > 20:
                    self.tanki.stop()
                    break
            self.tanki.stop()
            wait(500)

            # ── Capturar se vítima está na área (px ou ultra1) ───────────────
            self._ler_ultras()
            if pxvitima >= 2500 or self.ultra1 <= 80:
                self.tanki.stop()
                self._pegar_vitima(vendoVITIMA + "," + lapooo, vendoVITIMA)

        return {
            "vitimas":       self.vitimas,
            "black":         self.vitimaBLACK,
            "silver":        self.vitimaSILVER,
            "sairdoRESGATE": sairdoRESGATE,
        }

    # =========================================================================
    # clawLife — Varredura para pegar SOMENTE Silver Ball (viva)
    # =========================================================================
    def clawLife(self):
        print("=== clawLife: procurando Silver Ball ===")
        return self._varredura("Silver Ball")

    # =========================================================================
    # clawDead — Varredura para pegar SOMENTE Black Ball (morta)
    # =========================================================================
    def clawDead(self):
        print("=== clawDead: procurando Black Ball ===")
        return self._varredura("Black Ball")

    # =========================================================================
    # triangulo — Identifica e entrega nos triângulos verde/vermelho
    # Giro de posicionamento agora usa tanki.turn() com valores calibrados
    # =========================================================================
    def triangulo(self):
        vendoTRIANGULO         = 0
        vendoTRIANGULOVERDE    = 0
        vendoTRIANGULOVERMELHO = 0
        vendoTRIANGULOcor      = None

        while True:
            print("triangulos_inicial: verde:", vendoTRIANGULOVERDE,
                  "vermelho:", vendoTRIANGULOVERMELHO)

            if (vendoTRIANGULO >= 2
                    and vendoTRIANGULOVERDE >= 1
                    and vendoTRIANGULOVERMELHO >= 1):
                self.tanki.stop()
                self.ev3.speaker.beep(900, 10000)
                print("procurar saida")
                break

            self.tanki.stop()
            wait(500)
            self.talk.set_modo("triangulo")
            self.talk.limpar()
            wait(500)

            # ── Detectar e alinhar com o triângulo ───────────────────────────
            while True:
                frame = self.talk.ler_frame()

                if frame and frame.get("tipo") == "triangulo":
                    cor  = frame["cor"]
                    lado = frame["lado"]
                    print("Alinhando com triângulo. Cor:", cor, "Lado:", lado)

                    while lado != "meio":
                        if lado == "esquerda":
                            self.motorB.dc(-900)
                            self.motorC.dc(-900)
                        elif lado == "direita":
                            self.motorB.dc(900)
                            self.motorC.dc(900)
                        wait(50)
                        self.motorB.stop()
                        self.motorC.stop()
                        prox = self.talk.ler_frame()
                        if prox and prox.get("tipo") == "triangulo":
                            lado = prox["lado"]
                            cor  = prox["cor"]

                    self.ev3.speaker.beep(400)
                    if cor == "Vermelho":
                        vendoTRIANGULOcor = "vermelho"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERMELHO += 1
                    elif cor == "Verde":
                        vendoTRIANGULOcor = "verde"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERDE += 1
                    self.tanki.stop()
                    break

                else:
                    print("Não vendo triângulo")
                    wait(250)
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(100)
                    self.motorC.dc(100)
                    while True:
                        wait(100)
                        if self.motorB.angle() >= 30:
                            self.tanki.stop()
                            break
                    self.tanki.stop()
                    wait(300)

            # ── Ir até o triângulo ────────────────────────────────────────────
            self.tanki.stop()
            wait(100)
            retorno1  = self.multiplex1.read(0)
            ChoqueESQ = retorno1[4]
            ChoqueDIR = retorno1[7]

            if vendoTRIANGULO >= 1:
                print("ir pro triangulo")
                parado = 0
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)
                self.motorB.dc(100)
                self.motorC.dc(-100)
                while True:
                    self.talk.drenar()
                    retorno1  = self.multiplex1.read(0)
                    ChoqueESQ = retorno1[4]
                    ChoqueDIR = retorno1[7]
                    wait(100)
                    print(self.motorB.angle(), self.motorC.angle(),
                          self.tanki.state()[3], "parado:", parado,
                          ChoqueESQ, ChoqueDIR)
                    if self.tanki.state()[3] < 20:
                        parado += 1
                    if self.tanki.state()[3] > 60:
                        parado = 0
                    if parado > 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                self.tanki.turn(-150)
                self.tanki.stop()

                # ── Confirmar triângulo após aproximação ──────────────────────
                while True:
                    frame = self.talk.ler_frame()

                    if frame and frame.get("tipo") == "triangulo":
                        cor  = frame["cor"]
                        lado = frame["lado"]
                        print("Confirmando triângulo. Cor:", cor, "Lado:", lado)

                        while lado != "meio":
                            if lado == "esquerda":
                                self.motorB.dc(-900)
                                self.motorC.dc(-900)
                            elif lado == "direita":
                                self.motorB.dc(900)
                                self.motorC.dc(900)
                            wait(50)
                            self.motorB.stop()
                            self.motorC.stop()
                            prox = self.talk.ler_frame()
                            if prox and prox.get("tipo") == "triangulo":
                                lado = prox["lado"]
                                cor  = prox["cor"]

                        self.ev3.speaker.beep(400)
                        if cor == "Vermelho":
                            vendoTRIANGULOcor = "vermelho"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERMELHO += 1
                        elif cor == "Verde":
                            vendoTRIANGULOcor = "verde"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERDE += 1
                        self.tanki.stop()
                        break

                    else:
                        print("Não vendo triângulo")
                        wait(250)
                        self.motorB.reset_angle(0)
                        self.motorC.reset_angle(0)
                        wait(100)
                        self.motorB.dc(100)
                        self.motorC.dc(100)
                        while True:
                            wait(100)
                            if self.motorB.angle() >= 30:
                                self.tanki.stop()
                                break
                        self.tanki.stop()
                        wait(300)

                # ── Segunda ida ao triângulo ──────────────────────────────────
                parado = 0
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)
                self.motorB.dc(100)
                self.motorC.dc(-100)
                while True:
                    self.talk.drenar()
                    retorno1  = self.multiplex1.read(0)
                    ChoqueESQ = retorno1[4]
                    ChoqueDIR = retorno1[7]
                    wait(100)
                    print(self.motorB.angle(), self.motorC.angle(),
                          self.tanki.state()[3], "parado:", parado,
                          ChoqueESQ, ChoqueDIR)
                    if self.tanki.state()[3] < 20:
                        parado += 1
                    if self.tanki.state()[3] > 60:
                        parado = 0
                    if parado >= 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                self.tanki.turn(-150)
                self.tanki.stop()
                self.motorB.stop()
                self.motorC.stop()
                wait(300)

                # ── Posicionar para depositar ─────────────────────────────────
                # ANTES: girar_graus(180) — travava e girava errado
                # AGORA: tanki.straight() com valor calibrado por cor
                print("[triangulo] posicionando para depositar — cor:", vendoTRIANGULOcor)
                if vendoTRIANGULOcor == "verde":
                    self.tanki.straight(TURN_TRIANGULO_VERDE)
                elif vendoTRIANGULOcor == "vermelho":
                    self.tanki.straight(TURN_TRIANGULO_VERMELHO)
                self.tanki.stop()
                wait(300)

                print(vendoTRIANGULOcor, vendoTRIANGULOVERDE, vendoTRIANGULOVERMELHO)
                wait(1000)

                # ── Depositar no triângulo ────────────────────────────────────
                if vendoTRIANGULOcor == "verde":
                    self._depositar_triangulo(abertura_servo=30,  fechamento_servo=60)
                elif vendoTRIANGULOcor == "vermelho":
                    self._depositar_triangulo(abertura_servo=0, fechamento_servo=60)

            print("triangulos_final: verde:", vendoTRIANGULOVERDE,
                  "vermelho:", vendoTRIANGULOVERMELHO)

    # =========================================================================
    # _depositar_triangulo — Abre servo, faz ciclos frente/trás
    # =========================================================================
    def _depositar_triangulo(self, abertura_servo, fechamento_servo):
        parado = 0
        self.tanki.stop()
        self.motorB.reset_angle(0)
        self.motorC.reset_angle(0)
        wait(500)
        self.motorB.dc(-100)
        self.motorC.dc(100)
        wait(1000)
        while True:
            self.talk.drenar()
            wait(50)
            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if self.motorB.angle() <= -1000 or parado > 20:
                self.tanki.stop()
                break

        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        wait(500)
        self.servosMove.move(5, abertura_servo)
        wait(1000)

        for c in range(1, 4):
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            wait(500)
            self.servosMove.move(4, fechamento_servo)
            wait(500)
            self.motorB.dc(100)
            self.motorC.dc(-100)
            print("pra frente")
            while True:
                self.talk.drenar()
                wait(50)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if self.motorB.angle() >= 100 or parado > 20:
                    self.tanki.stop()
                    break
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()
            wait(100)
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.motorB.dc(-100)
            self.motorC.dc(100)
            wait(200)
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            wait(100)
            self.servosMove.move(4, abertura_servo)
            print("pra tras")
            while True:
                self.talk.drenar()
                wait(50)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if self.motorB.angle() <= -1000 or parado > 20:
                    self.tanki.stop()
                    break
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()

        self.servosMove.move(4, fechamento_servo)
        self.tanki.turn(150)
        self.tanki.stop()

    # =========================================================================
    # exit — Sair do resgate
    # =========================================================================
    def exit(self,esqgray1,mindgray1,dirgray1):
        print("sair do resgate")
        retorno = self.sensor1.read(2)
        fora1 = retorno[3]
        meio1 = retorno[2]
        meio2 = retorno[1]
        fora2 = retorno[0]
        retorno1  = self.multiplex1.read(0)
        ChoqueESQ = retorno1[4]
        ChoqueDIR = retorno1[7]
        self._ler_ultras()
        linha_preta = fora1<30 or meio1<30 or meio2<30 or fora2<30
        linha_prata = esqgray1 or mindgray1 or dirgray1

        self.tanki.stop()
        self.talk.girar_graus(90,self.motorB,self.motorC)
        self.tanki.stop()
        while True:
            self.tanki.stop()
            retorno = self.sensor1.read(2)
            fora1 = retorno[3]
            meio1 = retorno[2]
            meio2 = retorno[1]
            fora2 = retorno[0]
            retorno1  = self.multiplex1.read(0)
            ChoqueESQ = retorno1[4]
            ChoqueDIR = retorno1[7]
            self._ler_ultras()
            if self.ultra2 >= 180 or linha_preta:
                print("sem parede")
                self.tanki.stop()
                #verifica se tem linha preta ou prata
                while True:
                    self.tanki.stop()
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[3]
                    meio1 = retorno[2]
                    meio2 = retorno[1]
                    fora2 = retorno[0]
                    retorno1  = self.multiplex1.read(0)
                    ChoqueESQ = retorno1[4]
                    ChoqueDIR = retorno1[7]
                    self._ler_ultras()
                    if linha_preta:
                        self.motorB.dc(50)
                        self.motorC.dc(-50)
                        while True:
                            retorno = self.sensor1.read(2)
                            fora1 = retorno[3]
                            meio1 = retorno[2]
                            meio2 = retorno[1]
                            fora2 = retorno[0]
                            if meio1<meio2 or meio1>meio2:
                                self.tanki.stop()
                                self.tanki.turn(90)
                                self.tanki.stop()
                                return
            self.motorB.dc(60)
            self.motorC.dc(-60) #frente
            if ChoqueESQ == 1 or ChoqueDIR == 1:
                self.tanki.stop()
                self.tanki.straight(-30)
                self.tanki.stop()
            if linha_prata:
                wait(10)
                if linha_prata:
                    self.tanki.stop()
                    self.tanki.turn(-150)
                    self.tanki.straight(-120)
                    self.tanki.stop()
            wait(10)