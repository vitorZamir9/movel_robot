from pybricks.tools import wait

class Black909:
    def __init__(self, tanki, motorB, motorC, sensor1, ev3):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3

    def blackORwhite(self, fora1, meio1, meio2, fora2, pretoesq, pretodir):
        if pretodir > 0: 
            print("90preto esquerda")
            self.tanki.turn(10)
            self.tanki.stop() 
            self.motorB.stop()
            wait(100)
            self.ev3.speaker.beep()
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            retorno = self.sensor1.read(0)
            fora2 = retorno[3] #direita  REAL>>>esquerda
            wait(100)
            while True:
                retorno = self.sensor1.read(0)
                fora2 = retorno[3] #direita  REAL>>>esquerda
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
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            
        elif pretoesq > 0:
            print("90preto direita")
            self.tanki.turn(10)
            self.tanki.stop() 
            self.motorB.stop()
            wait(100)
            self.ev3.speaker.beep()
            self.motorB.dc(100)
            self.motorC.dc(100)
            self.motorB.dc(100)
            self.motorC.dc(100)
            retorno = self.sensor1.read(0)
            fora1 = retorno[0] #esquerda REAL>>>direita
            wait(100)
            while True:
                retorno = self.sensor1.read(0)
                fora1 = retorno[0] #esquerda REAL>>>direita
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
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            
        else:
            # GAP
            self.ev3.speaker.beep(100)
            self.tanki.stop()
            
            # Vai para frente reto
            self.tanki.drive(100, 0)
            
            # Fica lendo até achar a linha preta
            while True:
                retorno = self.sensor1.read(2) # Lê todos os sensores
                fora1_gap = retorno[0]
                meio1_gap = retorno[1]
                meio2_gap = retorno[2]
                fora2_gap = retorno[3]
                
                if fora1_gap <= 50 or meio1_gap <= 50 or meio2_gap <= 50 or fora2_gap <= 50:
                    self.tanki.stop()
                    break

            #fazer com que o robo agora va para o outro lado
            #ou seja fazer com que o robo va para frente ate ver a linha preta
            #utilizar os sensores fora1,meio1,meio2,fora2 para poder identificar a linha
            #importante que o gap não atrapalhe a correção quando o robo perde a linha
            
        return pretoesq, pretodir