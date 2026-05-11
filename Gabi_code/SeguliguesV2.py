#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.iodevices import LUMPDevice, DCMotor, Ev3devSensor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pybricks.iodevices import UARTDevice
import sys
import time

# Importa a tua nova classe!
from controlVerde import ControlVerde

ev3 = EV3Brick()
sensor1 = LUMPDevice(Port.S1)
motorB = Motor(Port.B, gears=[12,25], positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D, gears=[12,25], positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)

tanki = DriveBase(motorB, motorC, wheel_diameter=55.5, axle_track=104.0)
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

PESO_MEIO = 1.0
PESO_FORA = 2.25

# INICIALIZA A CLASSE AQUI
controle_do_verde = ControlVerde(ev3, motorB, motorC, tanki, ser, sensor1)

def sensor():
    old_error = 0
    integral = 0
    pretoesq = 0
    pretodir = 0

    while True:
        # ====================================================
        # 1. LEITURA GERAL
        # ====================================================
        controle_do_verde.atualizar_memoria_serial()
        retorno = sensor1.read(2)
        
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]

        # ====================================================
        # 2. NAVEGAÇÃO: PID 
        # ====================================================
        kp = 1.5
        kd = 0.5
        ki = 0.01
        base = 100

        esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
        direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
        error = (direita - esquerda) * 0.5

        integral += error * 0.01 
        derivative = error - old_error
        corr = (error * (kp * (-1))) + (derivative * kd) + (integral * ki)
        
        powerB = base - corr
        powerC = -base - corr
        
        powerB = max(min(int(powerB * (0.5 if powerB > 0 else 1.0)), 900), -900)
        powerC = max(min(int(powerC * (1.0 if powerC > 0 else 0.5)), 900), -900)

        motorB.dc(powerB)
        motorC.dc(powerC)

        old_error = error

        # ====================================================
        # 3. VERIFICAÇÃO DE VERDE (Abaixo do Seguidor)
        # ====================================================
        # Se for verde, a classe domina o robô, trava os motores que 
        # acabaram de receber o pulso do PID, faz o giro e solta.
        controle_do_verde.verificar_e_agir(retorno)

        # ====================================================
        # 4. MEMÓRIA DE CURVA DE 90 GRAUS (Prioridade Baixa)
        # ====================================================
        if fora1 <= 10:
            pretoesq = 140
            pretodir = 0
        if fora2 <= 10:
            pretodir = 140
            pretoesq = 0
        else:
            if pretoesq > 0:
                pretoesq -= 1
            if pretodir > 0:
                pretodir -= 1



#calibraBranco()
#calibraPreto()
sensor()
