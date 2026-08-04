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
        alvo = 10 # Alvo para a calibração do HSV do verde
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
        # ==================================
        # LÓGICA DA PRINCIPAL
        # ==================================
        if verdeDireita or verdeMeio or verdeEsquerda: 
            self.tanki.stop()
            # ==================================
            # LÓGICA DA DIREITA
            # ==================================
            if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo) and fora1 > meio1 and fora2 > meio2 :
                wait(30)
                #utilizando um valor com uma calibração mais suave e que pega uma margem boa de verdes
                if verdeDireita:
                    print("fazer logica do verde, partindo da identificação do verde na direita")
                    self.motorB.stop()
                    self.motorC.stop()
                    self.tanki.stop()
                    self.motorB.reset_angle(0)
                    self.motorC.reset_angle(0)
                    # OBS: fazer verficação com motor.run pois a movimentação lenta é escenssial para o verde
                    # vai pra tras dentro de um while, onde ele vai perguntar se esta vendo verde com o outro sensor atraves de um somatorio,senão ele vai fazer o verde que ele viu primeiro
                    #
                return None
            # ==================================
            # LÓGICA DA ESQUERDA
            # ==================================
            elif H2 >=(90-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo) and fora1 > meio1 and fora2 > meio2 :
                wait(30)
                #utilizando um valor com uma calibração mais suave e que pega uma margem boa de verdes
                if verdeEsquerda:
                    print("fazer logica do verde, partindo da identificação do verde na esquerda")
                return None
            # ==================================
            # LÓGICA DO MEIO
            # ==================================
            elif H3 >=(90-alvo) and H3 <=(110+alvo) and S3 >=(50-alvo) and S3 <=(70+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo): #foi torto e viu o verde no meio
                wait(30)
                #utilizando um valor com uma calibração mais suave e que pega uma margem boa de verdes
                if verdeMeio:
                    print("fazer logica do verde, partindo da identificação do verde no meio")
                return None
        return None