class Segue:
    def __init__(self,motorB,motorC,PESO_FORA,PESO_MEIO):
        self.motorB = motorB
        self.motorC = motorC
        #self.kp = 2.5
        #self.kd = 0.1
        #self.ki = 0.01
        #self.base = 120
        self.integral = 0
        self.old_error = 0
        self.PESO_MEIO = PESO_MEIO
        self.PESO_FORA = PESO_FORA
    
    def PID(self,fora1,meio1,meio2,fora2,kp,kd,ki,base):
        #essas 4 variaveis vao sair daqui quando ja estiver com a programação que o robo identifica inclinação
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.base = base
        esquerda = (meio1 * self.PESO_MEIO) + (fora1 * self.PESO_FORA)
        direita = (meio2 * self.PESO_MEIO) + (fora2 * self.PESO_FORA)
        error = (esquerda - direita) * 0.5

        self.integral += error * 0.01 
        derivative = error - self.old_error
        corr = (error * (self.kp * (-1))) + (derivative * self.kd) + (self.integral * self.ki)
    
        powerB = self.base - corr
        powerC = -self.base - corr
        increPLUS= 0.5
        INCREplus= 1.0
        powerB = max(min(int(powerB * (increPLUS if powerB > 0 else INCREplus)), 900), -900)
        powerC = max(min(int(powerC * (INCREplus if powerC > 0 else increPLUS)), 900), -900)

        self.motorB.dc(powerB)
        self.motorC.dc(powerC)

        self.old_error = error