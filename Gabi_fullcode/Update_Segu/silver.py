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
ENTER_TIMEOUT_MS  = 5000  # timeout para detectar lado na entrada (ms)

TURN_TRIANGULO_VERDE    = -240   # graus tanki.turn() para depositar no verde
TURN_TRIANGULO_VERMELHO = -240   # graus tanki.turn() para depositar no vermelho


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

        self.talk = TalkingSerial(ser, False)

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

    
    #################################################################
    # DEF de atualizar informações do sensor
    #################################################################
    def atualiza_sensor1(self):
        global sensor1
        global R1, R2, R3
        global G1, G2, G3
        global B1, B2, B3, alvo
        global cloresq, clormind, clordir
        global fora1, meio1, meio2, fora2
        global H1, H2, H3
        global S1, S2, S3
        global V1, V2, V3
        global posicao
        global C1, C2, C3
        # ==========================================
        # 1.0 LEITURA DO SENSOR DE COR
        # ==========================================
        retorno = self.sensor1.read(2)
        # Leitura dos sensores para seguir linha
        fora1 = retorno[3] # esquerda 
        meio1 = retorno[2] # esquerda 
        meio2 = retorno[1] # direita  
        fora2 = retorno[0] # direita  
        # Leitura da posição do sensor sobre a linha preta
        posicao = (retorno[29]*2)
        # Leitura unitária dos sensores de cor
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        # Leitura RGBC dos sensores
        R1, R3, R2 = (retorno[4]), (retorno[8]), (retorno[12])
        G1, G3, G2 = (retorno[5]), (retorno[9]), (retorno[13])
        B1, B3, B2 = (retorno[6]), (retorno[10]), (retorno[14])
        C1, C3, C2 = (retorno[7]), (retorno[11]), (retorno[15])
        # Leitura HSV para o verde
        H1, H3, H2 = (retorno[20]*2), (retorno[23]*2), (retorno[26]*2)
        S1, S3, S2 = (retorno[21]*2), (retorno[24]*2), (retorno[27]*2)
        V1, V3, V2 = (retorno[22]*2), (retorno[25]*2), (retorno[28]*2)
        alvo = 8 # Alvo para a calibração do HSV do verde

    def atualiza_multiplex1(self):
        global multiplex1
        global ultra1, ultra2, ultrad3, ultra4
        global botao_stop, botao_parar
        global ChoqueESQ, ChoqueDIR
        # ==========================================
        # 1.1 LEITURA DO SENSOR MULTIPLEX
        # ==========================================
        retorno1= self.multiplex1.read(0)
        # Leitura dos sensores ultrasônicos
        ultra1  = retorno1[0] # frente
        ultra2  = retorno1[1] # direita
        ultrad3 = retorno1[2] # vitima
        ultra4  = retorno1[3] # esquerda
        if ultra1 or ultra2 or ultra4 or ultrad3 == -1:
            #print("não esta identificando os ultra")
            if ultra1 == -1:
                print("ultra1")
                return -1
            if ultra2 == -1:
                print("ultra2")
                return -1
            if ultrad3 == -1:
                print("ultra3")
                return -1
            if ultra4 == -1:
                print("ultra4")
                return -1
        # Leitura dos botões para função pro robô
        botao_stop  = retorno1[6]
        botao_parar = retorno1[5]
        # Leitura dos botôes que servem pro parachoque
        ChoqueESQ = retorno1[4]
        ChoqueDIR = retorno1[7]
    # =========================================================================
    # ENTER — Entrada no resgate, identifica lado da parede (com timeout)
    # =========================================================================
    def enter(self, esqgray1, mindgray1, dirgray1):
        # No enter():
        self.esqgray1  = esqgray1
        self.mindgray1 = mindgray1
        self.dirgray1  = dirgray1
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
        print("vai pra frente")
        while True:
            retorno = self.sensor1.read(2)
            fora1 = retorno[3]
            meio1 = retorno[2]
            meio2 = retorno[1]
            fora2 = retorno[0]
            print(fora1 , meio1, meio2, fora2)
            if fora1 > 50 and meio1 > 50 and meio2 > 50 and fora2 > 50:
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
        self.tanki.turn(180) # anda para o primeiro ladrilho da frente
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

            if self.ultra4 <= 100 and self.ultra2 >= 100:
                self.tanki.stop()
                print("parede esquerda")
                entradaR = "parede esquerda"
                self.tanki.straight(10)
                self.tanki.stop()
                break
            elif self.ultra4 >= 100 and self.ultra2 <= 100:
                self.tanki.stop()
                print("parede direita")
                entradaR = "parede direita"
                self.tanki.straight(-10)
                self.tanki.stop()
                break
            elif self.ultra4 > 125 and self.ultra2 > 125:
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
    # IR PRO MEIO DO RESGATE
    # =========================================================================
    def ir_pro_meio(self, entradaR):
        # No ir_pro_meio():
        #self.draw_silver("IR PRO MEIO", "lado:" + str(entradaR)[:10])
        print("ir para o meio do resgate!")
        print("indo de: ", entradaR)
        self.tanki.stop()
        if entradaR == "parede esquerda":
            self.tanki.straight(40)
            self.tanki.turn(500)
            self.tanki.straight(-100)
            self.tanki.stop()
        elif entradaR == "parede direita":
            self.tanki.straight(-40)
            self.tanki.turn(500)
            self.tanki.straight(100)
            self.tanki.stop()
        elif entradaR == "parede meeeio":
            self.tanki.turn(300)
            self.tanki.stop()
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
                tipo = frame.get("detected", "")
                lado = frame["lado"]
                area = frame["area"]
                if lado == "meio" and tipo == vendoVITIMA:
                    print("Alinhado com a vítima!")
                    self.tanki.stop()
                    self.ev3.speaker.beep(800)
                    return True
                elif lado == "esquerda" and tipo == vendoVITIMA:
                    # self.tanki.straight(-10)
                    # self.tanki.stop()
                    self.motorB.dc(-70)
                    self.motorC.dc(-70)
                elif lado == "direita" and tipo == vendoVITIMA:
                    # self.tanki.straight(10)
                    # self.tanki.stop()
                    self.motorB.dc(70)
                    self.motorC.dc(70)
                elif area < 2500 and tipo == vendoVITIMA and lado == "meio":
                    print("Vítima detectada, mas fora da área de captura")
                    self.tanki.turn(30)
                    self.tanki.stop()
                wait(50)
                self.motorB.stop()
                self.motorC.stop()
            else:
                wait(200)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if parado > 20:
                    print("não está conseguindo ver vítima", vendoVITIMA,lapooo)
                    #self.motorB.dc(-50)
                    #self.motorC.dc(50)
                    if lapooo == "esquerda" :
                        self.motorB.dc(-60)  
                        self.motorC.dc(-60)
                    if lapooo == "direita":
                        self.motorB.dc(60)
                        self.motorC.dc(60)
                wait(200)
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
                        if self.motorB.angle() <= 60 or parado > 20:
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
                        if self.motorB.angle() >= -60 or parado > 20:
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
        # No _pegar_vitima():
        #self.draw_silver("PEGANDO", "tent:" + str(tentativa))
        MAX_TENTATIVAS = 3

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
            wait(500)

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
                    if lado == "meio" and area >= 7500:
                        cam_confirmou = True
                        self.tanki.stop()
                        print("[cam-avanco] vítima na área — parando para fechar garra")
                        break
                    if lado == "esquerda":
                        self.ev3.speaker.beep(200)
                        self.tanki.straight(-20)
                        self.tanki.stop()
                    if lado == "direita":
                        self.ev3.speaker.beep(200)
                        self.tanki.straight(20)
                        self.tanki.stop()
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0

                # Limite por ângulo ou robô travado
                if self.motorB.angle() >= 400 or parado > 20:
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
            wait(200)
            self.tanki.turn(-80)
            self.tanki.stop()

            # ── Validar posse com ultrad3 ─────────────────────────────────────
            print("verificar estados de vitimas")
            # agora aqui ele vai ver se ta vendo alguma vitima depois que subiu a garra
            # ai se ele tiver vendo, primeiro ele vai ver o tipo,  e dpois a distancia
            # ai quando ele ver a distancia, ele vai o seguinte, qual foi a vitima que ele acabou de falar que pegou
            # ai agora vendo, se ele tiver pego uma silver se tiver 0/2 e ele disser que que ta vendo uma, são dois casos
            # ou ele pegou uma ja, ou a que ele tava tentando pegar ainda não pegou, ai nesse segundo caso a gnt tem que subtrair do painel
            # se for uma black se ele pegar e disser que ta vendo ainda uma black quer dizer que ele não pegou
            #self._alinhar_camera(lapooo=None, vendoVITIMA=vendoVITIMA)
            alinhamento = False
            vitima_confirmada = None
            sem_vitimasVISAO = None
            detected = ""
            confianca = None
            lado1 = None
            area1 = None
            elapsed   = 0
            wait(100) 

            while True:
                frame1 = self.talk.ler_frame()
                
                if frame1 and frame1.get("tipo") == "bola" :
                    detected  = frame1.get("detected", "")
                    confianca = frame1.get("confianca", 0)
                    lado1     = frame1.get("lado", "")
                    area1     = frame1.get("area", 0)
                    print("Validação garra em baixo:", detected, confianca, lado1, area1)
                   
                    # if "" in detected or "" in confianca or "" in lado1 or "" in area1:
                    #     print("não vendo nada na serial")
                    #     sem_vitimasVISAO = True
                    #     break

                    if confianca > 50.0 and alinhamento == False:
                        self.tanki.stop()
                        wait(100)
                        if lado1 == "meio":
                            self.tanki.stop()
                            alinhamento = True
                        if lado1 == "esquerda" and alinhamento == False: 
                            self.tanki.straight(-25)
                            self.tanki.stop()
                        if lado1 == "direita" and alinhamento == False:
                            self.tanki.straight(25)
                            self.tanki.stop()

                    # ta vendo alguma vitima?
                    # se tiver vendo alguma vitima é alguma vitima que ele pegou?
                    # se ele tiver vendo vitima Silver>
                    # 0 Silver e vendo uma vitima> dois casos. pegou uma ja e ta vendo a segunda ou não pegou uma e ta vendo a vitima que errou
                    # 1 silver e tiver vendo uma> errou de pegar a ultima
                    # 0 black e vendo uma> não pegou nenhuma black
                    # 1 black esse caso não existe pq so pode ter uma black na arena
                    if "Silver Ball"  or "Black Ball" in detected and alinhamento == True:
                        print("vendo alguma vitima")
                        print("verificar se isso esta certo!?")

                        if detected == vendoVITIMA and vendoVITIMA == "Silver Ball" :
                            if self.vitimaSILVER == 0:
                                print("talvez ele tenha pego a primeira silver")
                                print("finalizando e separando")
                                vitima_confirmada = True
                                break
                            elif self.vitimaSILVER == 1 and detected == "Silver Ball":
                                print("talvez ele tenha pego a ultima silver")
                                print("finalizando e separando")
                                # como eu não tenha informação eu vou diminuir uma vitima do painel
                                # tentar verificar por um breve momento se tem alguma vitima na frente dele
                                while elapsed < 4000:
                                    frame1 = self.talk.ler_frame()
                                    if frame1:
                                        detected  = frame1.get("detected", "")
                                        confianca = frame1.get("confianca", 0)
                                        lado1     = frame1.get("lado", "")
                                        area1     = frame1.get("area", 0)
                                        print("Validação garra em baixo:", detected, confianca, lado1, area1)
                                        if confianca > 50.0 and detected == "Silver Ball":
                                            self.vitimaSILVER -= 1
                                            self.vitimas += 1
                                            vitima_confirmada = False
                                            break 
                                    wait(100)
                                    elapsed += 100
                                if vitima_confirmada == False:
                                    vitima_confirmada = False
                                    break
                                else:
                                    print("erro logica")
                                    break
                            else:
                                vitima_confirmada = True
                                break

                        elif detected == vendoVITIMA and vendoVITIMA == "Black Ball":
                            if self.vitimaBLACK == 0:
                                print("talvez ele tenha pego a primeira black")
                                print("finalizando e separando")
                                vitima_confirmada = True
                                break
                            elif self.vitimaBLACK == 1 and detected == "Black Ball":
                                print("talvez ele tenha pego a ultima black")
                                print("finalizando e separando")
                                # como eu não tenha informação eu vou diminuir uma vitima do painel
                                self.vitimaBLACK -= 1
                                self.vitimas += 1
                                vitima_confirmada = False
                                break
                            else:
                                vitima_confirmada = True
                                break
                elif frame1 and frame1.get("tipo") == "bola" and frame1.get("detected", "") == " ":
                    print("não vendo nada na camera")
                    sem_vitimasVISAO = True
                    break

                else:
                    vitima_confirmada = True
                    print("viu nada")
                    break
            
            if vitima_confirmada == True or sem_vitimasVISAO == True:
                # Após pegar (classificar):
                #self.draw_silver("SEPARANDO", vendoVITIMA[:15])
                print("[pegar] vítima confirmada pela garra!")
                break
            elif vitima_confirmada == False:
                print("[pegar] vítima NÃO detectada pela garra — retry")
                # Abre a garra e recua para tentar de novo
                self.servosMove.desativa(1)
                self.servosMove.desativa(2)
                self.servosMove.desativa(3)
                self.servosMove.desativa(4)
                self.servosMove.move(1, 250)
                self.servosMove.move(2, 0)
                self.servosMove.move(3, 60)
                wait(500)
                self.tanki.turn(-20)   # recua abrindo espaço
                self.tanki.stop()
                wait(200)

                if tentativa == MAX_TENTATIVAS:
                    print("[pegar] máximo de tentativas atingido — desistindo")

        # ── Classificar e depositar ───────────────────────────────────────────
        self.servosMove.desativa(1)
        self.servosMove.desativa(2)
        self.servosMove.desativa(3)
        self.servosMove.desativa(4)
        self.servosMove.move(1, 0)
        self.servosMove.move(2, 60)
        self.servosMove.move(3, 0)
        self.servosMove.move(4, 40)
        wait(100)
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
        for c in range(1,13):
            self.tanki.turn(10)
            self.tanki.turn(-10)
            self.tanki.stop()
        self.tanki.stop()
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
        for c in range(1,5):
            self.tanki.turn(10)
            self.tanki.turn(-10)
            self.tanki.stop()
        self.tanki.stop()
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
        for c in range(1,13):
            self.tanki.turn(10)
            self.tanki.turn(-10)
            self.tanki.stop()
        self.tanki.stop()
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
        for c in range(1,5):
            self.tanki.turn(10)
            self.tanki.turn(-10)
            self.tanki.stop()
        self.tanki.stop()
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

            
            self.talk.limpar()
            wait(200)

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
                        # som muito grave é vitima viva
                        # som mais agudo é vitima morta
                        print("[varredura] frame1 OK — aguardando confirmação")
                        if lado1 == "esquerda": 
                            self.tanki.straight(-10)
                            self.tanki.stop()
                        if lado1 == "direita":
                            self.tanki.straight(10)
                            self.tanki.stop()
                        if lado1 == "meio":
                            if area1 > 2500 or area1 > 1500:
                                self.tanki.turn(-20)
                                self.tanki.stop()
                        wait(350)
                        # ── FRAME 2: confirmação ──────────────────────────────
                        self.tanki.stop()
                        self.talk.limpar()
                        frame2 = self.talk.ler_frame()
                        wait(300)
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

                        # if not confirmado:
                        #     # Falso positivo — volta a buscar
                        #     continue

                        wait(300)
                        # ── FRAME 3: alinhamento fino ─────────────────────────
                        self.tanki.stop()
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
                            self.tanki.straight(-15)
                            self.tanki.stop()
                        elif lado_final == "direita":
                            self.tanki.straight(15)
                            self.tanki.stop()

                else:
                    # ── Sem detecção: gira um pouco e tenta de novo ───────────
                    wait(300)
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(10)
                    self.motorB.dc(100)
                    self.motorC.dc(100)
                    while True:
                        self.talk.drenar()
                        wait(50)
                        print(self.motorB.angle(), self.motorC.angle(), semvitima)
                        if self.motorB.angle() >= 45:
                            self.tanki.stop()
                            semvitima += 1
                            break
                    self.tanki.stop()
                    if ( semvitima == 15 or semvitima == 35 or semvitima == 50 or semvitima == 60 or semvitima == 70 or
                    semvitima == 85):
                        print("tentando ir no meio do resgate")
                        # tentar ir no meio do resgate
                        parado = 0
                        self.motorB.reset_angle(0)
                        self.motorC.reset_angle(0)
                        wait(100)
                        self.motorB.dc(60)
                        self.motorC.dc(-60)
                        while True:
                            self.talk.drenar()
                            self.atualiza_multiplex1()
                            self.atualiza_sensor1()
                            retorno1  = self.multiplex1.read(0)
                            ChoqueESQ = retorno1[4]
                            ChoqueDIR = retorno1[7]
                            if ChoqueDIR == 1 or ChoqueESQ == 1:
                                self.tanki.turn(-30)
                                self.tanki.stop()
                                self.tanki.straight(-90)
                                self.tanki.stop()
                            wait(50)
                            print(self.motorB.angle(), self.motorC.angle(), semvitima, "parado:", parado,
                                  "parachoque DIR:", ChoqueDIR,  "parachoque ESQ:", ChoqueESQ)
                            if self.motorB.angle() >= 400 or parado > 20:
                                self.tanki.stop()
                                semvitima += 1
                                break
                            if self.tanki.state()[3] < 20:
                                parado += 1
                            if self.tanki.state()[3] > 60:
                                parado = 0
                        self.tanki.stop()
                    
                    if semvitima >= 100:
                        print("não tem vítima")
                        if tipo== "Silver Ball" and self.vitimaSILVER > 0:
                            return "Triangulo_verde"
                        elif tipo == "Black Ball" and self.vitimaBLACK > 0 :
                            return "Triangulo_vermelho"
                        else:
                            if self.vitimaSILVER > 0:
                                return "Triangulo_verde" 
                            self.vitimas      = 10
                            self.vitimaBLACK  = 10
                            self.vitimaSILVER = 10
                            sairdoRESGATE     = 1
                            break

                    wait(400)

            if sairdoRESGATE == 1:
                return "sairdoRESGATE"
                

            # ── Alinhar câmera com a vítima (se necessário) ───────────────────
            self.tanki.stop()
            wait(200)
            self.ev3.speaker.beep()
            self.tanki.stop()
            wait(100)
            self.talk.limpar()
            self.tanki.settings(
                straight_speed=999999, straight_acceleration=9999999,
                turn_rate=9999999, turn_acceleration=99999999
            )
            wait(200)
            if lapooo != "meio":
                print("alinhar")
                self._alinhar_camera(lapooo, vendoVITIMA)
            print("alinhado")
            # ── Aproximar da vítima usando ultra1 + pxvitima ─────────────────
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()
            prafrente = None
            # Define quanto avançar baseado nos px E na distância real
            while True:
                self._ler_ultras()
                dist_frente = self.ultra1
                if dist_frente == -1:
                    print("[aprox] ultra1 não está funcionando — usando pxvitima")
                    dist_frente = 9999  # ignora ultra1
                    break
                elif pxvitima >= 5000 or dist_frente <= 80 and dist_frente != -1:
                    # Já está perto o suficiente — vai direto para captura
                    prafrente = 100
                    break
                elif pxvitima <= 2500:
                    print("verificando distancia da vitima")
                    if pxvitima > 200 and pxvitima < 2000:
                        print("vitima longe")
                        prafrente = 200
                        break
                    elif pxvitima >= 2000 and pxvitima <= 5000:
                        print("vitima perto")
                        prafrente = 100
                        break
                    else:
                        print("vitima muito longe")
                        prafrente = 250
                        break
                elif dist_frente <= 150 and dist_frente != -1:
                    prafrente = 100
                    break
                else:
                    prafrente = 200
                    break

            print("[aprox] pxvitima:", pxvitima, "ultra1:", dist_frente,
                  "→ prafrente:", prafrente)

            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.motorB.dc(60)
            self.motorC.dc(-60)
                
            while True:
                self.motorB.dc(60)
                self.motorC.dc(-60)
                frameAndar = self.talk.ler_frame()
                self._ler_ultras()   
                if frameAndar:
                    detected  = frameAndar.get("detected", "")
                    confianca = frameAndar.get("confianca", 0)
                    lado1     = frameAndar.get("lado", "")
                    area1     = frameAndar.get("area", 0)
                    print("FRAMEandada:", detected, confianca, lado1, area1)
                    if confianca > 50.0 and tipo in detected: 
                        self.tanki.stop()
                        wait(200)
                        if lado1 == "esquerda":
                            self.ev3.speaker.beep(200)
                            self.tanki.straight(-20)
                            self.tanki.stop()
                        if lado1 == "direita":
                            self.ev3.speaker.beep(200)
                            self.tanki.straight(20)
                            self.tanki.stop()
                        elif area1 > 5000:
                            self.tanki.stop()
                            break
                    elif detected == "":
                        self.motorB.dc(50)
                        self.motorC.dc(-50) 
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                # Para se chegou perto o suficiente pelo ultrassônico
                if self.ultra1 <= 60 and self.ultra1 != -1:
                    self.tanki.stop()
                    print("[aprox] ultra1 ≤ 60 — parando")
                    break
                if self.motorB.angle() >= prafrente or parado > 20:
                    self.tanki.stop()
                    break
                wait(100)
            self.tanki.stop()
            wait(200)

            # ── Capturar se vítima está na área (px ou ultra1) ───────────────
            self._ler_ultras()
            if pxvitima >= 2500:
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
    def triangulo(self,tipo):
        vendoTRIANGULO         = 0
        vendoTRIANGULOVERDE    = 0
        vendoTRIANGULOVERMELHO = 0
        vendoTRIANGULOcor      = None
        quantdTriangulos       = 0
        tipagemTRI             = None

        while True:
            print("triangulos_inicial: verde:", vendoTRIANGULOVERDE,
                  "vermelho:", vendoTRIANGULOVERMELHO)
            if tipo == "todos":
                quantdTriangulos = 2
            if tipo != "todos":
                quantdTriangulos = 1
            if ( vendoTRIANGULO >= quantdTriangulos and (vendoTRIANGULOVERDE >= 1 ) and (vendoTRIANGULOVERMELHO >= 1) ):
                self.tanki.stop()
                self.ev3.speaker.beep(900)
                print("procurar saida")
                break
            elif tipo == "Triangulo_verde" and vendoTRIANGULOVERDE > 0:
                self.tanki.stop()
                self.ev3.speaker.beep(900)
                print("procurar saida")
                break
            elif tipo == "Triangulo_vermelho" and vendoTRIANGULOVERMELHO > 0:
                self.tanki.stop()
                self.ev3.speaker.beep(900)
                print("procurar saida")
                break
            self.tanki.stop()
            wait(200)
            self.talk.set_modo("triangulo")
            self.talk.limpar()
            wait(200)

            # ── Detectar e alinhar com o triângulo ───────────────────────────
            while True:
                frame = self.talk.ler_frame()

                if frame and frame.get("tipo") == "triangulo" and tipo:
                    cor  = frame["cor"]
                    lado = frame["lado"]

                    print("Alinhando com triângulo. Cor:", cor, "Lado:", lado, "tipo:", tipo)
                    if cor == " Verde" and tipo == "Triangulo_verde":
                        tipagemTRI= "Verde"
                    elif cor == "Vermelho" and tipo == "Triangulo_vermelho":
                        tipagemTRI = "Vermelho"
                    while lado != "meio" :
                        if cor != tipagemTRI:
                            break
                        if lado == "esquerda" and cor == tipagemTRI:
                            self.motorB.dc(-900)
                            self.motorC.dc(-900)
                        elif lado == "direita" and cor == tipagemTRI:
                            self.motorB.dc(900)
                            self.motorC.dc(900)
                        wait(50)
                        self.motorB.stop()
                        self.motorC.stop()
                        prox = self.talk.ler_frame()
                        if prox and prox.get("tipo") == "triangulo" :
                            lado = prox["lado"]
                            cor  = prox["cor"]

                    self.ev3.speaker.beep(400)
                    if cor == "Vermelho" and tipo == "Triangulo_vermelho":
                        vendoTRIANGULOcor = "vermelho"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERMELHO += 1
                    elif cor == "Verde" and tipo == "Triangulo_verde":
                        vendoTRIANGULOcor = "verde"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERDE += 1
                    elif  cor == "Vermelho" and tipo == "todos":
                        vendoTRIANGULOcor = "vermelho"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERMELHO += 1
                    elif cor == "Verde" and tipo == "todos":
                        vendoTRIANGULOcor = "verde"
                        vendoTRIANGULO += 1
                        vendoTRIANGULOVERDE += 1
                    self.tanki.stop()
                    break

                else:
                    print("Não vendo triângulo")
                    wait(200)
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(100)
                    self.motorC.dc(100)
                    while True:
                        wait(100)
                        if self.motorB.angle() >= 40:
                            self.tanki.stop()
                            break
                    self.tanki.stop()
                    wait(200)

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
                self.motorB.dc(60)
                self.motorC.dc(-60)
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

                    if frame and frame.get("tipo") == "triangulo" and tipo :
                        cor  = frame["cor"]
                        lado = frame["lado"]
                        print("Confirmando triângulo. Cor:", cor, "Lado:", lado, "tipo:", tipo)

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
                            if prox and prox.get("tipo") == "triangulo" :
                                lado = prox["lado"]
                                cor  = prox["cor"]

                        self.ev3.speaker.beep(400)
                        if cor == "Vermelho" and tipo == "Triangulo_vermelho":
                            vendoTRIANGULOcor = "vermelho"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERMELHO += 1
                        elif cor == "Verde" and tipo == "Triangulo_verde":
                            vendoTRIANGULOcor = "verde"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERDE += 1
                        elif  cor == "Vermelho" and tipo == "todos":
                            vendoTRIANGULOcor = "vermelho"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERMELHO += 1
                        elif cor == "Verde" and tipo == "todos":
                            vendoTRIANGULOcor = "verde"
                            vendoTRIANGULO += 1
                            vendoTRIANGULOVERDE += 1
                        self.tanki.stop()
                        break

                    else:
                        print("Não vendo triângulo")
                        wait(200)
                        self.motorB.reset_angle(0)
                        self.motorC.reset_angle(0)
                        wait(100)
                        self.motorB.dc(100)
                        self.motorC.dc(100)
                        while True:
                            wait(100)
                            if self.motorB.angle() >= 40:
                                self.tanki.stop()
                                break
                        self.tanki.stop()
                        wait(300)

                # ── Segunda ida ao triângulo ──────────────────────────────────
                parado = 0
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
                self.tanki.turn(-60)
                self.tanki.stop()
                self.motorB.stop()
                self.motorC.stop()
                wait(200)

                # ── Posicionar para depositar ─────────────────────────────────
                # ANTES: girar_graus(180) — travava e girava errado
                # AGORA: tanki.straight() com valor calibrado por cor
                print("[triangulo] posicionando para depositar — cor:", vendoTRIANGULOcor)
                if vendoTRIANGULOcor == "verde":
                    self.tanki.straight(TURN_TRIANGULO_VERDE)
                elif vendoTRIANGULOcor == "vermelho":
                    self.tanki.straight(TURN_TRIANGULO_VERMELHO)
                self.tanki.stop()
                wait(200)

                print(vendoTRIANGULOcor, vendoTRIANGULOVERDE, vendoTRIANGULOVERMELHO)
                wait(200)

                # ── Depositar no triângulo ────────────────────────────────────
                if vendoTRIANGULOcor == "verde":
                    self._depositar_triangulo(abertura_servo=0,  fechamento_servo=40)
                elif vendoTRIANGULOcor == "vermelho":
                    self._depositar_triangulo(abertura_servo=90, fechamento_servo=40)

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
        wait(100)
        self.motorB.dc(-100)
        self.motorC.dc(100)
        self.motorB.dc(-100)
        self.motorC.dc(100)
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
        wait(200)
        self.servosMove.move(4, abertura_servo)
        wait(200)

        for c in range(1, 5):
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            wait(100)
            self.servosMove.move(4, fechamento_servo)
            self.motorB.dc(60)
            self.motorC.dc(-60)
            print("pra frente")
            while True:
                self.talk.drenar()
                wait(50)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if self.motorB.angle() >= 10 or parado > 20:
                    self.tanki.stop()
                    break
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            wait(100)
            self.servosMove.desativa(1)
            self.servosMove.desativa(2)
            self.servosMove.desativa(3)
            self.servosMove.desativa(4)
            wait(100)
            self.servosMove.move(4, abertura_servo)
            self.motorB.dc(-100)
            self.motorC.dc(100)
            print("pra tras")
            while True:
                self.talk.drenar()
                wait(50)
                if self.tanki.state()[3] < 20:
                    parado += 1
                if self.tanki.state()[3] > 60:
                    parado = 0
                if self.motorB.angle() <= -500 or parado > 20:
                    self.tanki.stop()
                    break
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()

        self.servosMove.move(4, fechamento_servo)
        self.tanki.turn(50)
        self.tanki.stop()

    # =========================================================================
    # exit — Sair do resgate
    # =========================================================================
    def exit(self,esqgray1,mindgray1,dirgray1):
        # No exit():
        #self.draw_silver("SAINDO", "procurando linha")
        print("sair do resgate")
        self.talk.set_modo("nadapross")
        self.atualiza_sensor1()
        self.atualiza_multiplex1()
        self._ler_ultras()
        retorno = self.sensor1.read(2)
        # Leitura dos sensores para seguir linha
        fora1 = retorno[3] # esquerda 
        meio1 = retorno[2] # esquerda 
        meio2 = retorno[1] # direita  
        fora2 = retorno[0] # direita 
        # Leitura unitária dos sensores de cor
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        # Leitura RGBC dos sensores
        R1, R3, R2 = (retorno[4]), (retorno[8]), (retorno[12])
        G1, G3, G2 = (retorno[5]), (retorno[9]), (retorno[13])
        B1, B3, B2 = (retorno[6]), (retorno[10]), (retorno[14])
        C1, C3, C2 = (retorno[7]), (retorno[11]), (retorno[15])
        blue = 45
        esqgray1 = B1 > blue and B1 < 70 and C1 > 21 and C1 < 30 and cloresq == 6
        mindgray1 = B3 > blue and B3 < 70 and C3 > 21 and C3 < 30 and clormind == 6 #prata não reflectivo
        dirgray1 = B2 > blue and B2 < 70 and C2> 21 and C2 < 30 and clordir == 6
        #######################################################################
        linha_preta = fora1 < 70 or meio1 < 70 or meio2 < 70 or fora2 < 70
        linha_prata = esqgray1 or mindgray1 or dirgray1
        self.tanki.stop()
        self.tanki.straight(110)
        self.tanki.stop()
        #wait(999999)
        parado = 0
        while True:
            self.atualiza_sensor1()
            self.atualiza_multiplex1()
            self._ler_ultras()
            retorno = self.sensor1.read(2)
            # Leitura dos sensores para seguir linha
            fora1 = retorno[3] # esquerda 
            meio1 = retorno[2] # esquerda 
            meio2 = retorno[1] # direita  
            fora2 = retorno[0] # direita 
            # Leitura unitária dos sensores de cor
            cloresq = retorno[17]
            clormind = retorno[18]
            clordir = retorno[19]
            # Leitura RGBC dos sensores
            R1, R3, R2 = (retorno[4]), (retorno[8]), (retorno[12])
            G1, G3, G2 = (retorno[5]), (retorno[9]), (retorno[13])
            B1, B3, B2 = (retorno[6]), (retorno[10]), (retorno[14])
            C1, C3, C2 = (retorno[7]), (retorno[11]), (retorno[15])
            blue = 45
            esqgray1 = B1 > blue and B1 < 70 and C1 > 21 and C1 < 30 and cloresq == 6
            mindgray1 = B3 > blue and B3 < 70 and C3 > 21 and C3 < 30 and clormind == 6 #prata não reflectivo
            dirgray1 = B2 > blue and B2 < 70 and C2> 21 and C2 < 30 and clordir == 6
            retorno1  = self.multiplex1.read(0)
            ChoqueESQ = retorno1[4]
            ChoqueDIR = retorno1[7]

            print("parado:", parado,
            "parachoque DIR:", ChoqueDIR,  "parachoque ESQ:", ChoqueESQ,"||",
            "fora1: ", fora1, "meio1: ", meio1, "meio2: ", meio2, "fora2: ", fora2,"||",
            "ultra Esquerdo:", ultra4, "ultra Direito:", ultra2)

            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if parado > 30:
                self.tanki.stop()
                self.tanki.turn(-50)
                self.tanki.straight(-40)
                self.tanki.stop()
            if ultra2 > 250:
                print("viu sem parede na direita")
                self.tanki.stop()
                break
            if ultra4 > 200 and  ultra2 > 200:
                print("viu nada")
            elif ChoqueESQ == 1 or ChoqueDIR == 1:
                print("parachoque")
                self.tanki.turn(-20)
                self.tanki.stop()
                self.tanki.straight(-40)
                self.tanki.stop()
            if fora1 < 70 or meio1 < 70 or meio2 < 70 or fora2 < 70 :
                if fora1 < 70 or meio1 < 70 or meio2 < 70 or fora2 < 70:
                    print("linha preta" )
                    self.tanki.turn(100)
                    self.tanki.stop()
                    break
            elif esqgray1 or mindgray1 or dirgray1:
                wait(10)
                if esqgray1 or mindgray1 or dirgray1:
                    print("linha prata", linha_prata)
                    self.tanki.turn(-50)
                    self.tanki.straight(-60)
                    self.tanki.stop()
            else:
                # self.motorB.dc(50)
                # self.motorC.dc(-50) #frente
                print
        print("saindo do resgate")
        self.tanki.turn(20)
        self.tanki.stop()
        self.atualiza_sensor1()
        if meio1 < 50 or meio2 < 50:
            self.tanki.turn(20)
            self.tanki.stop()
            return
        