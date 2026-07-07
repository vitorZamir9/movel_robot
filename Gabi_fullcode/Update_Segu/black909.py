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
        if pretodir > 0 : 
            print("90preto esquerda")
            while True:
                self.motorB.dc(80)
                self.motorC.dc(80)
                retorno = self.sensor1.read(2)
                meio2 = retorno[1] #direita  
                
                print(meio2)
                if meio2 <= 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    pretodir = 0
                    pretoesq = 0
                    break
            
            print("fez preto esquerda")
            wait(100)
            #tsttttttttttttttttttt direitaaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaaa
            
            
            
        elif pretoesq > 0 :
            print("90preto direita")
            while True:
                self.motorB.dc(-80)
                self.motorC.dc(-80)
                retorno = self.sensor1.read(2)
                meio1 = retorno[2] #direita  
                
                print(meio1)
                if meio1 <= 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    pretodir = 0
                    pretoesq = 0
                    break
            
            print("fez preto direita")
            wait(100)
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