from pybricks.tools import wait, StopWatch

class Green:
    def __init__(self,tanki,motorB,motorC,sensor1,ev3,ser,motores):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3 
        self.ser = ser
        self.motores = motores
    
    def MoveGreen(self,H1, S1, V1, H2, S2, V2, H3, S3, V3, alvo,
                   fora1, meio1, meio2, fora2, previsao_camera, cloresq, clordir, pretoesq, pretodir):
        verdeDireita = H1 >=(90-alvo) and H1 <=(140+alvo) and S1 >=(43-alvo) and S1 <=(75+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(90-alvo) and H3 <=(140+alvo) and S3 >=(43-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(90-alvo) and H2 <=(140+alvo) and S2 >=(43-alvo) and S2 <=(75+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)

        if not (verdeDireita or verdeEsquerda or verdeMeio or previsao_camera != None):
            return previsao_camera
            
        # ==================================
        # LÓGICA DA DIREITA
        # ==================================
        self.ev3.speaker.beep(800)
        if verdeDireita and not pretodir > 0:
            if meio1 >= 40 or meio2 >= 40:
                self.tanki.stop()
                self.tanki.turn(70)
                self.tanki.straight(90)
                self.tanki.stop()
                self.ev3.speaker.beep(400) 
                print(">>> EXECUTANDO VERDE DIREITA")
                self.tanki.stop()
                self.motorB.dc(100)
                self.motorC.dc(100)
                while True:
                    retorno = self.sensor1.read(2)
                    f1 = retorno[0]
                    if f1 <= 40:
                        self.tanki.stop()
                        break
                self.motorB.stop()
                self.motorC.stop()
                #self.ser.write(b"passou_verde\n")
            return None 

        # ==================================
        # LÓGICA DA ESQUERDA
        # ==================================
        elif verdeEsquerda and not pretoesq > 0:
            if meio1 >= 40 or meio2 >= 40:
                self.tanki.stop()
                self.tanki.turn(70)
                self.tanki.straight(-90)
                self.tanki.stop()
                self.ev3.speaker.beep(200) 
                print(">>> EXECUTANDO VERDE ESQUERDA")
                self.tanki.stop()
                self.motorB.dc(-100)
                self.motorC.dc(-100)
                while True:
                    retorno = self.sensor1.read(2)
                    f2 = retorno[3]
                    if f2 <= 40:
                        self.tanki.stop()
                        break
                self.motorB.stop()
                self.motorC.stop()
                #self.ser.write(b"passou_verde\n")
            return None

        # ==================================
        # LÓGICA DO BECO 
        # ==================================
        elif (verdeDireita and verdeEsquerda):
            wait(10)
            self.tanki.stop()
            self.ev3.speaker.beep(600) 
            print(">>> EXECUTANDO BECO")
            self.tanki.turn(30)
            self.tanki.straight(190)
            self.tanki.stop()
            
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.turn(-50)
            self.tanki.stop()
            
            #self.ser.write(b"passou_verde\n")
            return None 
        
        # ==================================
        # LÓGICA DE GAP (DEPOIS)
        # ==================================
        elif (meio1 <= 30 or meio2 <= 30) and (cloresq == 1 or clordir == 1):
            self.tanki.stop()
            self.ev3.speaker.beep(800, 200) 
            print(">>> SEGUINDO POR TEMPO (GAP/DEPOIS)")
            cronometro = StopWatch()
            tempo_limite = 500  
            while cronometro.time() < tempo_limite:
                retorno = self.sensor1.read(2)
                f1, m1, m2, f2 = retorno[0], retorno[1], retorno[2], retorno[3]
                
                # AQUI É ONDE USAMOS O SEU PID:
                self.meu_pid.PID(f1, m1, m2, f2, 2.0, 0, 0.15, 100)
                wait(10)
                
            print(">>> TEMPO ESGOTADO: Voltando ao loop principal")
            return None

        return previsao_camera