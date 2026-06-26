from pybricks.tools import wait
from gapwhite import Gapwhite

class Black909:
    def __init__(self, tanki, motorB, motorC, sensor1, ev3):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3
        self.gap = Gapwhite(tanki, motorB, motorC, sensor1, ev3)

    def blackORwhite(self, fora1, meio1, meio2, fora2, pretoesq, pretodir):
        if pretoesq > 0 : 
            print("90preto esquerda")
            #self.tanki.turn(5)
            self.tanki.stop() 
            self.motorB.stop()
            self.motorC.stop()
            wait(100)
            self.ev3.speaker.beep()
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            retorno = self.sensor1.read(2)
            fora2 = retorno[0] #direita 
            wait(100)
            while True:
                retorno = self.sensor1.read(2)
                fora2 = retorno[3] #direita  
                wait(100)
                print(fora2)
                if fora2 <= 50:
                    self.tanki.stop()
                    pretodir = 0
                    pretoesq = 0
                    break
            print("fez")
            wait(100)
            self.motorB.stop()
            self.motorC.stop() 
            self.tanki.stop()   
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            
        elif pretodir > 0 :
            print("90preto direita")
            #self.tanki.turn(5)
            self.tanki.stop() 
            self.motorB.stop()
            self.motorC.stop()
            wait(100)
            self.ev3.speaker.beep()
            self.motorB.dc(100)
            self.motorC.dc(100)
            self.motorB.dc(100)
            self.motorC.dc(100)
            retorno = self.sensor1.read(2)
            fora1 = retorno[3] #esquerda 
            wait(100)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[0] #esquerda 
                wait(100)
                print(fora1)
                if fora1 <= 50:
                    self.tanki.stop()
                    pretodir = 0
                    pretoesq = 0
                    contGap=0
                    break
            print("fez")
            wait(100)
            self.motorB.stop()
            self.motorC.stop()
            self.tanki.stop()
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
        else:
            self.ev3.speaker.beep()
            print("vendo branco")
            # self.motorB.dc(-100)
            # self.motorC.dc(100) #trás
            # retorno = self.sensor1.read(2)
            # while True:
            #     print("dando re")
            #     retorno = self.sensor1.read(2)
            #     fora1 = retorno[3] # esquerda 
            #     meio1 = retorno[2] # esquerda 
            #     meio2 = retorno[1] # direita  
            #     fora2 = retorno[0] # direita 
            #     if pretodir !=0  or pretoesq != 0:
            #         break
            #     if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
            #         self.motorB.stop()
            #         self.motorC.stop()
            #         break
            self.ev3.speaker.beep(600)
            # print("vendo gap")
            #self.gap.Litleshirt(fora1, meio1, meio2, fora2, pretoesq, pretodir)

        return pretoesq, pretodir