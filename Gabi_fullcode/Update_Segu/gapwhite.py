from pybricks.tools import wait, StopWatch

class Gapwhite:
    def __init__(self, tanki, motorB, motorC, sensor1, ev3):
        self.tanki = tanki
        self.motorB = motorB
        self.motorC = motorC
        self.sensor1 = sensor1
        self.ev3 = ev3

    def Litleshirt(self, fora1, meio1, meio2, fora2, pretoesq, pretodir):
        # GAP
        self.ev3.speaker.beep(1000)
        print("gaap")
        self.motorB.reset_angle(0)
        self.motorC.reset_angle(0)
        wait(100)
        self.motorB.dc(70)
        self.motorC.dc(-70) #frente
        retorno = self.sensor1.read(2)
        dezOUcincoCM = None
        while True:
            retorno = self.sensor1.read(2)
            fora1 = retorno[3] # esquerda 
            meio1 = retorno[2] # esquerda 
            meio2 = retorno[1] # direita  
            fora2 = retorno[0] # direita 
            if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                self.motorB.stop()
                self.motorC.stop()
                dezOUcincoCM = 1
                break
            elif self.motorB.angle() >= 120: #ajustar angulo do gap para 5cm
                dezOUcincoCM = 0
                break
        if dezOUcincoCM < 1:
            # ==========================================
            # 1. GIRA 45° ESQUERDA
            # ==========================================
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            self.motorB.dc(-100)
            self.motorC.dc(-100) #esquerda
            retorno = self.sensor1.read(2)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita 
                if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    if meio2 > meio1:
                        self.motorB.dc(-100)
                        self.motorC.dc(-100)
                        retorno = self.sensor1.read(2)
                        while True:
                            meio1 = retorno[2] # esquerda 
                            meio2 = retorno[1] # direita 
                            if meio2 < meio1:
                                self.motorB.stop()
                                self.motorC.stop()
                                break
                        cronometro = StopWatch()
                        tempo_limite = 300  
                        while cronometro.time() < tempo_limite:
                            retorno = self.sensor1.read(2)
                            f1, m1, m2, f2 = retorno[3], retorno[2], retorno[1], retorno[0]
                            self.meu_pid.PID(f1, m1, m2, f2, 2.8, 0, 0.15, 100)
                            wait(10)
                    return #sai da classe
                elif self.motorC.angle() <= -45:
                    self.motorB.stop()
                    self.motorC.stop()
                    break
            # ==========================================
            # 2. GIRA 90° DIREITA
            # ==========================================
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.motorB.dc(100)
            self.motorC.dc(100)
            self.motorB.dc(100)
            self.motorC.dc(100) #direita
            retorno = self.sensor1.read(2)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita 
                if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    if meio1 > meio2:
                        self.motorB.dc(100)
                        self.motorC.dc(100)
                        retorno = self.sensor1.read(2)
                        while True:
                            meio1 = retorno[2] # esquerda 
                            meio2 = retorno[1] # direita 
                            if meio1 < meio2:
                                self.motorB.stop()
                                self.motorC.stop()
                                break
                        cronometro = StopWatch()
                        tempo_limite = 300  
                        while cronometro.time() < tempo_limite:
                            retorno = self.sensor1.read(2)
                            f1, m1, m2, f2 = retorno[3], retorno[2], retorno[1], retorno[0]
                            self.meu_pid.PID(f1, m1, m2, f2, 2.8, 0, 0.15, 100)
                            wait(10)
                    return #sai da classe
                elif self.motorB.angle() >= 90:
                    self.motorB.stop()
                    self.motorC.stop()
                    break
            # ==========================================
            # 3. GIRA 135° ESQUERDA
            # ==========================================
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            self.motorB.dc(-100)
            self.motorC.dc(-100) #esquerda
            retorno = self.sensor1.read(2)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita 
                if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    if meio2 > meio1:
                        self.motorB.dc(-100)
                        self.motorC.dc(-100)
                        retorno = self.sensor1.read(2)
                        while True:
                            meio1 = retorno[2] # esquerda 
                            meio2 = retorno[1] # direita 
                            if meio2 < meio1:
                                self.motorB.stop()
                                self.motorC.stop()
                                break
                        cronometro = StopWatch()
                        tempo_limite = 300  
                        while cronometro.time() < tempo_limite:
                            retorno = self.sensor1.read(2)
                            f1, m1, m2, f2 = retorno[3], retorno[2], retorno[1], retorno[0]
                            self.meu_pid.PID(f1, m1, m2, f2, 2.8, 0, 0.15, 100)
                            wait(10)
                    return #sai da classe
                elif self.motorC.angle() <= -135:
                    self.motorB.stop()
                    self.motorC.stop()
                    break
            # ==========================================
            # 4. GIRA 180° DIREITA
            # ==========================================
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.motorB.dc(100)
            self.motorC.dc(100)
            self.motorB.dc(100)
            self.motorC.dc(100) #direita
            retorno = self.sensor1.read(2)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita 
                if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    if meio1 > meio2:
                        self.motorB.dc(100)
                        self.motorC.dc(100)
                        retorno = self.sensor1.read(2)
                        while True:
                            meio1 = retorno[2] # esquerda 
                            meio2 = retorno[1] # direita 
                            if meio1 < meio2:
                                self.motorB.stop()
                                self.motorC.stop()
                                break
                        cronometro = StopWatch()
                        tempo_limite = 300  
                        while cronometro.time() < tempo_limite:
                            retorno = self.sensor1.read(2)
                            f1, m1, m2, f2 = retorno[3], retorno[2], retorno[1], retorno[0]
                            self.meu_pid.PID(f1, m1, m2, f2, 2.8, 0, 0.15, 100)
                            wait(10)
                    return #sai da classe
                elif self.motorB.angle() >= 180:
                    self.motorB.stop()
                    self.motorC.stop()
                    break
            # ==========================================
            # 5. GIRA 90° ESQUERDA E FICA RETO NOVAMENTE
            # ==========================================
            self.motorB.reset_angle(0)
            self.motorC.reset_angle(0)
            self.motorB.dc(-100)
            self.motorC.dc(-100)
            self.motorB.dc(-100)
            self.motorC.dc(-100) #esquerda
            while True:
                if self.motorC.angle() <= -90:
                    self.motorB.stop()
                    self.motorC.stop()
                    break
            # ==========================================
            # 6. ENCONTRA LINHA INICIAL
            # ==========================================
            self.motorB.dc(-100)
            self.motorC.dc(100) #trás
            retorno = self.sensor1.read(2)
            while True:
                retorno = self.sensor1.read(2)
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita 
                if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
                    self.motorB.stop()
                    self.motorC.stop()
                    return # sai da classe e volta pro loop
        else:
            return
        #fazer com que o robo agora va para o outro lado
        #ou seja fazer com que o robo va para frente ate ver a linha preta
        #utilizar os sensores fora1,meio1,meio2,fora2 para poder identificar a linha
        #importante que o gap não atrapalhe a correção quando o robo perde a linha