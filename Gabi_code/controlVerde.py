from pybricks.tools import wait, StopWatch

class ControlVerde:
    def __init__(self, ev3, motorB, motorC, tanki, ser, sensor1):
        # Hardware
        self.ev3 = ev3
        self.motorB = motorB
        self.motorC = motorC
        self.tanki = tanki
        self.ser = ser
        self.sensor1 = sensor1
        
        # Variáveis de Estado (Memória)
        self.gyro_rasp_z = 0.0
        self.previsao_camera = None
        self.alvo = 8
        
        # Constantes do PID interno para o caso "depois"
        self.PESO_MEIO = 1.0
        self.PESO_FORA = 2.25

    def atualizar_memoria_serial(self):
        """Lê a porta serial e atualiza a previsão da câmara e o giroscópio"""
        data = self.ser.read_all()
        if data:
            try:
                buffer_serial = data.decode('utf-8', 'ignore')
                while '\n' in buffer_serial:
                    linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                    cmd = linha_cmd.strip()
                    
                    if not cmd or cmd == "frente":
                        continue
                    
                    if cmd.startswith("MPU_Z:"):
                        try:
                            self.gyro_rasp_z = float(cmd.split(":")[1].strip())
                        except:
                            pass
                        continue 
                        
                    print("CAMERA VÊ O FUTURO:", cmd)
                    if "esquerda antes" in cmd:
                        self.previsao_camera = "esquerda"
                    elif "direita antes" in cmd:
                        self.previsao_camera = "direita"
                    elif "dois verdes" in cmd:
                        self.previsao_camera = "beco"
                    elif "verde depois" in cmd:
                        self.previsao_camera = "depois"  
            except Exception as e:
                pass

    def verificar_e_agir(self, retorno_sensor):
        """Recebe as leituras do sensor de cor, valida os gatilhos e executa a manobra"""
        H1, S1, V1 = (retorno_sensor[20]*2), (retorno_sensor[21]*2), (retorno_sensor[22]*2)
        H3, S3, V3 = (retorno_sensor[23]*2), (retorno_sensor[24]*2), (retorno_sensor[25]*2)
        H2, S2, V2 = (retorno_sensor[26]*2), (retorno_sensor[27]*2), (retorno_sensor[28]*2)

        verdeDireita = H1 >=(95-self.alvo) and H1 <=(140+self.alvo) and S1 >=(47-self.alvo) and S1 <=(70+self.alvo) and V1 >=(40-self.alvo) and V1 <=(80+self.alvo)
        verdeMeio = H3 >=(95-self.alvo) and H3 <=(140+self.alvo) and S3 >=(47-self.alvo) and S3 <=(73+self.alvo) and V3 >=(40-self.alvo) and V3 <=(80+self.alvo)
        verdeEsquerda = H2 >=(95-self.alvo) and H2 <=(140+self.alvo) and S2 >=(47-self.alvo) and S2 <=(70+self.alvo) and V2 >=(40-self.alvo) and V2 <=(80+self.alvo)

        # Se não pisou em nada verde, sai imediatamente da função
        if not (verdeDireita or verdeEsquerda or verdeMeio):
            return

        # ==========================================
        # EXECUÇÃO: DIREITA
        # ==========================================
        if self.previsao_camera == "direita" and verdeDireita:
            self.tanki.stop()
            self.tanki.turn(70)
            self.tanki.straight(90)
            self.tanki.stop()
            self.ev3.speaker.beep(400) 
            print(">>> EXECUTANDO VERDE DIREITA")
            
            angulo_desejado = 90 
            alvo_giro = self.gyro_rasp_z + angulo_desejado
            
            self.tanki.stop()
            self.motorB.dc(999)
            self.motorC.dc(999)
            wait(200)

            while True:
                self.atualizar_memoria_serial()
                if angulo_desejado > 0 and self.gyro_rasp_z >= alvo_giro: 
                    self.tanki.stop()
                    break
                elif angulo_desejado <= 0 and self.gyro_rasp_z <= alvo_giro: 
                    self.tanki.stop()
                    break

            self.motorB.stop()
            self.motorC.stop()
            self.previsao_camera = None

        # ==========================================
        # EXECUÇÃO: ESQUERDA
        # ==========================================
        elif self.previsao_camera == "esquerda" and verdeEsquerda:
            self.tanki.stop()
            self.tanki.turn(70)
            self.tanki.straight(-90)
            self.tanki.stop()
            self.ev3.speaker.beep(200) 
            print(">>> EXECUTANDO VERDE ESQUERDA")
            
            angulo_desejado = -90
            alvo_giro = self.gyro_rasp_z + angulo_desejado
            
            self.tanki.stop()
            self.motorB.dc(-999)
            self.motorC.dc(-999)
            wait(200)

            while True:
                self.atualizar_memoria_serial()
                if angulo_desejado > 0 and self.gyro_rasp_z >= alvo_giro: 
                    self.tanki.stop()
                    break
                elif angulo_desejado <= 0 and self.gyro_rasp_z <= alvo_giro: 
                    self.tanki.stop()
                    break
                    
            self.motorB.stop()
            self.motorC.stop()
            self.previsao_camera = None 

        # ==========================================
        # EXECUÇÃO: BECO
        # ==========================================
        elif self.previsao_camera == "beco" and verdeDireita and verdeEsquerda:
            self.tanki.stop()
            self.ev3.speaker.beep(600) 
            print(">>> EXECUTANDO BECO")
            self.tanki.turn(30)
            self.tanki.straight(190)
            self.tanki.stop()
            
            angulo_desejado = 180
            alvo_giro = self.gyro_rasp_z + angulo_desejado
            
            self.motorB.dc(999)
            self.motorC.dc(999)

            while True:
                self.atualizar_memoria_serial()
                if angulo_desejado > 0 and self.gyro_rasp_z >= alvo_giro: 
                    self.tanki.stop()
                    break
                elif angulo_desejado <= 0 and self.gyro_rasp_z <= alvo_giro: 
                    self.tanki.stop()
                    break
                    
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.turn(-50)
            self.tanki.stop()
            self.previsao_camera = None

        # ==========================================
        # EXECUÇÃO: GAP / VERDE DEPOIS
        # ==========================================
        elif self.previsao_camera == "depois":
            self.tanki.stop()
            self.ev3.speaker.beep(800, 200) 
            print(">>> SEGUINDO POR TEMPO (GAP/DEPOIS)")
            
            cronometro = StopWatch()
            tempo_limite = 500
            
            # Variáveis locais de PID para este pequeno trajeto
            integral_local = 0
            old_error_local = 0
            
            while cronometro.time() < tempo_limite:
                retorno = self.sensor1.read(2)
                fora1, meio1, meio2, fora2 = retorno[0], retorno[1], retorno[2], retorno[3]

                kp = 2
                kd = 0
                ki = 0.15
                base = 100

                esquerda = (meio1 * self.PESO_MEIO) + (fora1 * self.PESO_FORA)
                direita = (meio2 * self.PESO_MEIO) + (fora2 * self.PESO_FORA)
                error = (direita - esquerda) * 0.5

                integral_local += error * 0.01 
                derivative = error - old_error_local
                corr = (error * (kp * (-1))) + (derivative * kd) + (integral_local * ki)
            
                powerB = base - corr
                powerC = -base - corr
                
                powerB = max(min(int(powerB * (0.5 if powerB > 0 else 1.0)), 900), -900)
                powerC = max(min(int(powerC * (1.0 if powerC > 0 else 0.5)), 900), -900)

                self.motorB.dc(powerB)
                self.motorC.dc(powerC)
                old_error_local = error
                wait(10)
            
            self.previsao_camera = None 
            print(">>> TEMPO ESGOTADO: Voltando ao loop principal")
