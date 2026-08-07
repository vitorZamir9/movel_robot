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
                   fora1, meio1, meio2, fora2, cloresq, clordir, pretoesq, pretodir):
        #=====================================
        # 0.0 ATUALIZAÇÃO DOS VALORES DOS SENSORES
        #=====================================
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
        contE = 0
        contD = 0
        ignore = 0
        #=====================================
        #BLOCOS DE VERDES
        #=====================================
        # r1 b1 g1, h1 s1 v1, cloresq

        #verde0 foi oq eu usei no regional e estadual
        verdeDireita0 = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio0 = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda0 = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)

        verdeDireita1 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(64-alvo) and S1 <=(72+alvo) and V1 >=(72-alvo) and V1 <=(74+alvo)
        verdeMeio1 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(64-alvo) and S3 <=(72+alvo) and V3 >=(72-alvo) and V3 <=(74+alvo)
        verdeEsquerda1 = H2 >=(110-alvo) and H2 <=(110+alvo) and S2 >=(60-alvo) and S2 <=(60+alvo) and V2 >=(86-alvo) and V2 <=(86+alvo)

        verdeDireita2 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(30-alvo) and S1 <=(30+alvo) and V1 >=(140-alvo) and V1 <=(140+alvo)
        verdeMeio2 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(30-alvo) and S3 <=(30+alvo) and V3 >=(140-alvo) and V3 <=(140+alvo)
        verdeEsquerda2 = H2 >=(95-alvo) and H2 <=(103+alvo) and S2 >=(40-alvo) and S2 <=(40+alvo) and V2 >=(127-alvo) and V2 <=(127+alvo)
        
        verdeDireita3 =  H1 >=(110-alvo) and H1 <=(110+alvo) and S1 >=(75-alvo) and S1 <=(75+alvo) and V1 >=(100-alvo) and V1 <=(100+alvo)
        verdeMeio3 = H3 >=(110-alvo) and H3 <=(110+alvo) and S3 >=(75-alvo) and S3 <=(75+alvo) and V3 >=(100-alvo) and V3 <=(100+alvo)
        verdeEsquerda3 = H2 >=(110-alvo) and H2 <=(110+alvo) and S2 >=(60-alvo) and S2 <=(60+alvo) and V2 >=(80-alvo) and V2 <=(80+alvo)

        verdeDireita = verdeDireita0 or verdeDireita1 or verdeDireita2 or verdeDireita3
        verdeMeio = verdeMeio0 or verdeMeio1 or verdeMeio2 or verdeMeio3
        verdeEsquerda = verdeEsquerda0 or verdeEsquerda1 or verdeEsquerda2 or verdeEsquerda3
        voltoudemais = False
        # ==================================
        # LÓGICA DA PRINCIPAL
        # ==================================
        retorno = self.sensor1.read(2)
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        H1 = (retorno[20]*2)
        S1 = (retorno[21]*2)
        V1 = (retorno[22]*2)
        H2 = (retorno[26]*2)
        S2 = (retorno[27]*2)
        V2 = (retorno[28]*2)
        if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo) and fora1 > meio1 and fora2 > meio2 :
            wait(10)
            if verdeDireita :
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                self.motorB.run(-70)
                self.motorC.run(70) #frente
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    #tanki.stop()
                    if verdeEsquerda:
                        contE= 1
                    if contE > 0:
                        contE = contE + 1
                    if contE >= 2:   
                        print("2verdes")
                        verde=2
                        break
                    print(contE)
                    if verdeDireita and fora1 > meio1 and fora2 > meio2:
                        print("direita")
                        verde=1
                        break
                self.tanki.stop()
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.motorB.run(100)
                self.motorC.run(-100) #tras
                while True:
                    wait(100)
                    print(self.motorB.angle(),self.motorC.angle())
                    if self.motorB.angle() >= 80:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                wait(1000) ##########################################################<<<<<<<<<<<<
                retorno = self.sensor1.read(2)
                fora1 = retorno[0]
                meio1 = retorno[1]
                meio2 = retorno[2]
                fora2 = retorno[3]
                cloresq = retorno[17]
                clormind = retorno[18]
                clordir = retorno[19]
                H1 = (retorno[20]*2)
                S1 = (retorno[21]*2)
                V1 = (retorno[22]*2)
                H2 = (retorno[26]*2)
                S2 = (retorno[27]*2)
                V2 = (retorno[28]*2)
                verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.motorB.run(-100)
                self.motorC.run(100) #frente
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    print(self.motorB.angle(),self.motorC.angle())
                    if verdeDireita or verdeEsquerda:
                        self.tanki.stop()
                        verde=0
                        verde=0
                        break
                    elif fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                        self.tanki.stop()
                        verde=1
                        verde=1
                        break
                self.tanki.stop()
                print(verde)
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if verde == 0:#vai pra tras conferir
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    self.motorB.run(-100)
                    self.motorC.run(100) #frente
                    while True:
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        print(self.motorB.angle(),self.motorC.angle())
                        if self.motorB.angle() <= -30 and verdeDireita or verdeEsquerda:
                            self.tanki.stop()
                            verde= 10
                            break
                        if self.motorB.angle() <= -35:
                            self.tanki.stop()
                            print("ele passou muito pra tras")
                            verde=11
                            break
                    self.tanki.stop()
                    print(verde)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                #######conefirir
                if verde == 11:
                    print("ele veio aqui")
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    self.motorB.run(100)
                    self.motorC.run(-100) #tras
                    while True:
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        print(self.motorB.angle(),self.motorC.angle())
                        if self.motorB.angle() >= 90:
                            self.tanki.stop()
                            break
                    self.tanki.stop()
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if verde == 10:
                    self.tanki.stop()
                    print("verde antes")
                    verde = 1
                    
                    self.tanki.stop()
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                ###########################################3
                if verde ==1:
                    self.motorB.run(-100)
                    self.motorC.run(100) #frente
                    while True:
                        retorno = self.sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        print(self.motorB.angle(),self.motorC.angle())
                        if verdeEsquerda:
                            if verdeDireita:
                                self.tanki.stop()
                                verde=2
                                break
                        elif self.motorB.angle() < -100:
                            self.tanki.stop()
                            break
                    print(verde)        
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if verde == 1:
                    print("verde direita")
                    self.tanki.turn(80)
                    self.tanki.straight(50)
                    self.tanki.stop()
                    self.motorB.run(999)
                    self.motorC.run(999) 
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[1]
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                    self.tanki.turn(-10)
                    self.tanki.stop()
                elif verde == 2:
                    print("2verdesss")
                    self.tanki.turn(30)
                    self.tanki.straight(190)
                    self.tanki.stop()
                    self.motorB.dc(999)
                    self.motorC.dc(999)
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[1]
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                    self.tanki.turn(-10)
                    self.tanki.stop()
                

#############################################################################################################################################################################################
        retorno = self.sensor1.read(2)
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        H1 = (retorno[20]*2)
        S1 = (retorno[21]*2)
        V1 = (retorno[22]*2)
        H2 = (retorno[26]*2)
        S2 = (retorno[27]*2)
        V2 = (retorno[28]*2)
        if H2 >=(90-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo) and fora1 > meio1 and fora2 > meio2:
            wait(10)
            if verdeEsquerda :
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                self.motorB.run(-70)
                self.motorC.run(70) #frente
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    #tanki.stop()
                    if verdeDireita:
                        contD= 1
                    if contD > 0:
                        contD = contD + 1
                    if contD >= 2:   
                        print("2verdes")
                        verde=2
                        break
                    print(contD)
                    if verdeEsquerda and fora1 > meio1 or fora2 > meio2:
                        print("esquerda")
                        verde=1
                        break
                self.tanki.stop()
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.motorB.run(100)
                self.motorC.run(-100) #tras
                while True:
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    print(self.motorB.angle(), self.motorC.angle())
                    if self.motorB.angle() >= 80:
                        self.tanki.stop()
                        break
                self.tanki.stop()
                wait(1000)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                retorno = self.sensor1.read(2)
                fora1 = retorno[0]
                meio1 = retorno[1]
                meio2 = retorno[2]
                fora2 = retorno[3]
                cloresq = retorno[17]
                clormind = retorno[18]
                clordir = retorno[19]
                H1 = (retorno[20]*2)
                S1 = (retorno[21]*2)
                V1 = (retorno[22]*2)
                H2 = (retorno[26]*2)
                S2 = (retorno[27]*2)
                V2 = (retorno[28]*2)
                verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                self.motorB.reset_angle(0)
                self.motorC.reset_angle(0)
                wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                self.motorB.run(-100)
                self.motorC.run(100) #frente
                while True:
                    retorno = self.sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    print(self.motorB.angle(), self.motorC.angle())
                    if verdeDireita or verdeEsquerda:
                        self.tanki.stop()
                        verde=0
                        verde=0
                        break
                    elif fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                        self.tanki.stop()
                        verde=1
                        verde=1
                        break
                self.tanki.stop()
                print(verde)
                wait(1000)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if verde ==0:
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    self.motorB.run(100)
                    self.motorC.run(-100) #tras
                    while True:
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        print(self.motorB.angle(), self.motorC.angle())
                        if self.motorB.angle() >= 90:
                            self.tanki.stop()
                            break
                    self.tanki.stop()
                    wait(1000)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                ###########################################3
                if verde ==1:
                    self.motorB.run(-100)
                    self.motorC.run(100) #frente
                    while True:
                        retorno = self.sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        print(self.motorB.angle(), self.motorC.angle())
                        if verdeDireita:
                            if verdeEsquerda:
                                self.tanki.stop()
                                verde=2
                                break
                        elif self.motorB.angle() < -100:
                            self.tanki.stop()
                            break
                    print(verde)       
                    wait(1000)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if verde == 1 and verde == 1:
                    print("verde esquerda")
                    self.tanki.turn(50)
                    self.tanki.straight(-50)
                    self.tanki.stop()
                    self.motorB.run(-999)
                    self.motorC.run(-999)
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[2]
                        wait(100)#######################################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                    self.tanki.turn(-10)
                    self.tanki.stop()
                elif verde == 2 and verde == 2:
                    print("2verdesss")
                    self.tanki.turn(30)
                    self.tanki.straight(190)
                    self.tanki.stop()
                    self.motorB.dc(999)
                    self.motorC.dc(999)
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[1]
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                    self.tanki.turn(-10)
                    self.tanki.stop()

######################################################################################################################################################################################################
        if H3 >=(90-alvo) and H3 <=(110+alvo) and S3 >=(50-alvo) and S3 <=(70+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo):
            wait(30)
            if verdeMeio and not fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:      
                self.ev3.speaker.beep(600,100)
                if verdeEsquerda or verdeDireita:
                    if verdeMeio and verdeDireita and fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                        print("FdireitaMM")
                        self.tanki.turn(70)
                        self.tanki.straight(50)
                        self.tanki.stop()
                        self.motorB.run(999)
                        self.motorC.run(999)
                        while True:
                            retorno = self.sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 65:
                                self.tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        self.motorB.stop()
                        self.motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                    elif verdeMeio and verdeEsquerda and fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                        print("fesquerdaMM")
                        self.tanki.turn(70)
                        self.tanki.straight(-50)
                        self.tanki.stop()
                        self.motorB.run(-999)
                        self.motorC.run(-999)
                        while True:
                            retorno = self.sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 65:
                                self.tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        self.motorB.stop()
                        self.motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                elif fora1 <= 40 or meio2 <= 40:
                    print("curva para direitaMM")
                    self.tanki.turn(50)
                    self.tanki.straight(50)
                    self.tanki.stop()
                    self.motorB.run(999)
                    self.motorC.run(999)
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[1]
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                elif fora2 <= 40 or meio1 <= 40:
                    print("curva para esquerdaMM")
                    self.tanki.turn(50)
                    self.tanki.straight(-50)
                    self.tanki.stop()
                    self.motorB.run(-999)
                    self.motorC.run(-999)
                    while True:
                        retorno = self.sensor1.read(2)
                        meio1 = retorno[2]
                        if meio1 <= 65:
                            self.tanki.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break        
                    self.motorB.stop()
                    self.motorC.stop()
                    contD = 0
                    contE = 0
                    contM = 0
                    pretodir = 0
                    pretoesq = 0
                    
        return None