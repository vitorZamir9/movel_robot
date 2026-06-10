#!/usr/bin/env pybricks-micropython
from pybricks.tools import wait


class Silver:
    def __init__(self, tanki, motorB, motorC, sensor1, multiplex1, ev3, ser, servosP):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.multiplex1 = multiplex1
        self.ev3 = ev3
        self.ser = ser
        self.servosP = servosP
        self.yaw_rasp = 0.0      # Guarda o valor real que vem da placa
        self.yaw_offset = 0.0    # Guarda o valor de "tara" (para zerar o ângulo)
        # Contadores de vítimas (persistem entre chamadas)
        self.vitimas = 0
        self.vitimaBLACK = 0
        self.vitimaSILVER = 0

    # =========================================================
    # ENTER — Entrada no resgate, identifica lado da parede
    # =========================================================
    def enter(self, esqgray, mindgray, dirgray):
        self.tanki.turn(-70)
        self.ev3.speaker.beep(900, 600)
        self.ev3.speaker.beep()
        self.tanki.stop()
        self.ser.write(b'Resgate_ON\r\n')
        wait(500)

        if esqgray and mindgray and dirgray:
            wait(10)
            if esqgray and mindgray and dirgray:
                self.tanki.stop()
                print("resgate on")
                self.ev3.speaker.beep()

                # Ir para frente até perder a linha
                self.motorB.run(300)
                self.motorC.run(-300)
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
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
                    meio1 = retorno[1]
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
                    meio2 = retorno[2]
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
                    retorno1 = self.multiplex1.read(0)
                    ultraesquerda = retorno1[0]
                    ultrafrente  = retorno1[2]
                    ultradireita = retorno1[3]
                    print(ultradireita, ultraesquerda, ultrafrente)

                    if ultraesquerda <= 150 and ultradireita >= 150:
                        self.tanki.stop()
                        print("parede esquerda")
                        entradaR = "parede esquerda"
                        self.tanki.straight(10)
                        self.tanki.stop()
                        break
                    elif ultraesquerda >= 150 and ultradireita <= 150:
                        self.tanki.stop()
                        print("parede direita")
                        entradaR = "parede direita"
                        self.tanki.straight(-10)
                        self.tanki.stop()
                        break
                    elif ultradireita > 100 and ultraesquerda > 100:
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
    # _LER_SERIAL — Lê e parseia um frame da serial
    # Retorna dict com detected, confianca, lado, area
    # ou None se não tiver dado completo
    # =========================================================
    def _ler_serial(self):
        """
        Lê a serial. Se achar [MPU], atualiza o giroscópio sozinho em segundo plano.
        Se achar dados da visão (Detected), retorna o dicionário.
        """
        data = self.ser.read_all()
        if not data:
            return None
            
        try:
            data_str = data.decode('utf-8').strip()
            
            # Variáveis para a visão
            detected = None
            confianca = None
            lado = None
            area = None
            
            for line in data_str.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # ==========================================
                # 1. LEITURA DO MPU (Atualização Automática)
                # ==========================================
                if "[MPU]" in line:
                    try:
                        texto_roll = line.split("Roll: ")[1].split("°")[0]
                        roll = float(texto_roll)
                        
                        texto_pitch = line.split("Pitch: ")[1].split("°")[0]
                        pitch = float(texto_pitch)
                        
                        texto_yaw = line.split("Yaw: ")[1].split("°")[0]
                        yaw = float(texto_yaw)
                        
                        # ATUALIZA O GIROSCÓPIO DA CLASSE AQUI!
                        self.guinadaAA.atualizar_dados(roll, pitch, yaw)
                    except (IndexError, ValueError):
                        pass
                    continue # Pula para a próxima linha do texto
                
                # ==========================================
                # 2. LEITURA DA VISÃO (YOLO)
                # ==========================================
                if 'Detected:' in line:
                    detected = line.split(':')[1].strip()
                elif 'Confian' in line:
                    parts = line.split(':')
                    if len(parts) > 1 and parts[1].strip():
                        try:
                            confianca = round(float(parts[1].strip().replace('%', '')), 1)
                        except ValueError:
                            confianca = None
                elif 'Lado:' in line:
                    lado = line.split(':')[1].strip()
                elif 'Area:' in line:
                    parts = line.split(':')
                    if len(parts) > 1 and parts[1].strip():
                        try:
                            area = int(parts[1].strip().replace('px', '').strip())
                        except ValueError:
                            area = None

            # Retorna apenas se encontrou um objeto válido na visão
            if detected and confianca is not None and lado and area is not None:
                return {
                    "detected": detected, 
                    "confianca": confianca, 
                    "lado": lado, 
                    "area": area
                }

        except Exception as e:
            print("Erro serial na Silver:", e)
            self.ser.flushInput()
            
        return None
    
    def girar_graus(self,angulo):#serve somente para o resgate
        # 1. Puxa a informação mais recente da placa
        self._ler_serial()
        
        # 2. "Zera" o giroscópio (salva a posição atual como ponto de partida)
        self.yaw_offset = self.yaw_rasp
        
        # 3. Liga os motores para girar
        self.motorB.dc(100)
        self.motorC.dc(100)
        
        while True:
            # 4. Atualiza os dados da Raspberry Pi constantemente
            self._ler_serial()
            
            # 5. Calcula o quanto o robô girou desde que você "zerou"
            giro_atual = self.yaw_rasp - self.yaw_offset
            
            # 6. Verifica se bateu os 90 graus
            if giro_atual >= abs(angulo):
                self.motorB.stop()
                self.motorC.stop()
                print("Curva de graus finalizada!")
                break

    # =========================================================
    # _ALINHAR_CAMERA — Gira até a vítima ficar no meio
    # =========================================================
    def _alinhar_camera(self, lapooo, vendoVITIMA):
        parado = 0
        while True:
            frame = self._ler_serial()
            if frame:
                lado = frame["lado"]
                if lado == "meio":
                    print("Alinhado com a vítima!")
                    self.tanki.stop()
                    self.ev3.speaker.beep(800)
                    return True
                if lado == "esquerda":
                    self.motorB.dc(-75)
                    self.motorC.dc(-75)
                elif lado == "direita":
                    self.motorB.dc(75)
                    self.motorC.dc(75)
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
                    self.motorB.dc(-40)
                    self.motorC.dc(40)
                wait(300)
                if lapooo == "esquerda":
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)
                    self.motorB.dc(-85)
                    self.motorC.dc(-85)
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
                    self.motorB.dc(85)
                    self.motorC.dc(85)
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
    # _PEGAR_VITIMA — Sequência de garra para uma vítima
    # tipo: "Black Ball" ou "Silver Ball"
    # =========================================================
    def _pegar_vitima(self, vitima, vendoVITIMA):
        self.tanki.turn(-50)
        self.tanki.stop()

        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)

        # Posição de coleta (igual para todos os lados nos dois tipos)
        self.servosP.move(1, 250)
        self.servosP.move(3, 90)
        self.servosP.move(4, 0)
        wait(1000)

        # Andar para pegar a vítima
        parado = 0
        self.motorB.reset_angle(0)
        self.motorC.reset_angle(0)
        wait(100)
        self.motorB.dc(60)
        self.motorC.dc(-60)
        while True:
            wait(100)
            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if self.motorB.angle() >= 200 or parado > 20:
                self.tanki.stop()
                break
        self.tanki.stop()

        # Separar
        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        self.servosP.move(3, 0)
        self.servosP.move(4, 90)
        wait(100)
        self.servosP.move(5, 40)
        self.servosP.move(1, 5)
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
    # _SEPARAR_BLACK — Deposita vítima morta (Black Ball)
    # =========================================================
    def _separar_black(self):
        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        wait(500)
        self.servosP.move(5, 40)
        self.servosP.move(3, 0)
        self.servosP.move(4, 90)
        wait(1000)
        self.servosP.move(1, 5)
        wait(1000)
        self.servosP.move(3, 90)
        self.servosP.move(4, 65)
        wait(1000)
        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        wait(100)
        self.servosP.move(1, 10)
        wait(100)
        self.servosP.move(1, 0)
        wait(1000)
        self.servosP.move(1, 5)
        self.servosP.move(3, 90)
        self.servosP.move(4, 0)
        wait(100)
        self.servosP.move(1, 0)
        wait(500)

    # =========================================================
    # _SEPARAR_SILVER — Deposita vítima viva (Silver Ball)
    # =========================================================
    def _separar_silver(self):
        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        wait(500)
        self.servosP.move(5, 40)
        self.servosP.move(3, 0)
        self.servosP.move(4, 90)
        wait(1000)
        self.servosP.move(1, 5)
        wait(1000)
        self.servosP.move(4, 0)
        self.servosP.move(3, 10)
        wait(1000)
        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        wait(100)
        self.servosP.move(1, 10)
        wait(100)
        self.servosP.move(1, 0)
        wait(1000)
        self.servosP.move(1, 10)
        self.servosP.move(3, 90)
        self.servosP.move(4, 0)
        wait(100)
        self.servosP.move(1, 0)
        wait(500)

    # =========================================================
    # _VARREDURA — Loop de detecção, alinhamento e coleta
    # tipo: "Silver Ball" (viva) ou "Black Ball" (morta)
    # Retorna dict com contadores e sairdoRESGATE
    # =========================================================
    def _varredura(self, tipo):
        semvitima = 0
        sairdoRESGATE = None

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
            self.ser.write(b'bolas\r\n')
            self.ser.clear()
            wait(1000)
            # ---- Loop: detectar a vítima do tipo certo ----
            vitima = None
            lapooo = None
            vendoVITIMA = None
            pxvitima = None
            javiuantes = None

            while True:
                frame = self._ler_serial()
                if frame:
                    detected  = frame["detected"]
                    confianca = frame["confianca"]
                    lado      = frame["lado"]
                    area      = frame["area"]

                    conf_str = str(confianca).rstrip('0').rstrip('.') if '.' in str(confianca) else str(confianca)
                    print("DETECTADO:", detected, confianca, lado, area)

                    if confianca > 80.0 and tipo in detected:
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
                    self.motorB.dc(100)
                    self.motorC.dc(100) #direita
                    while True:
                        wait(50)
                        print(self.motorB.angle(), self.motorC.angle(), semvitima)
                        if self.motorB.angle() >= 45:
                            self.tanki.stop()
                            semvitima += 1
                            break
                    self.tanki.stop()
                    if semvitima >= 150:
                        print("não tem vítima")
                        self.vitimas    = 10
                        self.vitimaBLACK = 10
                        self.vitimaSILVER = 10
                        sairdoRESGATE   = 1
                        break
                    wait(300)

            if sairdoRESGATE == 1:
                break

            # ---- Alinhar câmera com a vítima ----
            self.tanki.stop()
            wait(1000)
            self.ev3.speaker.beep()
            self.tanki.stop()
            wait(100)
            self.ser.clear()
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
                # Perto o suficiente: pegar a vítima
                self._pegar_vitima(vitima, vendoVITIMA)

        return {
            "vitimas":        self.vitimas,
            "black":          self.vitimaBLACK,
            "silver":         self.vitimaSILVER,
            "sairdoRESGATE":  sairdoRESGATE
        }

    # =========================================================
    # CLAWLIFE — Varredura para pegar SOMENTE Silver Ball (viva)
    # =========================================================
    def clawLife(self):
        print("=== clawLife: procurando Silver Ball ===")
        return self._varredura("Silver Ball")

    # =========================================================
    # CLAWDEAD — Varredura para pegar SOMENTE Black Ball (morta)
    # =========================================================
    def clawDead(self):
        print("=== clawDead: procurando Black Ball ===")
        return self._varredura("Black Ball")

    # =========================================================
    # TRIANGULO — Identifica e entrega nos triângulos verde/vermelho
    # Depende de guinadaAA (giroscópio) — falta hardware
    # =========================================================
    def triangulo(self):
        vendoTRIANGULO        = 0
        vendoTRIANGULOVERDE   = 0
        vendoTRIANGULOVERMELHO = 0
        vendoTRIANGULOcor     = None

        while True:
            print("triangulos_inicial: verde:", vendoTRIANGULOVERDE, "vermelho:", vendoTRIANGULOVERMELHO)

            if vendoTRIANGULO >= 2 and vendoTRIANGULOVERDE >= 1 and vendoTRIANGULOVERMELHO >= 1:
                self.tanki.stop()
                self.ev3.speaker.beep(900, 10000)
                print("procurar saida")
                break

            self.tanki.stop()
            wait(500)
            self.ser.write(b'triangulo\r\n')
            self.ser.clear()
            wait(500)

            # ---- Detectar e alinhar com o triângulo ----
            while True:
                data = self.ser.read_all()
                if data:
                    try:
                        data_str = data.decode('utf-8').strip()
                        retangulo = None
                        lado = None
                        for line in data_str.split('\n'):
                            line = line.strip()
                            if not line:
                                continue
                            if 'Retangulo' in line:
                                retangulo = line
                            if 'Lado:' in line:
                                lado = line.split(':')[1].strip()

                        if retangulo:
                            print("Alinhando com triângulo. Lado:", lado)
                            while lado != "meio":
                                data = self.ser.read_all()
                                if data:
                                    data_str = data.decode('utf-8').strip()
                                    for line in data_str.split('\n'):
                                        line = line.strip()
                                        if not line:
                                            continue
                                        if 'Lado:' in line:
                                            lado = line.split(':')[1].strip()
                                if lado == "esquerda":
                                    self.motorB.dc(-900)
                                    self.motorC.dc(-900)
                                elif lado == "direita":
                                    self.motorB.dc(900)
                                    self.motorC.dc(900)
                                wait(50)
                                self.motorB.stop()
                                self.motorC.stop()

                            self.ev3.speaker.beep(400)
                            if "Vermelho" in retangulo:
                                vendoTRIANGULOcor = "vermelho"
                                vendoTRIANGULO += 1
                                vendoTRIANGULOVERMELHO += 1
                            elif "Verde" in retangulo:
                                vendoTRIANGULOcor = "verde"
                                vendoTRIANGULO += 1
                                vendoTRIANGULOVERDE += 1
                            self.tanki.stop()
                            break

                    except ValueError:
                        print("Aviso: UTF-8 inválido")
                        self.ser.flushInput()
                        continue
                    except Exception as e:
                        print("Erro:", e)
                        self.ser.flushInput()
                        continue
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

            # ---- Ir até o triângulo ----
            self.tanki.stop()
            wait(100)
            retorno1 = self.multiplex1.read(0)
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
                    retorno1  = self.multiplex1.read(0)
                    ChoqueESQ = retorno1[4]
                    ChoqueDIR = retorno1[7]
                    wait(100)
                    print(self.motorB.angle(), self.motorC.angle(), self.tanki.state()[3], "parado:", parado, ChoqueESQ, ChoqueDIR)
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
                    data = self.ser.read_all()
                    if data:
                        try:
                            data_str = data.decode('utf-8').strip()
                            retangulo = None
                            lado = None
                            for line in data_str.split('\n'):
                                line = line.strip()
                                if not line:
                                    continue
                                if 'Retangulo' in line:
                                    retangulo = line
                                if 'Lado:' in line:
                                    lado = line.split(':')[1].strip()

                            if retangulo:
                                print("Confirmando triângulo. Lado:", lado)
                                while lado != "meio":
                                    data = self.ser.read_all()
                                    if data:
                                        data_str = data.decode('utf-8').strip()
                                        for line in data_str.split('\n'):
                                            line = line.strip()
                                            if not line:
                                                continue
                                            if 'Lado:' in line:
                                                lado = line.split(':')[1].strip()
                                    if lado == "esquerda":
                                        self.motorB.dc(-900)
                                        self.motorC.dc(-900)
                                    elif lado == "direita":
                                        self.motorB.dc(900)
                                        self.motorC.dc(900)
                                    wait(50)
                                    self.motorB.stop()
                                    self.motorC.stop()

                                self.ev3.speaker.beep(400)
                                if "Vermelho" in retangulo:
                                    vendoTRIANGULOcor = "vermelho"
                                    vendoTRIANGULO += 1
                                    vendoTRIANGULOVERMELHO += 1
                                elif "Verde" in retangulo:
                                    vendoTRIANGULOcor = "verde"
                                    vendoTRIANGULO += 1
                                    vendoTRIANGULOVERDE += 1
                                self.tanki.stop()
                                break

                        except ValueError:
                            print("Aviso: UTF-8 inválido")
                            self.ser.flushInput()
                            continue
                        except Exception as e:
                            print("Erro:", e)
                            self.ser.flushInput()
                            continue
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
                    retorno1  = self.multiplex1.read(0)
                    ChoqueESQ = retorno1[4]
                    ChoqueDIR = retorno1[7]
                    wait(100)
                    print(self.motorB.angle(), self.motorC.angle(), self.tanki.state()[3], "parado:", parado, ChoqueESQ, ChoqueDIR)
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

                # ---- Gabaritar ao triângulo com giroscópio ----
                self.girar_graus(180)

                print(vendoTRIANGULOcor, vendoTRIANGULOVERDE, vendoTRIANGULOVERMELHO)
                wait(1000)

                # ---- Depositar no triângulo ----
                if vendoTRIANGULOcor == "verde":
                    self._depositar_triangulo(abertura_servo=0, fechamento_servo=40)
                elif vendoTRIANGULOcor == "vermelho":
                    self._depositar_triangulo(abertura_servo=80, fechamento_servo=40)

            print("triangulos_final: verde:", vendoTRIANGULOVERDE, "vermelho:", vendoTRIANGULOVERMELHO)

    # =========================================================
    # _DEPOSITAR_TRIANGULO — Abre servo, faz ciclos frente/trás
    # abertura_servo: 0 para verde, 80 para vermelho
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
            wait(50)
            if self.tanki.state()[3] < 20:
                parado += 1
            if self.tanki.state()[3] > 60:
                parado = 0
            if self.motorB.angle() <= -1000 or parado > 20:
                self.tanki.stop()
                break

        self.servosP.desativa(1)
        self.servosP.desativa(3)
        self.servosP.desativa(4)
        self.servosP.desativa(5)
        wait(500)
        self.servosP.move(5, abertura_servo)
        wait(1000)

        for c in range(1, 4):
            parado = 0
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.servosP.desativa(1)
            self.servosP.desativa(3)
            self.servosP.desativa(4)
            self.servosP.desativa(5)
            wait(500)
            self.servosP.move(5, fechamento_servo)
            wait(500)
            self.motorB.dc(100)
            self.motorC.dc(-100)
            print("pra frente")
            while True:
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
            self.servosP.desativa(1)
            self.servosP.desativa(3)
            self.servosP.desativa(4)
            self.servosP.desativa(5)
            wait(100)
            self.servosP.move(5, abertura_servo)
            print("pra tras")
            while True:
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

        self.servosP.move(5, fechamento_servo)
        self.tanki.turn(150)
        self.tanki.stop()

    # =========================================================
    # EXIT — Sair do resgate
    # =========================================================
    def exit(self):
        print("sair do resgate")
        self.motorB.dc(-100)
        self.motorC.dc(100)
        wait(1000)
        self.tanki.stop()
        wait(10000)
