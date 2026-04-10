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
multiplex1 = LUMPDevice(Port.S2)
sensor3= Ev3devSensor(Port.S3)
motorB = Motor(Port.D,)
motorC = Motor(Port.C,)
ser = UARTDevice(Port.S5, baudrate=115200, timeout=1)


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
data= ser.read_all()
ser.write(b'off\r\n')
resgatt=0

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
    global multiplex1
    global ser
    global data_str
    global resgatt
    while True:
        retorno1= multiplex1.read(0)
        ultrafrente= retorno1[3]
        ultratras= retorno1[2]
        ultradireita= retorno1[1]
        ultraesquerda= retorno1[0]
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
        contGap = 1
        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
        #print(data)
        # Verifica se identificou uma rampa
        #if gyro == 10:  # Ajuste conforme necessário
         #   print("Rampa detectada!")
            
        # Verifica se viu vermelho
        if red_tape1 ==2 and red_tape2 ==2 and red_tape3 ==2:
            ev3.speaker.beep(1200)
            motorB.stop()
            motorC.stop()
            break
################################################################################################################
        # Verifica se viu prata
        clear = 40
        esqgray = R1 > 105 and G1 > 105 and B1 > 105 and C1 > clear 
        mindgray = R3 > 105 and G3 > 105 and B3 > 105 and C3 > clear #prata reflectivo
        dirgray = R2 > 105 and G2 > 105 and B2 > 105 and C2 > clear 
        
        esqgray1 = B1 > 55 and B1 < 61 and C1 > 25 and C1 < 31 and cloresq == 6
        mindgray1 = B3 > 55 and B3 < 61 and C3 > 25 and C3 < 31 and clormind == 6 #calibrar o prata não reflectivo
        dirgray1 = B2 > 55 and B2 < 61 and C2> 25 and C2 < 31 and clordir == 6

        if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
            wait(10)
            if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
                tanki.stop()
                ev3.speaker.beep(900)
                tanki.turn(-70)
                ev3.speaker.beep(900,600)
                ev3.speaker.beep()
                tanki.stop()
                wait(500)
                if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
                    wait(10)
                    if esqgray and mindgray and dirgray or esqgray1 and mindgray1 and dirgray1:
                        tanki.stop()
                        print("resgate on")
                        ev3.speaker.beep()
                        count=0
                        while count < 2:
                            tanki.turn(-10)
                            tanki.stop()
                            motorB.run(200)
                            motorC.run(-200)
                            while True:
                                retorno = sensor1.read(2)
                                cloresq = retorno[17]
                                clordir = retorno[19]
                                meio1 = retorno[2]
                                meio2 = retorno[1]
                                if  meio1 > 95 and meio2 > 95 :
                                    tanki.stop()
                                    break     
                            #ficar reto
                        
                            motorB.run(-350)
                            motorC.run(0)
                            while True:
                                retorno = sensor1.read(2)
                                cloresq = retorno[17]
                                clordir = retorno[19]
                                meio1 = retorno[2]
                                meio2 = retorno[1]
                                if  meio1 < 70:
                                    tanki.stop()
                                    break    
                            #mais pra trás
                            ev3.speaker.beep(500)
                            motorB.run(0)
                            motorC.run(350)
                            while True:
                                retorno = sensor1.read(2)
                                cloresq = retorno[17]
                                clordir = retorno[19]
                                meio1 = retorno[2]
                                meio2 = retorno[1]
                                if meio2 > 30:
                                    tanki.stop()
                                    break 
                            #ver prata
                            motorB.run(350)
                            motorC.run(0)
                            while True:
                                retorno = sensor1.read(2)
                                esqgray = R1 > 105 and G1 > 105 and B1 > 105 and C1 > clear 
                                mindgray = R3 > 105 and G3 > 105 and B3 > 105 and C3 > clear #prata reflectivo
                                dirgray = R2 > 105 and G2 > 105 and B2 > 105 and C2 > clear 
                                esqgray1 = B1 > 55 and B1 < 61 and C1 > 25 and C1 < 31 and cloresq == 6
                                mindgray1 = B3 > 55 and B3 < 61 and C3 > 25 and C3 < 31 and clormind == 6 #calibrar o prata não reflectivo
                                dirgray1 = B2 > 55 and B2 < 61 and C2> 25 and C2 < 31 and clordir == 6
                                if esqgray or esqgray1:
                                    tanki.stop()
                                    pretodir = 0
                                    pretoesq = 0
                                    break     
                            #ver prata
                            motorB.run(0)
                            motorC.run(-350)
                            while True:
                                retorno = sensor1.read(2)
                                esqgray = R1 > 105 and G1 > 105 and B1 > 105 and C1 > clear 
                                mindgray = R3 > 105 and G3 > 105 and B3 > 105 and C3 > clear #prata reflectivo
                                dirgray = R2 > 105 and G2 > 105 and B2 > 105 and C2 > clear 
                                esqgray1 = B1 > 55 and B1 < 61 and C1 > 25 and C1 < 31 and cloresq == 6
                                mindgray1 = B3 > 55 and B3 < 61 and C3 > 25 and C3 < 31 and clormind == 6 #calibrar o prata não reflectivo
                                dirgray1 = B2 > 55 and B2 < 61 and C2> 25 and C2 < 31 and clordir == 6
                                if dirgray or dirgray1:
                                    tanki.stop()
                                    pretodir = 0
                                    pretoesq = 0
                                    break    
                            count += 1
                        #entrar no resgate
                        count=0
                        ser.write(b'Resgate_ON\r\n')
                        tanki.stop()
                        tanki.settings(turn_rate=400, turn_acceleration=999)
                        ev3.speaker.beep(400,1000)
                        ev3.speaker.beep(100)
                        wait(200)
                        tanki.turn(400)
                        tanki.stop()
                        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
                        ev3.speaker.beep() 
                        #saber onde entrou no resgate
                        while True:
                            retorno1= multiplex1.read(0)
                            ultrafrente= retorno1[3]
                            ultratras= retorno1[2]
                            ultradireita= retorno1[1]
                            ultraesquerda= retorno1[0]
                            print(ultradireita,ultraesquerda, ultrafrente,ultratras)
                            if ultraesquerda <= 150 and ultradireita >= 150:
                                #parede a esquerda
                                tanki.stop()
                                print("parede esquerda")
                                entradaR= str("parede esquerda")
                                break
                            elif ultraesquerda >= 150 and ultradireita <= 150:
                                #parede a direita
                                tanki.stop()
                                print("parede direita")
                                entradaR= str("parede direita")
                                break
                            elif ultradireita > 100 :
                                if  ultraesquerda > 100 :
                                    #estar em algum meio
                                    tanki.stop()
                                    print("parede meeeio")
                                    entradaR= str("parede meeeio")
                                    break
                            wait(100)
                        #iniciar identificação
                        tanki.stop()
                        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
                        while True:
                            retorno1= multiplex1.read(0)
                            ultrafrente= retorno1[3]
                            ultratras= retorno1[2]
                            ultradireita= retorno1[1]
                            ultraesquerda= retorno1[0]
                            # Lê dados da serial
                            data = ser.read_all()
                            cabooou= None
                            tanki.straight(50)
                            tanki.stop()
                            if data:
                                try:
                                    data_str = data.decode('utf-8').strip()
                                    print("Dados recebidos: " + data_str)
                                    
                                    detected = None
                                    confianca = None
                                    lado = None

                                    for line in data_str.split('\n'):
                                        line = line.strip()
                                        if not line:
                                            continue
                                            
                                        if 'Detected:' in line:
                                            detected = line.split(':')[1].strip()
                                        elif 'Confian' in line:
                                            parts = line.split(':')
                                            if len(parts) > 1 and parts[1].strip():
                                                conf_str = parts[1].strip().replace('%', '')
                                                try:
                                                    confianca = round(float(conf_str), 1)  # Arredonda para 1 casa decimal
                                                except ValueError:
                                                    confianca = None
                                                    print("Aviso: Valor de confiança inválido")
                                        elif 'Lado:' in line:
                                            lado = line.split(':')[1].strip()

                                    if detected and confianca is not None and lado:
                                        # Converte para string e remove zeros desnecessários
                                        conf_str = str(confianca).rstrip('0').rstrip('.') if '.' in str(confianca) else str(confianca)
                                        print("Detectado: " + detected + ", Confiança: " + conf_str + "%, Lado: " + lado)
                                        print("ultra",ultrafrente)
                                        if confianca > 90.0 and ultrafrente <= 150 :
                                            if 'Black Ball' in detected:
                                                if lado == 'esquerda':
                                                    ev3.speaker.beep(400)
                                                    vitima = "Black Ball,esquerda"
                                                    lapooo = "esquerda"
                                                    cabooou= 1
                                                elif lado == 'meio':
                                                    ev3.speaker.beep(500)
                                                    vitima = "Black Ball,meio"
                                                    lapooo = "meio"
                                                    cabooou= 1
                                                elif lado == 'direita':
                                                    ev3.speaker.beep(600)
                                                    vitima = "Black Ball,direita"
                                                    lapooo = "direita"
                                                    cabooou= 1
                                            elif 'Silver Ball' in detected:
                                                if lado == 'esquerda':
                                                    ev3.speaker.beep(100)
                                                    vitima = "Silver Ball,esquerda"
                                                    lapooo = "esquerda"
                                                    cabooou= 1
                                                elif lado == 'meio':
                                                    ev3.speaker.beep(200)
                                                    vitima = "Silver Ball,meio"
                                                    lapooo = "meio"
                                                    cabooou= 1
                                                elif lado == 'direita':
                                                    ev3.speaker.beep(300)
                                                    vitima = "Silver Ball,direita"
                                                    lapooo = "direita"
                                                    cabooou= 1
                                            if cabooou != None:
                                                break
                                        

                                except ValueError:
                                    print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                    # Método universal para limpar buffer de entrada
                                    while ser.in_waiting > 0:
                                        ser.read(ser.in_waiting)
                                    continue
                                    
                                except Exception as e:
                                    print("Erro inesperado:", str(e))
                                    while ser.in_waiting > 0:
                                        ser.read(ser.in_waiting)
                                    continue
                                
                            wait(100)
                        #onde a vitima esta
                        
                        while True:
                            retorno1= multiplex1.read(0)
                            ultrafrente= retorno1[3]
                            ultratras= retorno1[2]
                            ultradireita= retorno1[1]
                            ultraesquerda= retorno1[0]
                            tanki.settings(straight_speed=99, straight_acceleration=999, turn_rate=99, turn_acceleration=999)
                            if vitima and lapooo != None:
                                ev3.speaker.beep()
                                if lapooo == ("esquerda"):
                                    print("esquerda")
                                    ultimacoisa= ultrafrente
                                    break
                                elif lapooo == ("meio"):
                                    print("meio")
                                    tanki.straight(0)
                                    tanki.stop()
                                    motorB.run(300)
                                    motorC.run(-300)
                                    ev3.speaker.beep(500,500)
                                    if ultrafrente < 100:
                                        tanki.stop()
                                        ultimacoisa= ultrafrente
                                        break
                                    elif ultrafrente > 100:
                                        tanki.turn(50)
                                        tanki.stop()
                                elif lapooo == ("direita"):
                                    print("direita")
                                    ultimacoisa= ultrafrente
                                    break
                            wait(100)
                            print(ultrafrente)
                            ultimacoisa= ultrafrente
                        #verifica novamente
                        ev3.speaker.beep()  
                        if ultimacoisa < 150:
                            tanki.turn(-50)
                            tanki.stop()
                        ev3.speaker.beep(50,1000)
                        wait(99999999)
                        while True:
                            # Lê dados da serial
                            # looping serial2
                            data = ser.read_all()
                            if data:
                                try:
                                    data_str = data.decode('utf-8').strip()
                                    print("Dados recebidos: " + data_str)
                                    
                                    detected = None
                                    confianca = None
                                    lado = None

                                    for line in data_str.split('\n'):
                                        line = line.strip()
                                        if not line:
                                            continue
                                            
                                        if 'Detected:' in line:
                                            detected = line.split(':')[1].strip()
                                        elif 'Confian' in line:
                                            parts = line.split(':')
                                            if len(parts) > 1 and parts[1].strip():
                                                conf_str = parts[1].strip().replace('%', '')
                                                try:
                                                    confianca = round(float(conf_str), 1)  # Arredonda para 1 casa decimal
                                                except ValueError:
                                                    confianca = None
                                                    print("Aviso: Valor de confiança inválido")
                                        elif 'Lado:' in line:
                                            lado = line.split(':')[1].strip()

                                    if detected and confianca is not None and lado:
                                        # Converte para string e remove zeros desnecessários
                                        conf_str = str(confianca).rstrip('0').rstrip('.') if '.' in str(confianca) else str(confianca)
                                        print("Detectado: " + detected + ", Confiança: " + conf_str + "%, Lado: " + lado)
                                        
                                        if confianca > 90.0:
                                            if 'Black Ball' in detected:
                                                if lado == 'esquerda':
                                                    ev3.speaker.beep(400)
                                                    vitima = "Black Ball,esquerda"
                                                    lapooo = "esquerda"
                                                    break
                                                elif lado == 'meio':
                                                    ev3.speaker.beep(500)
                                                    vitima = "Black Ball,meio"
                                                    lapooo = "meio"
                                                    break
                                                elif lado == 'direita':
                                                    ev3.speaker.beep(600)
                                                    vitima = "Black Ball,direita"
                                                    lapooo = "direita"
                                                    break
                                            elif 'Silver Ball' in detected:
                                                if lado == 'esquerda':
                                                    ev3.speaker.beep(100)
                                                    vitima = "Silver Ball,esquerda"
                                                    lapooo = "esquerda"
                                                    break
                                                elif lado == 'meio':
                                                    ev3.speaker.beep(200)
                                                    vitima = "Silver Ball,meio"
                                                    lapooo = "meio"
                                                    break
                                                elif lado == 'direita':
                                                    ev3.speaker.beep(300)
                                                    vitima = "Silver Ball,direita"
                                                    lapooo = "direita"
                                                    break
                                
                                except UnicodeDecodeError:
                                    print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                    ser.flushInput()  # Limpa o buffer de entrada
                                    continue
                                    
                                except Exception as e:
                                    print("Erro inesperado: " + e)
                                    ser.flushInput()
                                    continue
                                    
                            wait(100)
                        while True:
                            print(vitima)
                            wait(100)
                        wait(999999)
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
        alvo= 11
        # Verifica se viu verde
        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        
        if 0==0:
            if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo):
                wait(30)
                if verdeDireita:
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    motorB.run(500)
                    motorC.run(500)
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
                        tanki.straight(550)
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
                        tanki.turn(-50)
                        tanki.stop()
                        wait(20)
                        tanki.stop()
                    else:
                        if cloresq == 1 or clordir == 1: # curva verde
                            if meio1 > 50 or meio2 > 50:
                                ev3.speaker.beep(600,100)
                                tanki.turn(100)
                                tanki.straight(170)
                                tanki.stop()
                        elif verdeDireita:
                            wait(30)
                            if verdeEsquerda: # 2verdes
                                tanki.turn(100)
                                tanki.straight(550)
                                tanki.stop()
                                motorB.run(999)
                                motorC.run(999)
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
                                tanki.turn(-50)
                                tanki.stop()
                                wait(20)
                                tanki.stop()

#############################################################################################################################################################################################
            if H2 >=(90-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo):
                wait(30)
                if verdeEsquerda:
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    motorB.run(-500)
                    motorC.run(-500)
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
                        tanki.straight(550)
                        tanki.stop()
                        motorB.run(999)
                        motorC.run(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 60:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        tanki.turn(-50)
                        tanki.stop()
                        wait(20)
                        tanki.stop()
                    else:
                        if cloresq == 1 or clordir == 1: # curva verde
                            if meio1 > 50 or meio2 > 50:
                                ev3.speaker.beep(600,100)
                                tanki.turn(100)
                                tanki.straight(-170)
                                tanki.stop()
                        elif verdeEsquerda:
                            wait(30)
                            if verdeDireita: # 2verdes
                                tanki.turn(100)
                                tanki.straight(550)
                                tanki.stop()
                                motorB.run(999)
                                motorC.run(999)
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
                                tanki.turn(-50)
                                tanki.stop()
                                wait(20)
                                tanki.stop()

######################################################################################################################################################################################################
            if H3 >=(90-alvo) and H3 <=(110+alvo) and S3 >=(50-alvo) and S3 <=(70+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo):
                wait(45)
                if verdeMeio:      
                    ev3.speaker.beep(600,100)
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
                ev3.speaker.beep(600,100)
                pretodir = 0
                pretoesq = 0
                contGap = 0
                tanki.stop()
                print("gaap")
                motorB.run(-400)
                motorC.run(400)
                while True:
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    if pretodir !=0  or pretoesq != 0:
                        break

                    if meio1 >= 90 and meio2 >= 90:
                        contGap = contGap + 1
                        print(contGap)

                    if contGap > 200 or meio1 < 40 or meio2 < 40:
                        print("linha do gap")
                        break
                tanki.stop()
                # verifica curva s/n s:para n:gaap
                if meio1 > 90 or meio2 > 90:
                    if fora1 > 90 and fora2 > 90:
                        #n:gaap
                        motorB.reset_angle(0)
                        motorB.run(400)
                        motorC.run(-400)
                        wait(150) #ajeitar
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            if meio1 < 40 or meio2 < 40 or motorB.angle() > 400:
                                tanki.stop()
                                break
                        tanki.stop()
                        if meio1 < 40 or meio2 < 40 or posicao == 0:
                            #gap feito
                            ev3.speaker.beep(600,100)
                            tanki.turn(40)
                            tanki.stop()
                        else:
                            #nao feito
                            tanki.straight(250)
                            tanki.stop()
                            if fora1 < 40 or meio1 < 40 or meio2 < 40 or fora2 < 40:
                                #linha direita
                                tanki.turn(100)
                                tanki.stop()
                            tanki.straight(-250)
                            tanki.stop()
                            if fora1 < 40 or meio1 < 40 or meio2 < 40 or fora2 < 40:
                                #linha reta
                                tanki.turn(100)
                                tanki.stop()
                            tanki.straight(-250)
                            tanki.stop()
                            if fora1 < 40 or meio1 < 40 or meio2 < 40 or fora2 < 40:
                                #linha esquerda
                                tanki.turn(100)
                                tanki.stop()
                            tanki.straight(250)
                            tanki.stop()
                            ev3.speaker.beep(600,100)
                            motorB.run(-400)
                            motorC.run(400)
                            while True:
                                retorno = sensor1.read(2)
                                fora1 = retorno[0]
                                meio1 = retorno[1]
                                meio2 = retorno[2]
                                fora2 = retorno[3]
                                if meio1 < 40 or meio2 < 40:
                                    tanki.stop()
                                    break
                            tanki.stop()
                            if meio1 < 40:
                                tanki.straight(-50)
                                tanki.stop()
                            elif meio2 < 40:
                                tanki.straight(50)
                                tanki.stop()
                else:
                    #s:para
                    tanki.turn(100)
                    tanki.stop()
                    ev3.speaker.beep(600,100)
                
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
    
        kp = 12.8
        kd = -14
        ki = 0.001  
        base = ((85) * 10)

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
