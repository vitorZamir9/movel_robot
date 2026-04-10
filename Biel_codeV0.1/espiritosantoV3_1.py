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

####################################################################################################
ev3= EV3Brick()
sensor1 = LUMPDevice(Port.S1)
motorB = Motor(Port.C,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
#VARIAVEIS/IMPORT
error = 0
powerB = 0
powerC = 0
corr = 0
old_error = 0
pretoesq = 0
pretodir = 0
integral = 0
derivative = 0
PESO_MEIO = 1
PESO_FORA = 2.25
contE = 0
contD = 0
tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5 , axle_track=104.0)
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
####initi####
def calibraBranco():
    retorno = sensor1.read(3)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(3)
        wait(100)
    print("Calibrado Branco")

def calibraPreto():
    retorno = sensor1.read(4)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(4)
        wait(100)
    print("Calibrado Preto")

#################################################################

def sensor():
    global old_error  
    global sensor1  
    global timete
    global derivative
    global integral
    global motorB
    global motorC
    while True:
        retorno = sensor1.read(2)
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
       
        kp = 7
        kd = 20
        ki = 0.001  
        base = ((50) * 10)

        esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
        direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
        error = (direita - esquerda) * 0.5

        integral += error * 0.01 
        derivative = error - old_error
        corr = (error * (kp * (-1))) + (derivative * kd) + (integral * ki)
    
        powerB = base - corr
        powerC = -base - corr
        increPLUS=0.5
        INCREplus=1.0
        powerB = max(min(int(powerB * (increPLUS if powerB > 0 else INCREplus)), 900), -900)
        powerC = max(min(int(powerC * (INCREplus if powerC > 0 else increPLUS)), 900), -900)

        motorB.dc(powerB)
        motorC.dc(powerC)

        old_error = error
#calibraBranco()
#calibraPreto()
sensor()
