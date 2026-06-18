#!/usr/bin/env pybricks-micropython
from pybricks.tools import wait
from talkingserial import TalkingSerial


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
        # ── Módulo serial centralizado ────────────────────────────────────────
        self.talk = TalkingSerial(ser, True)

        # Contadores de vítimas (persistem entre chamadas)
        self.vitimas      = 0
        self.vitimaBLACK  = 0
        self.vitimaSILVER = 0
        self.ultra1 = self.multiplex1.read(0)[0] # frente
        self.ultra2 = self.multiplex1.read(0)[1] # direita
        self.ultrad3 = self.multiplex1.read(0)[2] # vitima
        self.ultra4 = self.multiplex1.read(0)[3] # esquerda


    # =========================================================
    # ENTER — Entrada no resgate, identifica lado da parede
    # =========================================================
    def enter(self, esqgray, mindgray, dirgray, esqgray1, mindgray1, dirgray1):
        self.tanki.turn(70)
        self.ev3.speaker.beep(900, 600)
        self.ev3.speaker.beep()
        self.tanki.stop()

        self.talk.enviar("bolas")   # avisa a Rasp para modo bolas
        wait(500)

        if esqgray or mindgray or dirgray or esqgray1 or mindgray1 or dirgray1:
            wait(10)
            if esqgray or mindgray or dirgray or esqgray1 or mindgray1 or dirgray1:
                self.tanki.stop()
                print("resgate on")
                self.ev3.speaker.beep()

                # Ir para frente até perder a linha
                self.motorB.run(300)
                self.motorC.run(-300)
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[3] # esquerda 
                    meio1 = retorno[2] # esquerda 
                    meio2 = retorno[1] # direita  
                    fora2 = retorno[0] # direita  
                    if fora1 > 90 and meio1 > 90 and meio2 > 90 and fora2 > 90:
                        self.tanki.turn(-50)
                        self.tanki.stop()
                        break
                    wait(100)

                # Recuar para a esquerda
                self.motorB.run(-300)
                self.motorC.run(0)
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[3] # esquerda 
                    meio1 = retorno[2] # esquerda 
                    meio2 = retorno[1] # direita  
                    fora2 = retorno[0] # direita  
                    if meio1 < 70:
                        self.tanki.stop()
                        break
                    wait(100)

                self.tanki.turn(30)
                self.tanki.stop()
                wait(100)
                print("recuar pra direita")

                # Recuar para a direita
                self.motorB.run(0)
                self.motorC.run(300)
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[3] # esquerda 
                    meio1 = retorno[2] # esquerda 
                    meio2 = retorno[1] # direita  
                    fora2 = retorno[0] # direita  
                    if meio2 > 30:
                        self.tanki.stop()
                        break
                    wait(100)

                # Entrar no resgate (guinada)
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

                # Identificar posição de entrada (parede esquerda / direita / meio)
                entradaR = ""
                while True:
                    self.ultra1 = self.multiplex1.read(0)[0] # frente
                    self.ultra2 = self.multiplex1.read(0)[1] # direita
                    self.ultrad3 = self.multiplex1.read(0)[2] # vitima
                    self.ultra4 = self.multiplex1.read(0)[3] # esquerda
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

                wait(1000)
                self.tanki.stop()
                self.tanki.settings(
                    straight_speed=999999, straight_acceleration=999999,
                    turn_rate=999999, turn_acceleration=99999
                )
                return entradaR

        return None  # Não era prata de verdade

    # =========================================================
    # girar_graus — delegado ao TalkingSerial
    # =========================================================
    def girar_graus(self, angulo):
        self.talk.girar_graus(angulo, self.motorB, self.motorC)

    # =========================================================
    # _alinhar_camera — Gira até a vítima ficar no meio
    # =========================================================
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

    # =========================================================
    # _pegar_vitima — Sequência de garra para uma vítima
    # =========================================================
    def _pegar_vitima(self, vitima, vendoVITIMA):
        self.tanki.turn(-50)
        self.tanki.stop()

        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)

        self.servosMove.move(1, 250)
        self.servosMove.move(3, 90)
        self.servosMove.move(4, 0)
        wait(1000)

        # Andar para pegar a vítima
        parado = 0
        self.motorB.reset_angle(0)
        self.motorC.reset_angle(0)
        wait(100)
        self.motorB.dc(60)
        self.motorC.dc(-60)
        while True:
            self.talk.drenar()   # mantém serial drenada durante o avanço
            wait(100)
            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if self.motorB.angle() >= 200 or parado > 20:
                self.tanki.stop()
                break
        self.tanki.stop()

        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        self.servosMove.move(3, 0)
        self.servosMove.move(4, 90)
        wait(100)
        self.servosMove.move(5, 40)
        self.servosMove.move(1, 5)
        wait(500)
        self.tanki.turn(-80)
        self.tanki.stop()

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

    # =========================================================
    # _separar_black — Deposita vítima morta (Black Ball)
    # =========================================================
    def _separar_black(self):
        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        wait(500)
        self.servosMove.move(5, 40)
        self.servosMove.move(3, 0)
        self.servosMove.move(4, 90)
        wait(1000)
        self.servosMove.move(1, 5)
        wait(1000)
        self.servosMove.move(3, 90)
        self.servosMove.move(4, 65)
        wait(1000)
        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        wait(100)
        self.servosMove.move(1, 10)
        wait(100)
        self.servosMove.move(1, 0)
        wait(1000)
        self.servosMove.move(1, 5)
        self.servosMove.move(3, 90)
        self.servosMove.move(4, 0)
        wait(100)
        self.servosMove.move(1, 0)
        wait(500)

    # =========================================================
    # _separar_silver — Deposita vítima viva (Silver Ball)
    # =========================================================
    def _separar_silver(self):
        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        wait(500)
        self.servosMove.move(5, 40)
        self.servosMove.move(3, 0)
        self.servosMove.move(4, 90)
        wait(1000)
        self.servosMove.move(1, 5)
        wait(1000)
        self.servosMove.move(4, 0)
        self.servosMove.move(3, 10)
        wait(1000)
        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        wait(100)
        self.servosMove.move(1, 10)
        wait(100)
        self.servosMove.move(1, 0)
        wait(1000)
        self.servosMove.move(1, 10)
        self.servosMove.move(3, 90)
        self.servosMove.move(4, 0)
        wait(100)
        self.servosMove.move(1, 0)
        wait(500)

    # =========================================================
    # _varredura — Loop de detecção, alinhamento e coleta
    # tipo: "Silver Ball" (viva) ou "Black Ball" (morta)
    # =========================================================
    def _varredura(self, tipo):
        semvitima     = 0
        sairdoRESGATE = None

        # Descarta leituras velhas antes de começar
        self.talk.limpar()

        while True:
            print("vitimas_inicio:", self.vitimas,
                  "Black:", self.vitimaBLACK,
                  "Silver:", self.vitimaSILVER)

            # Condição de saída: pegou a vítima do tipo pedido
            if tipo == "Silver Ball" and self.vitimaSILVER >= 2:
                self.tanki.stop()
                sairdoRESGATE = 0
                break
            if tipo == "Black Ball" and self.vitimaBLACK >= 1:
                self.tanki.stop()
                sairdoRESGATE = 0
                break

            wait(500)
            self.talk.enviar("bolas")   # garante que a Rasp está no modo certo
            self.talk.limpar()
            wait(1000)

            # ---- Loop: detectar a vítima do tipo certo ----
            vitima     = None
            lapooo     = None
            vendoVITIMA = None
            pxvitima   = None
            javiuantes = None

            while True:
                frame = self.talk.ler_frame()
                if frame:
                    print("zamir")
                    detected  = frame["detected"]
                    confianca = frame["confianca"]
                    lado      = frame["lado"]
                    area      = frame["area"]

                    print("DETECTADO:", detected, confianca, lado, area)

                    if confianca > 60.0 and tipo in detected:
                        lapooo      = lado
                        vendoVITIMA = detected.split(',')[0] if ',' in detected else detected
                        pxvitima    = area

                        if lado == "meio":
                            javiuantes = "meio"
                            self.ev3.speaker.beep(500 if "Black" in detected else 200)
                        elif lado == "esquerda":
                            self.ev3.speaker.beep(400 if "Black" in detected else 100)
                        elif lado == "direita":
                            self.ev3.speaker.beep(600 if "Black" in detected else 300)

                        vitima = detected + "," + lado
                        break  # achou a vítima certa

                else:
                    # Sem detecção: gira um pouco e tenta de novo
                    wait(200)
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(100)
                    self.motorC.dc(100)
                    while True:
                        self.talk.drenar()   # não fica surdo durante o giro
                        wait(50)
                        print(self.motorB.angle(), self.motorC.angle(), semvitima)
                        if self.motorB.angle() >= 45:
                            self.tanki.stop()
                            semvitima += 1
                            break
                    self.tanki.stop()
                    if semvitima >= 150:
                        print("não tem vítima")
                        self.vitimas     = 10
                        self.vitimaBLACK  = 10
                        self.vitimaSILVER = 10
                        sairdoRESGATE    = 1
                        break
                    wait(300)

            if sairdoRESGATE == 1:
                self.exit()
                break

            # ---- Alinhar câmera com a vítima ----
            self.tanki.stop()
            wait(1000)
            self.ev3.speaker.beep()
            self.tanki.stop()
            wait(100)
            self.talk.limpar()
            self.tanki.settings(
                straight_speed=999999, straight_acceleration=9999999,
                turn_rate=9999999, turn_acceleration=99999999
            )
            wait(500)
            print("alinhar")

            if javiuantes != "meio":
                self._alinhar_camera(lapooo, vendoVITIMA)

            # ---- Chegar perto da vítima ----
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()

            prafrente = 200 if pxvitima < 2500 else 10
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.motorB.dc(60)
            self.motorC.dc(-60)
            while True:
                self.talk.drenar()   # drena serial durante o avanço
                wait(100)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if self.motorB.angle() >= prafrente or parado > 20:
                    self.tanki.stop()
                    break
            self.tanki.stop()
            wait(500)

            if pxvitima > 2500:
                self.tanki.stop()
                self._pegar_vitima(vitima, vendoVITIMA)

        return {
            "vitimas":       self.vitimas,
            "black":         self.vitimaBLACK,
            "silver":        self.vitimaSILVER,
            "sairdoRESGATE": sairdoRESGATE
        }

    # =========================================================
    # clawLife — Varredura para pegar SOMENTE Silver Ball (viva)
    # =========================================================
    def clawLife(self):
        print("=== clawLife: procurando Silver Ball ===")
        return self._varredura("Silver Ball")

    # =========================================================
    # clawDead — Varredura para pegar SOMENTE Black Ball (morta)
    # =========================================================
    def clawDead(self):
        print("=== clawDead: procurando Black Ball ===")
        return self._varredura("Black Ball")

    # =========================================================
    # triangulo — Identifica e entrega nos triângulos verde/vermelho
    # =========================================================
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
            self.talk.set_modo("triangulo")   # avisa a Rasp para modo triângulo
            self.talk.limpar()
            wait(500)

            # ---- Detectar e alinhar com o triângulo ----
            while True:
                frame = self.talk.ler_frame()

                if frame and frame.get("tipo") == "triangulo":
                    cor  = frame["cor"]    # "Vermelho" ou "Verde"
                    lado = frame["lado"]   # "esquerda" | "meio" | "direita"
                    print("Alinhando com triângulo. Cor:", cor, "Lado:", lado)

                    # Alinha até ficar no meio
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
                        # Atualiza lado com próxima leitura
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
                    # Não vê triângulo: gira um pouco e tenta de novo
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

            # ---- Ir até o triângulo ----
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
                    self.talk.drenar()   # drena serial durante avanço
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

                # Confirmar triângulo após aproximação
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

                # Ir pro triângulo de novo
                parado = 0
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)
                self.motorB.dc(100)
                self.motorC.dc(-100)
                while True:
                    self.talk.drenar()   # drena serial durante segundo avanço
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

                # Gabaritar ao triângulo com giroscópio
                self.girar_graus(180)

                print(vendoTRIANGULOcor, vendoTRIANGULOVERDE, vendoTRIANGULOVERMELHO)
                wait(1000)

                # Depositar no triângulo
                if vendoTRIANGULOcor == "verde":
                    self._depositar_triangulo(abertura_servo=0,  fechamento_servo=40)
                elif vendoTRIANGULOcor == "vermelho":
                    self._depositar_triangulo(abertura_servo=80, fechamento_servo=40)

            print("triangulos_final: verde:", vendoTRIANGULOVERDE,
                  "vermelho:", vendoTRIANGULOVERMELHO)

    # =========================================================
    # _depositar_triangulo — Abre servo, faz ciclos frente/trás
    # =========================================================
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
            self.talk.drenar()   # drena serial durante recuo inicial
            wait(50)
            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if self.motorB.angle() <= -1000 or parado > 20:
                self.tanki.stop()
                break

        self.servosMove.desativa(1)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.desativa(5)
        wait(500)
        self.servosMove.move(5, abertura_servo)
        wait(1000)

        for c in range(1, 4):
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.servosMove.desativa(1)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            self.servosMove.desativa(5)
            wait(500)
            self.servosMove.move(5, fechamento_servo)
            wait(500)
            self.motorB.dc(100)
            self.motorC.dc(-100)
            print("pra frente")
            while True:
                self.talk.drenar()   # drena serial durante avanço
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
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            self.servosMove.desativa(5)
            wait(100)
            self.servosMove.move(5, abertura_servo)
            print("pra tras")
            while True:
                self.talk.drenar()   # drena serial durante recuo
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

        self.servosMove.move(5, fechamento_servo)
        self.tanki.turn(150)
        self.tanki.stop()

    # =========================================================
    # exit — Sair do resgate
    # =========================================================
    def exit(self):
        print("sair do resgate")
        self.motorB.dc(-100)
        self.motorC.dc(100)
        wait(1000)
        self.tanki.stop()
        wait(10000)