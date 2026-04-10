#!/usr/bin/env pybricks-micropython

# Classe para controlar os servos da placa de servos via porta serial
class Servos:
    def __init__(self, portaServos, atualizaInstantaneo = False):
        self.lista = [0xff, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]
        self.ser = portaServos
        self.atualizaInstantaneo = atualizaInstantaneo

    def move(self,servo,angulo):
        if(servo <= 0):
            return
        if(servo > 6):
            return
        if(angulo < 0):
            angulo = 0
        if(angulo > 180):
            angulo = 180
        self.lista[servo] = angulo
        if self.atualizaInstantaneo:
            self.atualiza()

    def atualiza(self):
        self.ser.write(bytes(self.lista))

    def desativa(self,servo):
        if(servo <= 0):
            return
        if(servo > 6):
            return
        self.lista[servo] = 200 #maior que 180 desativa ele
        if self.atualizaInstantaneo:
            self.atualiza()
