from pybricks.tools import wait
from gapwhite import Gapwhite

class Black909:
    def __init__(self, tanki, motorB, motorC, sensor1, ev3, ts):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3
        self.ts = ts
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
            # ── GAP detectado pela câmera ─────────────────────────────
            # A Raspberry mandou "gap" ou "gap angulo {graus}"
            # Se tiver ângulo, giramos até endireitar, depois seguimos
            self.ev3.speaker.beep()
            print("GAP detectado")

            angulo = self.ts.gap_angulo   # None se não veio ângulo

            if angulo is not None and abs(angulo) > 5:
                # Gira para alinhar com a linha antes do gap (angulo → 0)
                print("Alinhando gap: angulo=", angulo)
                sentido = -1 if angulo > 0 else 1
                self.motorB.dc(60 * sentido)
                self.motorC.dc(-60 * sentido)
                wait(abs(int(angulo * 8)))   # ~8ms por grau, ajuste conforme robô
                self.motorB.stop()
                self.motorC.stop()
                wait(100)

            # Avança reto para cruzar o gap
            self.motorB.dc(60)
            self.motorC.dc(-60)
            wait(400)   # ajuste conforme largura do gap
            self.motorB.stop()
            self.motorC.stop()
            wait(100)
            self.ev3.speaker.beep(600)
            # print("vendo gap")
            #self.gap.Litleshirt(fora1, meio1, meio2, fora2, pretoesq, pretodir)

        return pretoesq, pretodir