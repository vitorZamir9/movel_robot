from pybricks.tools import wait, StopWatch
from segue import Segue
PESO_MEIO = 1.0
PESO_FORA = 2.275
class Green:
    def __init__(self,tanki,motorB,motorC,sensor1,ev3,ser,motores):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3 
        self.ser = ser
        self.motores = motores
        #self.motores = Segue(motorB, motorC, PESO_FORA, PESO_MEIO)
    
    def MoveGreen(self,H1, S1, V1, H2, S2, V2, H3, S3, V3, alvo,
                   fora1, meio1, meio2, fora2, previsao_camera, cloresq, clordir, pretoesq, pretodir):
        
        #=====================================
        #BLOCOS DE VERDES
        #=====================================
        
        # r1 b1 g1, h1 s1 v1, cloresq
        
        verdeDireita1 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(64-alvo) and S1 <=(72+alvo) and V1 >=(72-alvo) and V1 <=(74+alvo)
        verdeMeio1 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(64-alvo) and S3 <=(72+alvo) and V3 >=(72-alvo) and V3 <=(74+alvo)
        verdeEsquerda1 = H2 >=(110-alvo) and H2 <=(110+alvo) and S2 >=(60-alvo) and S2 <=(60+alvo) and V2 >=(86-alvo) and V2 <=(86+alvo)

        verdeDireita2 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(30-alvo) and S1 <=(30+alvo) and V1 >=(140-alvo) and V1 <=(140+alvo)
        verdeMeio2 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(30-alvo) and S3 <=(30+alvo) and V3 >=(140-alvo) and V3 <=(140+alvo)
        verdeEsquerda2 = H2 >=(95-alvo) and H2 <=(103+alvo) and S2 >=(40-alvo) and S2 <=(40+alvo) and V2 >=(127-alvo) and V2 <=(127+alvo)
        
        verdeDireita3 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(75-alvo) and S1 <=(75+alvo) and V1 >=(100-alvo) and V1 <=(100+alvo)
        verdeMeio3 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(75-alvo) and S3 <=(75+alvo) and V3 >=(100-alvo) and V3 <=(100+alvo)
        verdeEsquerda3 = H2 >=(110-alvo) and H2 <=(110+alvo) and S2 >=(60-alvo) and S2 <=(60+alvo) and V2 >=(80-alvo) and V2 <=(80+alvo)

        verdeDireita = verdeDireita1 or verdeDireita2 or verdeDireita3
        verdeMeio = verdeMeio1 or verdeMeio2 or verdeMeio3
        verdeEsquerda = verdeEsquerda1 or verdeEsquerda2 or verdeEsquerda3

        if not (verdeDireita or verdeEsquerda or verdeMeio or previsao_camera != None):
            return previsao_camera
            
        # ==================================
        # LÓGICA DA DIREITA
        # ==================================
        #wait(100)
        #print("verde")
        if verdeDireita and not pretodir > 0:

            
            if verdeEsquerda: #detectou dois verdes, é beco
                wait(10)
                self.tanki.stop()
                self.ev3.speaker.beep(600, 300) 
                self.ev3.speaker.beep(100, 100) 
                print(">>> EXECUTANDO BECO")
                self.tanki.turn(30)
                self.tanki.straight(190)
                self.tanki.stop()
                self.motorB.dc(100)
                self.motorC.dc(100)
                while True:
                    retorno = self.sensor1.read(2)
                    m1 = retorno[2]
                    if m1 <= 40:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                
                self.motorB.stop()
                self.motorC.stop()
                self.tanki.turn(-50)
                self.tanki.stop()
                return None
            
            #self.ser.write(b"passou_verde\n")
            #se não for beco, segue a lógica normal
            #if meio1 >= 40 or meio2 >= 40:
            else: #verificar possíveis falhas de movimentação
                self.tanki.stop()
                self.tanki.turn(60)
                self.tanki.straight(90)
                self.ev3.speaker.beep(200,100)
                self.tanki.stop()
                self.ev3.speaker.beep(200,1000) 
                print(">>> EXECUTANDO VERDE DIREITA")
                self.tanki.stop()
                self.motorB.dc(90)
                self.motorC.dc(90)
                while True:
                    retorno = self.sensor1.read(2)
                    m1 = retorno[2]
                    if m1 <= 50:
                        self.tanki.stop()
                        break
                
                self.motorB.stop()
                self.motorC.stop()
                return None 
                
            return None 

        # ==================================
        # LÓGICA DA ESQUERDA
        # ==================================
        elif verdeEsquerda and not pretoesq > 0:
            wait(10)

            if verdeDireita: #detectou dois verdes, é beco
                wait(10)
                self.tanki.stop()
                self.ev3.speaker.beep(600, 300) 
                self.ev3.speaker.beep(100, 100) 
                print(">>> EXECUTANDO BECO")
                self.tanki.turn(30)
                self.tanki.straight(190)
                self.tanki.stop()
                self.motorB.dc(90)
                self.motorC.dc(90)
                while True:
                    retorno = self.sensor1.read(2)
                    m1 = retorno[2]
                    if m1 <= 50:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                
                self.motorB.stop()
                self.motorC.stop()
                self.tanki.turn(-50)
                self.tanki.stop()
                return None
             
            #if meio1 >= 40 or meio2 >= 40:
            else: #verificar possíveis falhas de movimentação
                self.tanki.stop()
                self.tanki.turn(60)
                self.tanki.straight(-90)
                self.tanki.stop()
                self.ev3.speaker.beep(200,1000) 
                print(">>> EXECUTANDO VERDE ESQUERDA")
                self.tanki.stop()
                self.motorB.dc(-100)
                self.motorC.dc(-100)
                while True:
                    retorno = self.sensor1.read(2)
                    m2 = retorno[1]
                    if m2 <= 40:
                        self.tanki.stop()
                        break
                self.motorB.stop()
                self.motorC.stop()
                # print('viu verde e tá parado')
                # self.tanki.stop()
                # wait(300000000)
                #self.ser.write(b"passou_verde\n")
            return None
        
        elif verdeMeio: #foi torto e viu o verde no meio
            self.tanki.stop()
            self.motorB.stop()
            self.motorC.stop()
            self.ev3.speaker.beep(200,1000) 
            print(">>> EXECUTANDO VERDE MEIO")
            wait(1000)
            if meio1 < 20: #pra direita
                self.tanki.turn(30)
                self.tanki.straight(60)
                self.ev3.speaker.beep(200,1000) 
                print(">>> EXECUTANDO VERDE MEIO DIREITA")
                self.tanki.stop()
                self.motorB.dc(90)
                self.motorC.dc(90)
                while True:
                    retorno = self.sensor1.read(2)
                    m1 = retorno[2]
                    if m1 <= 50:
                        self.tanki.stop()
                        break
                
                self.motorB.stop()
                self.motorC.stop()
                return None
            
            elif meio2 < 20:#pra esquerda
                self.tanki.turn(30)
                self.tanki.straight(-60)
                self.ev3.speaker.beep(200,1000) 
                print(">>> EXECUTANDO VERDE MEIO ESQUERDA")
                self.tanki.stop()
                self.motorB.dc(-100)
                self.motorC.dc(-100)
                while True:
                    retorno = self.sensor1.read(2)
                    m2 = retorno[1]
                    if m2 <= 40:
                        self.tanki.stop()
                        break
                self.motorB.stop()
                self.motorC.stop()
                return None
            else:
                self.tanki.turn(-50)
                return None

        # ==================================
        # LÓGICA DO BECO #MANTER SÓ PRA DIZER QUE TEM
        # ==================================
        # elif (verdeDireita and verdeEsquerda):
        #     wait(10)
        #     self.tanki.stop()
        #     self.ev3.speaker.beep(600) 
        #     print(">>> EXECUTANDO BECO")
        #     self.tanki.turn(30)
        #     self.tanki.straight(190)
        #     self.tanki.stop()
            
        #     self.motorB.stop()
        #     self.motorC.stop()
        #     self.tanki.turn(-50)
        #     self.tanki.stop()
            
        #     #self.ser.write(b"passou_verde\n")
        #     return None 
        

        
        # ==================================
        # LÓGICA DE GAP (DEPOIS)
        # ==================================
        # elif (meio1 <= 30 or meio2 <= 30) and (cloresq == 1 or clordir == 1): #pode dar errado?
        #     self.tanki.stop()
        #     self.ev3.speaker.beep(800, 200) 
        #     print(">>> SEGUINDO POR TEMPO (GAP/DEPOIS)")
        #     cronometro = StopWatch()
        #     tempo_limite = 500  
        #     while cronometro.time() < tempo_limite:
        #         retorno = self.sensor1.read(2)
        #         f1, m1, m2, f2 = retorno[0], retorno[1], retorno[2], retorno[3]
                
        #         # AQUI É ONDE USAMOS O SEU PID:
        #         self.motores.PID(f1, m1, m2, f2, 2.0, 0, 0.15, 100)
        #         wait(10)
                
        #     print(">>> TEMPO ESGOTADO: Voltando ao loop principal")
        #     return None

        return previsao_camera