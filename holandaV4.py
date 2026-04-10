#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.iodevices import LUMPDevice, DCMotor, Ev3devSensor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

####################################################################################################
ev3= EV3Brick()

sensor1= LUMPDevice(Port.S1)
#multiplex1= LUMPDevice(Port.S2)
sensor3= Ev3devSensor(Port.S3)
motorB = Motor(Port.D,)
motorC = Motor(Port.C,)



#VARIAVEIS/IMPORT
kp = 15 
kd = -9.5
ki = 0.001  

base = ((90) * 10) 

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
PESO_FORA = 2.5
contE = 0
contD = 0

tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5, axle_track=104)
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



def sensor():
    global old_error  
    global sensor1  
    global pretodir
    global pretoesq
    global timete
    global sensor3
    global derivative
    global integral
    global motorB
    global motorC
    global contD
    global contE
    global tanki
    while True:
        retorno = sensor1.read(2)
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
        red_tape1 = retorno[17]
        red_tape2 = retorno[18]
        red_tape3 = retorno[19]
        R1 = (retorno[4])
        G1 = (retorno[5])
        B1 = (retorno[6])
        C1 = (retorno[7])

        R3 = (retorno[8])
        G3 = (retorno[9])
        B3 = (retorno[10])
        C3 = (retorno[11])

        R2 = (retorno[12])
        G2 = (retorno[13])
        B2 = (retorno[14])
        C2 = (retorno[15])

        H1 = (retorno[20]*2)
        S1 = (retorno[21]*2)
        V1 = (retorno[22]*2)
        
        H3 = (retorno[23]*2)
        S3 = (retorno[24]*2)
        V3 = (retorno[25]*2)

        H2 = (retorno[26]*2)
        S2 = (retorno[27]*2)
        V2 = (retorno[28]*2)
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        posicao = (retorno[29]*2)
        gyro = sensor3.read("ACCEL")
        
        # Verifica se identificou uma rampa
        #if gyro == 10:  # Ajuste conforme necessário
         #   print("Rampa detectada!")
            
        # Verifica se viu vermelho
        if red_tape1 ==2 and red_tape2 ==2 and red_tape3 ==2:
            ev3.speaker.beep(1200,100)
            motorB.stop()
            motorC.stop()
            break
################################################################################################################
        # Verifica se viu prata
        esqgray = R1 > 120 and G1 > 120 and B1 > 120 and C1 > 70 
        mindgray = R3 > 120 and G3 > 120 and B3 > 120 and C3 > 70
        dirgray = R2 > 120 and G2 > 120 and B2 > 120 and C2 > 70
        
        esqgray1 = B1 > 55 and B1 < 60 and C1 > 27 and C1 < 32 and cloresq == 6
        mindgray1 = B3 > 55 and B3 < 60 and C3 > 27 and C3 < 32 and clormind == 6
        dirgray1 = B2 > 55 and B2 < 60 and C2> 27 and C2 < 32 and clordir == 6
        if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
           wait(30)
           if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
            tanki.stop()
            ev3.speaker.beep(900,100)
            print("prata encontrado..")
            break
###############################################################################################################        
        # Verifica se há um obstáculo
        #if distancia_obstaculo < 100:  # Ajuste conforme necessário
         #   print("Obstáculo detectado!")

########################################################################################
########################################################################################
        if fora1 <= 10:
            
            pretoesq = 160
            pretodir = 0

        if fora2 <= 10:
            
            pretodir = 160
            pretoesq = 0

        else:
             if pretoesq > 0:
                pretoesq = pretoesq - 1

             if pretodir > 0:
                pretodir = pretodir - 1
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################        
        alvo= 8
        # Verifica se viu verde
        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        
        if 0==0:
            if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo):
                wait(40)
                if verdeDireita:
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    motorB.run(-400)
                    motorC.run(400)
                    while True:
                        retorno= sensor1.read(2)
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        print("direita")
                        if verdeEsquerda:
                            contE= 1
                        if contE > 0:
                            contE = contE + 1

                        if contE > 15 or motorB.angle() > -400 or motorC.angle() < 400:
                            tanki.stop()
                            break
                    contD = 0
                    contE = 0
                    contM = 0
                    if contE > 1: # 2 verde
                        tanki.turn(100)
                        tanki.straight(500)
                        tanki.stop()
                        motorB.run(-999)
                        motorC.run(-999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 60:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        tanki.turn(-70)
                        tanki.stop()
                        wait(20)
                        tanki.stop()
                    else:
                        if cloresq == 1 or clordir == 1: # curva verde
                            if meio1 > 50 or meio2 > 50:
                                ev3.speaker.beep(300,100)
                                tanki.turn(100)
                                tanki.straight(170)
                                tanki.stop()
                        elif verdeDireita:
                            wait(40)
                            if verdeEsquerda: # 2verdes
                                tanki.turn(100)
                                tanki.straight(500)
                                tanki.stop()
                                motorB.run(999)
                                motorC.run(999)
                                while True:
                                    retorno = sensor1.read(2)
                                    meio1 = retorno[1]
                                    if meio1 <= 60:
                                        tanki.stop()
                                        contD = 0
                                        contE = 0
                                        contM = 0
                                        pretodir = 0
                                        pretoesq = 0
                                        break        
                                tanki.turn(-70)
                                tanki.stop()
                                wait(20)
                                tanki.stop()

#############################################################################################################################################################################################
            if H2 >=(90-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo):
                wait(40)
                if verdeEsquerda:
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    motorB.run(-400)
                    motorC.run(400)
                    while True:
                        retorno= sensor1.read(2)
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        print("esquerda")
                        if verdeDireita:
                            contD= 1
                        if contD > 0:
                            contD = contD + 1
                        if contD > 15 or motorB.angle() > -400 or motorC.angle() < 400:
                            tanki.stop()
                            break
                    contD = 0
                    contE = 0
                    contM = 0
                    if contD > 1: # 2 verde
                        tanki.turn(100)
                        tanki.straight(500)
                        tanki.stop()
                        motorB.run(999)
                        motorC.run(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 60:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        tanki.turn(-70)
                        tanki.stop()
                        wait(20)
                        tanki.stop()
                    else:
                        if cloresq == 1 or clordir == 1: # curva verde
                            if meio1 > 50 or meio2 > 50:
                                ev3.speaker.beep(300,100)
                                tanki.turn(100)
                                tanki.straight(-170)
                                tanki.stop()
                        elif verdeEsquerda:
                            wait(40)
                            if verdeDireita: # 2verdes
                                tanki.turn(100)
                                tanki.straight(500)
                                tanki.stop()
                                motorB.run(999)
                                motorC.run(999)
                                while True:
                                    retorno = sensor1.read(2)
                                    meio1 = retorno[1]
                                    if meio1 <= 60:
                                        tanki.stop()
                                        contD = 0
                                        contE = 0
                                        contM = 0
                                        pretodir = 0
                                        pretoesq = 0
                                        break        
                                tanki.turn(-70)
                                tanki.stop()
                                wait(20)
                                tanki.stop()

######################################################################################################################################################################################################
            if H3 >=(90-alvo) and H3 <=(110+alvo) and S3 >=(50-alvo) and S3 <=(70+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo):
                wait(45)
                if verdeMeio:      
                    ev3.speaker.beep(300,100)
                    if verdeEsquerda or verdeDireita:
                        if verdeMeio and verdeDireita:
                            print("Fdireita")
                            tanki.turn(100)
                            tanki.straight(100)
                            tanki.stop()
                            motorB.run(999)
                            motorC.run(999)
                            while True:
                                retorno = sensor1.read(2)
                                meio1 = retorno[1]
                                if meio1 <= 60:
                                    tanki.stop()
                                    contD = 0
                                    contE = 0
                                    contM = 0
                                    pretodir = 0
                                    pretoesq = 0
                                    break        
                            motorB.stop()
                            motorC.stop()
                        elif verdeMeio and verdeEsquerda:
                            print("fesquerda")
                            tanki.turn(100)
                            tanki.straight(-100)
                            tanki.stop()
                            motorB.run(-999)
                            motorC.run(-999)
                            while True:
                                retorno = sensor1.read(2)
                                meio1 = retorno[2]
                                if meio1 <= 60:
                                    tanki.stop()
                                    contD = 0
                                    contE = 0
                                    contM = 0
                                    pretodir = 0
                                    pretoesq = 0
                                    break        
                            motorB.stop()
                            motorC.stop()
                    elif fora1 <= 40 or meio2 <= 40:
                        print("curva para direita")
                        tanki.turn(150)
                        tanki.straight(100)
                        tanki.stop()
                        motorB.run(999)
                        motorC.run(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 60:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                    elif fora2 <= 40 or meio1 <= 40:
                        print("curva para esquerda")
                        tanki.turn(100)
                        tanki.straight(-100)
                        tanki.stop()
                        motorB.run(-999)
                        motorC.run(-999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 60:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                    
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
        
        if fora1 >= 90 and fora2 >= 90 and meio1 >= 90 and meio2 >= 90:
            if pretodir > 0: 
                tanki.turn(6)
                tanki.stop() 
                 
                motorB.stop()
                motorC.stop()
                    
                motorB.run(-999)
                motorC.run(-999)
                while True:
                    retorno = sensor1.read(2)
                    meio1 = retorno[2]
                    if meio1 <= 60:
                        tanki.stop()
                                
                        pretodir = 0
                        pretoesq = 0
                        break        
                motorB.stop()
                motorC.stop()
                
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa

            elif pretoesq > 0:
                tanki.turn(6)
                tanki.stop() 
                 
                motorB.stop()
                motorC.stop()
                    
                motorB.run(999)
                motorC.run(999)
                while True:
                    retorno = sensor1.read(2)
                    meio2 = retorno[1]
                    if meio2 <= 60:
                        tanki.stop()
                        
                        pretodir = 0
                        pretoesq = 0
                        break
                
                motorB.stop()
                motorC.stop()
                
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                
            else:
                ev3.speaker.beep(800, 100)
                pretodir = 0
                pretoesq = 0
                tanki.stop()
                print("gaap")
                
                motorB.run(-500)
                motorC.run(500)
                
                while True :
                    retorno = sensor1.read(2)
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    
                    if pretodir !=0  or pretoesq != 0:
                        break 
            
                    if meio1 <= 50 or meio2 <= 50:
                        motorB.stop()
                        motorC.stop()
                        wait(100)
                        break
                #frente
                tanki.stop()
                tanki.turn(-30)
                tanki.stop()
                certo = 1
                while True:
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    fora2 = retorno[3]
                    if fora1 < 50  or fora2 < 50:
                        certo = 0
                        break 
                    else:
                        certo = 1
                        break

                tanki.stop()
                while certo == 1 :
                    ev3.speaker.beep(100, 100)
                    if pretodir !=0  or pretoesq != 0:
                        certo =0
                        break 
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    motorB.run(500)
                    motorC.run(-500)
                    while True:     
                        if motorB.angle() > 620 or motorC.angle() < -620:
                            motorB.stop()
                            motorC.stop()
                            break
                    tanki.stop()
                
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        posicao = retorno[29]
                        whit1 = retorno[17]
                        whit2 = retorno[18]
                        whit3 = retorno[19]
                        
                        if fora1 < 40 or meio1 < 40 or meio2 < 40 or fora2 < 40 or whit2 == 0 :
                            if posicao > 1 or posicao < 1:
                                tanki.stop()
                                print("passou")
                                tanki.turn(30)
                                break
                        elif fora1 > 50 and meio1 > 50 and meio2 > 50 and fora2 > 50:
                            #camisinha
                            wait(300)
                            tanki.straight(-90)
                            tanki.stop()
                            if fora1 < 20 or meio1 < 20:
                                tanki.turn(50)
                                tanki.stop()
                                break
                            else:
                                wait(300)
                                tanki.straight(160)
                                tanki.stop()
                                if meio2 < 20 or fora2 < 20:
                                    tanki.turn(50)
                                    tanki.stop
                                    break
                                else:
                                    wait(300)
                                    tanki.straight(-90)
                                    tanki.stop()
                                    print("ré")
                                    tanki.turn(80)
                                    tanki.stop()
                                    if meio1 < 20 or meio2 < 20 or whit2 == 0:
                                        tanki.turn(50)
                                        tanki.stop()
                                        break
                                    else:
                                        motorB.run(-500)
                                        motorC.run(500)
                                        while True:
                                            retorno = sensor1.read(2)
                                            fora1 = retorno[0]
                                            meio1 = retorno[1]
                                            meio2 = retorno[2]
                                            fora2 = retorno[3]
                                            if fora1 < 40 or fora2 < 40 or meio1 < 40 or meio2 < 40:
                                                tanki.stop()
                                                break
                    break                                     
                tanki.turn(15)
                tanki.stop()
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                   #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
    

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

        motorB.run(powerB)
        motorC.run(powerC)

        old_error = error
    

#calibraBranco()
#calibraPreto()
sensor()
