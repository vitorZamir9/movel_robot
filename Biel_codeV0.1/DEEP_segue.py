#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.iodevices import LUMPDevice, DCMotor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

# Instância do EV3 Brick
ev3 = EV3Brick()

# Configuração dos motores
motorB = Motor(Port.D)
motorC = Motor(Port.C)

# Configuração dos sensores de cor
sensor1 = LUMPDevice(Port.S1)

# ====== PARTE MODIFICADA (SEGUIDOR DE LINHA) ======
kp = 13 
kd = -9   
ki = 0.001   

base = ((90) * 10)  

old_error = 0
integral = 0

PESO_MEIO = 1
PESO_FORA = 2

while True:
    retorno = sensor1.read(2)
    fora1 = retorno[0]
    meio1 = retorno[1]
    meio2 = retorno[2]
    fora2 = retorno[3]

    esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
    direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
    error = (direita - esquerda) * 0.5

    integral += error * 0.01 
    derivative = error - old_error
    corr = (error * (kp * (-1))) + (derivative * kd) + (integral * ki)
    
    # Ajuste assimétrico da potência (frente mais fraco que ré)
    powerB = base - corr
    powerC = -base - corr

    # Atenua potência positiva (frente) e mantém/amplifica negativa (ré)
    powerB = max(min(int(powerB * (0.5 if powerB > 0 else 1.0)), 900), -900)
    powerC = max(min(int(powerC * (1.0 if powerC > 0 else 0.5)), 900), -900)

    motorB.run(powerB)
    motorC.run(powerC)

    old_error = error
