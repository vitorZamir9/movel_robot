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
from servos import Servos
import sys

####################################################################################################
ev3= EV3Brick()

guinadaAA= LUMPDevice(Port.S4)
Anguly=LUMPDevice(Port.S3)
sensor1 = LUMPDevice(Port.S1)
multiplex1 = LUMPDevice(Port.S2)
motorB = Motor(Port.B,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=1)
serialservo = UARTDevice(Port.S5, baudrate=115200, timeout=0.1)
servosP= Servos(serialservo,True)

#VARIAVEIS/IMPORT
kp = 5
kd = 13
casa = 0
error = 0
powerB = 0
powerC = 0
corr = 0
old_error = 0
pretoesq = 0
pretodir = 0
integral = 0
derivative = 0
contE = 0
contD = 0
forsado = 0
contGap=0
ultimacoisa=0
vitimas=0
vitimaSILVER = 0
vitimaBLACK = 0
vendoTRIANGULO=0
vendoTRIANGULOVERDE=0
vendoTRIANGULOVERMELHO=0
prafrente=0
semvitima=0
chegarnavitima=None
sairdoRESGATE=None
pxvitima=None
parado = 0
javiuantes = None
agora = None
tanki = DriveBase(motorB, motorC, wheel_diameter= 65.0 , axle_track=129.0)
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
####initi####
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

def botao():
    global multiplex1
    while True:
        retorno1 = multiplex1.read(0)
        botao_stop = retorno1[6]
        if botao_stop > 0:
            print("parado")
            motorB.stop()
            motorC.stop()
        

def sensor():
    global old_error  
    global sensor1  
    global pretodir
    global pretoesq
    global timete
    global guinadaAA
    global Anguly
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
    global guinada
    global afagem
    global verdeDireita
    global verdeEsquerda
    global verdeMeio
    global ultrafrente
    global ultradireita
    global ultraesquerda
    global kp
    global kd
    global casa
    global powerB
    global powerC
    global forsado
    global contGap
    global agora
    global vendoVITIMA 
    global vitima
    global detected
    global vitimas
    global vitimaSILVER
    global vitimaBLACK
    global vendoTRIANGULO
    global vendoTRIANGULOVERDE
    global vendoTRIANGULOVERMELHO
    global parado
    global prafrente
    global lado
    global javiuantes
    global pxvitima
    global chegarnavitima
    global semvitima
    global sairdoRESGATE
    while True:
        #teste rasp/teste agluma coisa
        Anguly.read(4)
        guinadaAA.read(4)
        wait(100)
        Anguly.read(0)
        guinadaAA.read(0)
        wait(100)
        ev3.speaker.beep()
        #servooooooooooooooooooos
        servosP.desativa(1)
        servosP.desativa(3)
        servosP.desativa(4)
        servosP.desativa(5)
        wait(500)
        servosP.move(5,40)
        servosP.move(1,5)
        wait(100)
        break

    while True:
        ev3.screen.clear()
        ev3.screen.print("-7")
        ser.write(b'OFF\r\n')
        y=0
        retorno1= multiplex1.read(0)
        ultrafrente= retorno1[2]
        ultradireita= retorno1[3]
        ultraesquerda= retorno1[0]
        botao_stop=retorno1[6]
        botao_parar= retorno1[5]
        ChoqueESQ= retorno1[4]
        ChoqueDIR= retorno1[7]
        retorno = sensor1.read(2)
        fora1 = retorno[0]#esquerda REAL>>>direita
        meio1 = retorno[1]#esquerda REAL>>>direita
        meio2 = retorno[2]#direita  REAL>>>esquerda
        fora2 = retorno[3]#direita  REAL>>>esquerda
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
        contGap = 1
        afagem=Anguly.read(6)[0]
        guinada=guinadaAA.read(0)[0]
        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

################################################################################################################
        # Verifica se identificou uma rampa
        #print(afagem)
        if afagem >= 5:  # ajustar de acordo com o sensor 
            print("Rampa detectada!")
            kd = 2.5
            kp = 7.5
        if afagem <= -5:
            casa = 10
        if afagem > -1 and casa == 10:
            casa = 0
            print("pegou")
            motorB.run(-100)
            motorC.run(100)
            wait(50)
            tanki.stop()
        else:
            kd = 14
            kp = 5.5
            #seguidor valor
################################################################################################################
        #verificar se o robo ta parado ou forçando
################################################################################################################
        # Verifica se viu vermelho
        retorno = sensor1.read(2)
        red_tape1 = retorno[17]
        red_tape2 = retorno[18]
        red_tape3 = retorno[19]
        if red_tape1 ==2 and red_tape2 ==2 and red_tape3 ==2:
            ev3.speaker.beep(1200)
            motorB.stop()
            motorC.stop()
            break
            
################################################################################################################
        # Verifica se viu prata
        clear = 35
        rgb=85
        esqgray = R1 > rgb and G1 > rgb and B1 > rgb and C1 > clear 
        mindgray = R3 > rgb and G3 > rgb and B3 > rgb and C3 > clear #prata reflectivo
        dirgray = R2 > rgb and G2 > rgb and B2 > rgb and C2 > clear 
        
        esqgray1 = B1 > 50 and B1 < 66 and C1 > 24 and C1 < 31 and cloresq == 6
        mindgray1 = B3 > 50 and B3 < 66 and C3 > 24 and C3 < 31 and clormind == 6 #calibrar o prata não reflectivo
        dirgray1 = B2 > 50 and B2 < 66 and C2> 24 and C2 < 31 and clordir == 6
        #problema pra identificar pratan reflectivo
        if esqgray and mindgray and dirgray or y==0 :
            wait(10)
            if esqgray and mindgray and dirgray and y==0 :
                tanki.stop()
                ev3.speaker.beep(900)
                tanki.turn(-70)
                ev3.speaker.beep(900,600)
                ev3.speaker.beep()
                tanki.stop()
                ser.write(b'Resgate_ON\r\n')
                wait(500)
                if esqgray and mindgray and dirgray :
                    wait(10)
                    if esqgray and mindgray and dirgray :
                        tanki.stop()
                        print("resgate on")
                        ev3.speaker.beep()
                        #ir para frente
                        motorB.run(300)
                        motorC.run(-300)
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            if fora1 > 90 and meio1 > 90 and meio2 > 90 and fora2 > 90:
                                tanki.turn(-50)
                                tanki.stop()
                                break
                            wait(100)
                        #recuar para esquerda
                        motorB.run(-300)
                        motorC.run(0)
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            cloresq = retorno[17]
                            clordir = retorno[19]
                            if meio1 < 70 :
                                tanki.stop()
                                break
                            wait(100)
                        tanki.turn(30)
                        tanki.stop()
                        wait(100)
                        print("recuar pra direita")
                        motorB.run(0)
                        motorC.run(300)
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            cloresq = retorno[17]
                            clordir = retorno[19]
                            if meio2 > 30 :
                                tanki.stop()
                                break
                            wait(100)
                        #entrar no resgate
                        count=0
                        tanki.stop()
                        tanki.settings(turn_rate=400, turn_acceleration=999)
                        ev3.speaker.beep(400,1000)
                        ev3.speaker.beep(100)
                        guinada
                        wait(200)
                        tanki.turn(150)
                        tanki.stop()
                        wait(1000)
                        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
                        ev3.speaker.beep() 
                        #saber onde entrou no resgate
                        #iniciar identificação
                        tanki.stop()
                        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
                        ev3.speaker.beep() 
                        #saber onde entrou no resgate#####################################################################################################################################
                        while True:
                            retorno1= multiplex1.read(0)
                            ultrafrente= retorno1[2]
                            ultradireita= retorno1[3]
                            ultraesquerda= retorno1[0]
                            print(ultradireita,ultraesquerda, ultrafrente)
                            if ultraesquerda <= 150 and ultradireita >= 150:
                                #parede a esquerda
                                tanki.stop()
                                print("parede esquerda")
                                entradaR= str("parede esquerda")
                                tanki.straight(10)
                                tanki.stop()
                                break
                            elif ultraesquerda >= 150 and ultradireita <= 150:
                                #parede a direita
                                tanki.stop()
                                print("parede direita")
                                entradaR= str("parede direita")
                                tanki.straight(-10)
                                tanki.stop()
                                break
                            elif ultradireita > 100 :
                                if  ultraesquerda > 100 :
                                    #estar em algum meio
                                    tanki.stop()
                                    print("parede meeeio")
                                    entradaR= str("parede meeeio")
                                    break
                        wait(1000)
                        #iniciar identificação0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
                        tanki.stop()
                        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)
                        #fazerum loop aqui para so sair quando pegar todas as vitimas(3 vitimas no total)
                        vitimas=0
                        vitimaBLACK=0
                        vitimaSILVER=0
                        semvitima=0
                        chegarnavitima=None
                        pxvitima=None
                        sairdoRESGATE=None
                        while True:#so sai quando pegar 3 vitimaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaas
                            print("quantas vitimas_inicio: ", vitimas ,"Black Ball: ", vitimaBLACK,"Silver Ball: ", vitimaSILVER)
                            if vitimas >= 3 and vitimaBLACK >= 1 and vitimaSILVER >= 2:
                                print("identificar os triangulos")
                                tanki.stop()
                                sairdoRESGATE=0
                                break
                            wait(500)
                            ser.write(b'Resgate_ON\r\n')
                            ser.clear()#apagar mensagens antigas
                            while True :#loop de chegar mais perto da vitima
                                while True:
                                    retorno1= multiplex1.read(0)
                                    ultrafrente= retorno1[2]
                                    ultradireita= retorno1[3]
                                    ultraesquerda= retorno1[0]
                                    ser.write(b'Resgate_ON\r\n')
                                    # Lê dados da serial
                                    data = ser.read_all()
                                    cabooou = None
                                    vitima = None
                                    lapooo = None
                                    vendoVITIMA = None
                                    javiuantes=None
                                    pxvitima=None
                                    if data:
                                        try:
                                            data_str = data.decode('utf-8').strip()
                                            detected = None
                                            confianca = None
                                            lado = None
                                            area = None  # <-- nova variável
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
                                                            confianca = round(float(conf_str), 1)
                                                        except ValueError:
                                                            confianca = None
                                                            print("Aviso: Valor de confiança inválido")
                                                elif 'Lado:' in line:
                                                    lado = line.split(':')[1].strip()
                                                elif 'Area:' in line:  # <-- captura área
                                                    parts = line.split(':')
                                                    if len(parts) > 1 and parts[1].strip():
                                                        area_str = parts[1].strip().replace('px', '').strip()
                                                        try:
                                                            area = int(area_str)
                                                        except ValueError:
                                                            area = None
                                                            print("Aviso: Valor de área inválido")
                                            # só exibe se tiver tudo
                                            if detected and confianca is not None and lado and area is not None:
                                                conf_str = str(confianca).rstrip('0').rstrip('.') if '.' in str(confianca) else str(confianca)
                                                print("ALINHAR_COM_VITIMA: " + detected + ", Confiança: " + conf_str + "%, Lado: " + lado + ", Área: " + str(area) + " px")
                                                if confianca > 80.0 :
                                                    if 'Black Ball' in detected:
                                                        if lado == 'meio':
                                                            ev3.speaker.beep(500)
                                                            vitima = "Black Ball,meio"
                                                            lapooo = "meio"
                                                            vendoVITIMA="Black Ball"
                                                            cabooou= 1
                                                            chegarnavitima
                                                            javiuantes="meio"
                                                            pxvitima=area
                                                        elif lado == 'esquerda':
                                                            ev3.speaker.beep(400)
                                                            vitima = "Black Ball,esquerda"
                                                            lapooo = "esquerda"
                                                            vendoVITIMA="Black Ball"
                                                            cabooou= 1
                                                            pxvitima=area
                                                        elif lado == 'direita':
                                                            ev3.speaker.beep(600)
                                                            vitima = "Black Ball,direita"
                                                            lapooo = "direita"
                                                            vendoVITIMA="Black Ball"
                                                            cabooou= 1
                                                            pxvitima=area
                                                    elif 'Silver Ball' in detected:
                                                        if lado == 'meio':
                                                            ev3.speaker.beep(200)
                                                            vitima = "Silver Ball,meio"
                                                            lapooo = "meio"
                                                            vendoVITIMA="Silver Ball"
                                                            cabooou= 1
                                                            javiuantes="meio"
                                                            pxvitima=area
                                                        elif lado == 'esquerda':
                                                            ev3.speaker.beep(100)
                                                            vitima = "Silver Ball,esquerda"
                                                            lapooo = "esquerda"
                                                            vendoVITIMA="Silver Ball"
                                                            cabooou= 1
                                                            pxvitima=area
                                                        elif lado == 'direita':
                                                            ev3.speaker.beep(300)
                                                            vitima = "Silver Ball,direita"
                                                            lapooo = "direita"
                                                            vendoVITIMA="Silver Ball"
                                                            cabooou= 1
                                                            pxvitima=area
                                                    if cabooou != None:
                                                        break
                                        except ValueError:
                                            print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                            ser.flushInput()
                                            continue
                                        except Exception as e:
                                            print("Erro inesperado:", e)
                                            ser.flushInput()
                                            continue
                                    else:
                                        wait(200)
                                        motorB.reset_angle(0)
                                        motorC.reset_angle(0)
                                        wait(100)
                                        motorB.dc(100)
                                        motorC.dc(100)
                                        while True:
                                            wait(50)
                                            print(motorB.angle(),motorC.angle(),semvitima)
                                            if motorB.angle() >= 45:
                                                tanki.stop()
                                                semvitima = semvitima + 1
                                                break
                                        tanki.stop()
                                        if semvitima >= 150 :
                                            print("não tem vitima")
                                            vitimas=10
                                            vitimaBLACK=10
                                            vitimaSILVER=10
                                            sairdoRESGATE=1
                                            break
                                        wait(300)
                                #onde a vitima estaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                                if semvitima >= 150 :
                                    print("não tem vitimaaaaaaaaaaaaa")
                                    vitimas=10
                                    vitimaBLACK=10
                                    vitimaSILVER=10
                                    sairdoRESGATE=1
                                    break
                                tanki.stop()
                                wait(1000)
                                #verifica novamente
                                ev3.speaker.beep()  
                                #################################################ALINHAR COM O MEIO DA CAMERA
                                tanki.stop()
                                wait(100)
                                ser.clear()
                                tanki.settings(straight_speed=999999, straight_acceleration=9999999, turn_rate=9999999, turn_acceleration=99999999)
                                wait(500)
                                print("alin@@@@@ar")
                                tanki.stop()
                                tanki.stop()
                                ev3.speaker.beep()
                                while True:
                                    data = ser.read_all()
                                    if data:
                                        try:
                                            data_str = data.decode('utf-8').strip()
                                            detected = None
                                            confianca = None
                                            lado = None
                                            area = None  
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
                                                            confianca = round(float(conf_str), 1)
                                                        except ValueError:
                                                            confianca = None
                                                            print("Aviso: Valor de confiança inválido")
                                                elif 'Lado:' in line:
                                                    lado = line.split(':')[1].strip()
                                                elif 'Area:' in line:  
                                                    parts = line.split(':')
                                                    if len(parts) > 1 and parts[1].strip():
                                                        area_str = parts[1].strip().replace('px', '').strip()
                                                        try:
                                                            area = int(area_str)
                                                        except ValueError:
                                                            area = None
                                                            print("Aviso: Valor de área inválido")
                                            # Só segue se tiver todos os dados
                                            if detected and confianca is not None and lado and area is not None:
                                                conf_str = str(confianca).rstrip('0').rstrip('.') if '.' in str(confianca) else str(confianca)
                                                print("ALINHAR_COM_VITIMA: " + detected + ", Confiança: " + conf_str + "%, Lado: " + lado + ", Área: " + str(area) + " px")
                                                if javiuantes == "meio":
                                                    break
                                                if confianca > 80.0 and detected == vendoVITIMA:
                                                    # Loop de alinhamento até lado == "meio"
                                                    while lado != "meio":
                                                        # Atualiza leitura serial dentro do loop
                                                        data = ser.read_all()
                                                        if data:
                                                            try:
                                                                data_str = data.decode('utf-8').strip()
                                                                for line in data_str.split('\n'):
                                                                    line = line.strip()
                                                                    if not line:
                                                                        continue
                                                                    if 'Lado:' in line:
                                                                        lado = line.split(':')[1].strip()
                                                            except:
                                                                pass
                                                        if lapooo == "esquerda":
                                                            print("Girando para esquerda...")
                                                            motorB.dc(-75)
                                                            motorC.dc(-75)
                                                        elif lapooo == "direita":
                                                            print("Girando para direita...")
                                                            motorB.dc(75)
                                                            motorC.dc(75)
                                                        wait(50)
                                                        motorB.stop()
                                                        motorC.stop()
                                                    # Chegou no meio
                                                    print("Alinhado com a vítima!")
                                                    tanki.stop()
                                                    ev3.speaker.beep(800)
                                                    break  # sai do while True principal
                                        except ValueError:
                                            print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                            ser.flushInput()
                                            continue
                                        except Exception as e:
                                            print("Erro inesperado:", e)
                                            ser.flushInput()
                                            continue
                                    else:
                                        # Caso não tenha detecção
                                        wait(300)
                                        print(motorB.angle(), motorC.angle(), tanki.state()[3], "parado: ", parado)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0 
                                        if parado > 10:            
                                            print("não está conseguindo ver vítima ou algo do tipo")
                                            motorB.dc(-40)
                                            motorC.dc(40)
                                        wait(300)
                                        if lapooo == "esquerda":
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            wait(100)
                                            motorB.dc(-85)
                                            motorC.dc(-85)
                                            while True:
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),"parado: ",parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() <= -60 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            tanki.stop()
                                            tanki.stop()
                                        wait(300)
                                        if lapooo == "direita":
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            wait(100)
                                            motorB.dc(85)
                                            motorC.dc(85)
                                            while True:
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),"parado: ",parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() >= 60 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            tanki.stop()
                                            tanki.stop()
                                        ###########################################################################################################################
                                        ###########################################################################################################################
                                #sai do loop de se alinha com a vitima!^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 
                                motorB.stop()
                                motorC.stop()
                                motorB.stop()
                                motorC.stop()
                                tanki.stop()
                                #ver se a vitima esta longe:
                                prafrente=0
                                if pxvitima < 2500:
                                    prafrente = 200
                                elif pxvitima >2500:
                                    prafrente = 10
                                ################################################################################################################################
                                wait(100)
                                tanki.stop()
                                motorB.reset_angle(0)
                                motorC.reset_angle(0)
                                wait(100)
                                motorB.dc(60)
                                motorC.dc(-60)
                                parado=0
                                while True:
                                    wait(100)
                                    print(motorB.angle(),motorC.angle(),tanki.state()[3],"parado: ",parado)
                                    if tanki.state()[3] < 20:
                                        parado = parado + 1
                                    if tanki.state()[3] > 60:
                                        parado = 0
                                    if motorB.angle() >= prafrente or parado > 20:
                                        tanki.stop()
                                        break
                                tanki.stop()
                                wait(500)
                                if pxvitima >2500:#sai do loop de se alinhar e chegar perto da vitima
                                    tanki.stop()
                                    break
                            #######################################sair do loop chegar na vitima
                            if semvitima >= 150 :
                                print("não tem vitimaaaaaaaaaaaaa")
                                vitimas=10
                                vitimaBLACK=10
                                vitimaSILVER=10
                                sairdoRESGATE=1
                                break#aqui ele sai blz?
                            tanki.turn(-50)
                            tanki.stop()
                            servosP.desativa(1)
                            servosP.desativa(3)
                            servosP.desativa(4)
                            servosP.desativa(5)
                            if  vitima == "Black Ball,esquerda" :
                                print("1")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            elif vitima == "Black Ball,meio" :
                                print("2")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            elif vitima == "Black Ball,direita" :
                                print("3")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            elif vitima == "Silver Ball,esquerda" :
                                print("4")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            elif vitima == "Silver Ball,meio":
                                print("5")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            elif vitima == "Silver Ball,direita":
                                print("6")
                                servosP.move(1,250)
                                servosP.move(3,90)
                                servosP.move(4,0)
                            wait(1000)
                            #andar um pouco pra pegar a vitima
                            motorB.reset_angle(0)
                            motorC.reset_angle(0)
                            wait(100)
                            motorB.dc(60)
                            motorC.dc(-60)
                            parado=0
                            while True:
                                wait(100)
                                print(motorB.angle(),motorC.angle(),tanki.state()[3],"parado: ",parado)
                                if tanki.state()[3] < 20:
                                    parado = parado + 1
                                if tanki.state()[3] > 60:
                                    parado = 0
                                if motorB.angle() >= 200 or parado > 20:
                                    tanki.stop()
                                    break
                            tanki.stop()
                            #em baixo ele separa 
                            servosP.desativa(1)
                            servosP.desativa(3)
                            servosP.desativa(4)
                            servosP.desativa(5)
                            servosP.move(3,0)
                            servosP.move(4,90)
                            wait(100)
                            servosP.move(5,40)
                            servosP.move(1,5)
                            wait(500)
                            tanki.turn(-80)
                            tanki.stop()
                            #################################################################SEPARAR
                            if  vendoVITIMA == "Black Ball" :
                                servosP.desativa(1)
                                servosP.desativa(3)
                                servosP.desativa(4)
                                servosP.desativa(5)
                                wait(500)
                                servosP.move(5,40)
                                servosP.move(3,0)
                                servosP.move(4,90)
                                wait(1000)
                                servosP.move(1,5)
                                wait(1000)
                                servosP.move(3,90)
                                servosP.move(4,65)
                                wait(1000)
                                servosP.desativa(1)
                                servosP.desativa(3)
                                servosP.desativa(4)
                                servosP.desativa(5)
                                wait(100)
                                servosP.move(1,10)
                                wait(100)
                                servosP.move(1,0)
                                wait(1000)
                                servosP.move(1,5)
                                servosP.move(3,90)
                                servosP.move(4,0)
                                wait(100)
                                servosP.move(1,0)
                                wait(500)
                                #adicionar a variavel
                                vitimaBLACK = vitimaBLACK + 1
                                vitimas = vitimas + 1
                            elif vendoVITIMA == "Silver Ball" :
                                servosP.desativa(1)
                                servosP.desativa(3)
                                servosP.desativa(4)
                                servosP.desativa(5)
                                wait(500)
                                servosP.move(5,40)
                                servosP.move(3,0)
                                servosP.move(4,90)
                                wait(1000)
                                servosP.move(1,5)
                                wait(1000)
                                servosP.move(4,0)
                                servosP.move(3,10)
                                wait(1000)
                                servosP.desativa(1)
                                servosP.desativa(3)
                                servosP.desativa(4)
                                servosP.desativa(5)
                                wait(100)
                                servosP.move(1,10)
                                wait(100)
                                servosP.move(1,0)
                                wait(1000)
                                servosP.move(1,10)
                                servosP.move(3,90)
                                servosP.move(4,0)
                                wait(100)
                                servosP.move(1,0)
                                wait(500)
                                #adicionar a variavel
                                vitimaSILVER = vitimaSILVER + 1
                                vitimas = vitimas + 1
                            #verificar se pegou as vitimas realmente
                            #tem que fazer
                            print("quantas vitimas_final: ", vitimas ,"Black Ball: ", vitimaBLACK,"Silver Ball: ", vitimaSILVER)
                        #identificar triangulos agora:
                        #AQUI É PRA PERGUNTAR SE É PRA ENTREGAR ALGUMA COISA NOS TRIANGULOS OU SE É PRA VAZAR DO RESGATE
                        #
                        #
                        ##########################################################################################################################################################################################33
                        vendoTRIANGULO = 0
                        vendoTRIANGULOVERDE=0
                        vendoTRIANGULOVERMELHO=0
                        vendoTRIANGULOcor = None
                        if sairdoRESGATE == 0 : #entregar nos triangulos
                            while True:
                                print("triangulos_inicial: ","verde: ", vendoTRIANGULOVERDE, "vermelho: ", vendoTRIANGULOVERMELHO)
                                if vendoTRIANGULO >= 2 and vendoTRIANGULOVERDE >= 1 and vendoTRIANGULOVERMELHO >= 1:
                                    tanki.stop()
                                    ev3.speaker.beep(900,10000)
                                    print("procurar saida")
                                    sairdoRESGATE=1
                                    break
                                tanki.stop()
                                wait(100)
                                ser.clear()
                                wait(500)   
                                while True:
                                    data = ser.read_all()
                                    if data:
                                        try:
                                            data_str = data.decode('utf-8').strip()
                                            retangulo = None
                                            lado = None
                                            for line in data_str.split('\n'):
                                                line = line.strip()
                                                if not line:
                                                    continue
                                                if 'Retangulo' in line:
                                                    retangulo = line
                                                if 'Lado:' in line:
                                                    lado = line.split(':')[1].strip()
                                            if retangulo:
                                                print("Alinhando com o triângulo. Lado atual:", lado)
                                                # Loop para alinhar até ficar no meio
                                                while lado != "meio":
                                                    # Atualiza a leitura da serial a cada volta
                                                    data = ser.read_all()
                                                    if data:
                                                        data_str = data.decode('utf-8').strip()
                                                        for line in data_str.split('\n'):
                                                            line = line.strip()
                                                            if not line:
                                                                continue
                                                            if 'Lado:' in line:
                                                                lado = line.split(':')[1].strip()
                                                    # Comando de giro baseado no lado atual
                                                    if lado == "esquerda":
                                                        motorB.dc(-900)
                                                        motorC.dc(-900)
                                                    elif lado == "direita":
                                                        motorB.dc(900)
                                                        motorC.dc(900)
                                                    wait(50)
                                                    motorB.stop()
                                                    motorC.stop()
                                                # Quando chega no meio
                                                ev3.speaker.beep(400)
                                                if "Vermelho" in retangulo:
                                                    vendoTRIANGULOcor = "vermelho"
                                                    vendoTRIANGULO += 1
                                                    vendoTRIANGULOVERMELHO += 1
                                                elif "Verde" in retangulo:
                                                    vendoTRIANGULOcor = "verde"
                                                    vendoTRIANGULO += 1
                                                    vendoTRIANGULOVERDE += 1
                                                tanki.stop()
                                                break  # Sai do while True principal
                                        except ValueError:
                                            print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                            ser.flushInput()
                                            continue
                                        except Exception as e:
                                            print("Erro inesperado:", e)
                                            ser.flushInput()
                                            continue
                                    else:
                                        print("Não vendo triângulo")
                                        wait(250)
                                        motorB.reset_angle(0)
                                        motorC.reset_angle(0)
                                        wait(100)
                                        motorB.dc(100)
                                        motorC.dc(100)
                                        while True:
                                            wait(100)
                                            if motorB.angle() >= 30:
                                                tanki.stop()
                                                break
                                        tanki.stop()
                                        wait(300)
                                #ir até o triangulo
                                tanki.stop()
                                wait(100)
                                retorno1= multiplex1.read(0)
                                ChoqueESQ= retorno1[4]
                                ChoqueDIR= retorno1[7]
                                if vendoTRIANGULO >=1:
                                    print("ir pro triangulo")
                                    tanki.stop()
                                    motorB.reset_angle(0)
                                    motorC.reset_angle(0)
                                    wait(100)
                                    motorB.dc(100)
                                    motorC.dc(-100)
                                    parado=0
                                    while True:
                                        retorno1= multiplex1.read(0)
                                        ChoqueESQ= retorno1[4]
                                        ChoqueDIR= retorno1[7]
                                        wait(100)
                                        print(motorB.angle(),motorC.angle(),tanki.state()[3],"parado: ",parado,ChoqueESQ,ChoqueDIR)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0
                                        if parado > 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                                            tanki.stop()
                                            break
                                    tanki.stop()
                                    tanki.turn(-150)
                                    tanki.stop()
                                    #conferir se é triangulo mesmo:
                                    while True:
                                        data = ser.read_all()
                                        if data:
                                            try:
                                                data_str = data.decode('utf-8').strip()
                                                retangulo = None
                                                lado = None
                                                for line in data_str.split('\n'):
                                                    line = line.strip()
                                                    if not line:
                                                        continue
                                                    if 'Retangulo' in line:
                                                        retangulo = line
                                                    if 'Lado:' in line:
                                                        lado = line.split(':')[1].strip()
                                                if retangulo:
                                                    print("Alinhando com o triângulo. Lado atual:", lado)
                                                    # Loop para alinhar até ficar no meio
                                                    while lado != "meio":
                                                        # Atualiza a leitura da serial a cada volta
                                                        data = ser.read_all()
                                                        if data:
                                                            data_str = data.decode('utf-8').strip()
                                                            for line in data_str.split('\n'):
                                                                line = line.strip()
                                                                if not line:
                                                                    continue
                                                                if 'Lado:' in line:
                                                                    lado = line.split(':')[1].strip()
                                                        # Comando de giro baseado no lado atual
                                                        if lado == "esquerda":
                                                            motorB.dc(-900)
                                                            motorC.dc(-900)
                                                        elif lado == "direita":
                                                            motorB.dc(900)
                                                            motorC.dc(900)
                                                        wait(50)
                                                        motorB.stop()
                                                        motorC.stop()
                                                    # Quando chega no meio
                                                    ev3.speaker.beep(400)
                                                    if "Vermelho" in retangulo:
                                                        vendoTRIANGULOcor = "vermelho"
                                                        vendoTRIANGULO += 1
                                                        vendoTRIANGULOVERMELHO += 1
                                                    elif "Verde" in retangulo:
                                                        vendoTRIANGULOcor = "verde"
                                                        vendoTRIANGULO += 1
                                                        vendoTRIANGULOVERDE += 1
                                                    tanki.stop()
                                                    break  # Sai do while True principal
                                            except ValueError:
                                                print("Aviso: Dados recebidos não são UTF-8 válido. Ignorando...")
                                                ser.flushInput()
                                                continue
                                            except Exception as e:
                                                print("Erro inesperado:", e)
                                                ser.flushInput()
                                                continue
                                        else:
                                            print("Não vendo triângulo")
                                            wait(250)
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            wait(100)
                                            motorB.dc(100)
                                            motorC.dc(100)
                                            while True:
                                                wait(100)
                                                if motorB.angle() >= 30:
                                                    tanki.stop()
                                                    break
                                            tanki.stop()
                                            wait(300)
                                    #########################################################################################
                                    #ir pro triangulo
                                    tanki.stop()
                                    motorB.reset_angle(0)
                                    motorC.reset_angle(0)
                                    wait(100)
                                    motorB.dc(100)
                                    motorC.dc(-100)
                                    parado=0
                                    while True:
                                        retorno1= multiplex1.read(0)
                                        ChoqueESQ= retorno1[4]
                                        ChoqueDIR= retorno1[7]
                                        wait(100)
                                        print(motorB.angle(),motorC.angle(),tanki.state()[3],"parado: ",parado,ChoqueESQ,ChoqueDIR)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0
                                        if parado >= 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                                            tanki.stop()
                                            break
                                    tanki.stop()
                                    tanki.turn(-150)
                                    tanki.stop()
                                    motorB.stop()
                                    motorC.stop()
                                    wait(300)
                                    #########################################################################################################
                                    #MODIFICAR GIRO DO TRIANGULO
                                    guinada=guinadaAA.read(0)[0]
                                    wait(300)
                                    Anguly.read(4)
                                    guinadaAA.read(4)
                                    wait(100)
                                    Anguly.read(0)
                                    guinadaAA.read(0)
                                    wait(1000)
                                    ev3.speaker.beep()
                                    guinada=guinadaAA.read(0)[0]
                                    print(guinada)
                                    motorB.reset_angle(0)
                                    motorC.reset_angle(0)
                                    wait(100)
                                    motorB.dc(100)
                                    motorC.dc(100)
                                    while True: # girarr
                                        guinada=guinadaAA.read(0)[0]
                                        wait(100)
                                        print(motorB.angle(),motorC.angle(),parado,"guinada: ",guinada)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0
                                        if abs(guinada) >= 70 or parado >= 20:
                                            tanki.stop()
                                            break
                                    tanki.stop()
                                    motorB.reset_angle(0)
                                    motorC.reset_angle(0)
                                    wait(100)
                                    motorB.dc(-100)
                                    motorC.dc(100)
                                    print("pra tras")
                                    while True: # ir para tras
                                        wait(50)
                                        print(motorB.angle(),motorC.angle(),parado)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0
                                        if motorB.angle() <= -1000 or parado >= 20:
                                            tanki.stop()
                                            break
                                    motorB.stop()
                                    motorC.stop()
                                    motorB.stop()
                                    motorC.stop()
                                    tanki.stop()
                                    tanki.turn(150)# vai pra frente depois que girou
                                    tanki.stop()
                                    tanki.stop()
                                    motorB.reset_angle(0)
                                    motorC.reset_angle(0)
                                    wait(100)
                                    motorB.dc(-100)
                                    motorC.dc(100)
                                    ev3.speaker.beep()
                                    while True: # ir para tras denovo
                                        wait(50)
                                        print(motorB.angle(),motorC.angle(),parado)
                                        if tanki.state()[3] < 20:
                                            parado = parado + 1
                                        if tanki.state()[3] > 60:
                                            parado = 0
                                        if motorB.angle() <= -1000 or parado > 20:
                                            tanki.stop()
                                            break
                                    tanki.stop()
                                    tanki.stop()
                                    #^^^^^^^^îsso acima é para se gabaritar ao triangulo
                                    print(vendoTRIANGULOcor,vendoTRIANGULOVERDE,vendoTRIANGULOVERMELHO)
                                    wait(1000)
                                    #########################################################################################################################################################################
                                    if vendoTRIANGULOcor == "verde":
                                        tanki.stop()
                                        motorB.reset_angle(0)
                                        motorC.reset_angle(0)
                                        wait(500)
                                        motorB.dc(-100)
                                        motorC.dc(100)
                                        motorB.dc(-100)
                                        motorC.dc(100)
                                        wait(1000)
                                        while True: # ir para tras pra ter certeza que ta no triangulo
                                            wait(50)
                                            print(motorB.angle(),motorC.angle(),"parado: ",parado, "state: ",tanki.state()[3])
                                            if tanki.state()[3] < 20:
                                                parado = parado + 1
                                            if tanki.state()[3] > 60:
                                                parado = 0
                                            if motorB.angle() <= -1000 or parado > 20:
                                                tanki.stop()
                                                break
                                        tanki.stop
                                        servosP.desativa(1)
                                        servosP.desativa(3)
                                        servosP.desativa(4)
                                        servosP.desativa(5)
                                        wait(500)
                                        servosP.move(5,0)# abrir
                                        wait(1000)
                                        for c in range(1,4):
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            servosP.desativa(1)
                                            servosP.desativa(3)
                                            servosP.desativa(4)
                                            servosP.desativa(5)
                                            wait(500)
                                            servosP.move(5,40)#fechar
                                            wait(500)
                                            motorB.dc(100)
                                            motorC.dc(-100)
                                            print("pra frente")
                                            while True:# ir para frente
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() >= 100 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            motorB.stop()
                                            motorC.stop()
                                            motorB.stop()
                                            motorC.stop()
                                            tanki.stop()
                                            wait(100)
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            wait(100)
                                            motorB.dc(-100)
                                            motorC.dc(100)
                                            wait(200)
                                            servosP.desativa(1)
                                            servosP.desativa(3)
                                            servosP.desativa(4)
                                            servosP.desativa(5)
                                            wait(100)
                                            servosP.move(5,0)# abrir
                                            print("pra tras")
                                            while True:#pra trasssss
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() <= -1000 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            motorB.stop()
                                            motorC.stop()
                                            motorB.stop()
                                            motorC.stop()
                                            tanki.stop()
                                        #sair do for line
                                        servosP.move(5,40)# fechar
                                        tanki.turn(150)
                                        tanki.stop()
                                    elif vendoTRIANGULOcor == "vermelho":
                                        tanki.stop()
                                        motorB.reset_angle(0)
                                        motorC.reset_angle(0)
                                        wait(500)
                                        motorB.dc(-100)
                                        motorC.dc(100)
                                        motorB.dc(-100)
                                        motorC.dc(100)
                                        wait(1000)
                                        while True: # ir para tras pra ter certeza que ta no triangulo
                                            wait(50)
                                            print(motorB.angle(),motorC.angle(),"parado: ",parado, "state: ",tanki.state()[3])
                                            if tanki.state()[3] < 20:
                                                parado = parado + 1
                                            if tanki.state()[3] > 60:
                                                parado = 0
                                            if motorB.angle() <= -1000 or parado > 20:
                                                tanki.stop()
                                                break
                                        tanki.stop
                                        servosP.desativa(1)
                                        servosP.desativa(3)
                                        servosP.desativa(4)
                                        servosP.desativa(5)
                                        wait(500)
                                        servosP.move(5,80)# abrir
                                        wait(1000)
                                        for c in range(1,4):
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            servosP.desativa(1)
                                            servosP.desativa(3)
                                            servosP.desativa(4)
                                            servosP.desativa(5)
                                            wait(500)
                                            servosP.move(5,40)#fechar
                                            wait(500)
                                            motorB.dc(100)
                                            motorC.dc(-100)
                                            print("pra frente")
                                            while True:# ir para frente
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() >= 100 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            motorB.stop()
                                            motorC.stop()
                                            motorB.stop()
                                            motorC.stop()
                                            tanki.stop()
                                            wait(100)
                                            motorB.reset_angle(0)
                                            motorC.reset_angle(0)
                                            wait(100)
                                            motorB.dc(-100)
                                            motorC.dc(100)
                                            wait(200)
                                            servosP.desativa(1)
                                            servosP.desativa(3)
                                            servosP.desativa(4)
                                            servosP.desativa(5)
                                            wait(100)
                                            servosP.move(5,80)# abrir
                                            print("pra tras")
                                            while True:#pra trasssss
                                                wait(50)
                                                print(motorB.angle(),motorC.angle(),parado)
                                                if tanki.state()[3] < 20:
                                                    parado = parado + 1
                                                if tanki.state()[3] > 60:
                                                    parado = 0
                                                if motorB.angle() <= -1000 or parado > 20:
                                                    tanki.stop()
                                                    break
                                            motorB.stop()
                                            motorC.stop()
                                            motorB.stop()
                                            motorC.stop()
                                            tanki.stop()
                                        #sair do for line
                                        servosP.move(5,40)
                                        tanki.turn(150)
                                        tanki.stop()
                                        ################################
                                    ################################################
                                    tanki.stop()
                                    print("triangulos_final: ","verde: ", vendoTRIANGULOVERDE, "vermelho: ", vendoTRIANGULOVERMELHO)
                        ##########################################################################################################################################################################################33
                        if sairdoRESGATE == 1:#fugir do resgate
                            print("sair do resgate")
                            wait(1000)
                            motorB.dc(100)
                            motorC.dc(100)
                            wait(10000)
                            tanki.stop()
                            #MODIFICAR APARTIR DAQUI!!!!
                        ########################################################################################################################################
                        while True:
                            retorno1= multiplex1.read(0)
                            ultrafrente= retorno1[2]
                            ultradireita= retorno1[3]
                            ultraesquerda= retorno1[0]
                            #print(ultrafrente)
                            wait(100)
                        wait(999999)
#########################################################################################
                        
###############################################################################################################        
        # Verifica se há um obstáculo
        #ta faltando inserir a parte once ele identifica o obstaculo com a camera!!!!!!

        retorno1= multiplex1.read(0)
        ultrafrente= retorno1[2]
        ultradireita= retorno1[3]
        ultraesquerda= retorno1[0]
        botao_stop=retorno1[6]
        botao_parar= retorno1[5]
        ChoqueESQ= retorno1[4]
        ChoqueDIR= retorno1[7]
        if ChoqueESQ == 1 or ChoqueDIR == 1 :  
            print("Obstáculo detectado!")
            guinada
            tanki.turn(-50)
            tanki.straight(-150)
            tanki.stop()
            motorB.dc(100)
            motorC.dc(-10)
            contOBS=0
            wait(1000)
            while True:
                guinada=guinadaAA.read(0)[0]
                retorno = sensor1.read(2)
                fora1 = retorno[0]#esquerda REAL>>>direita
                meio1 = retorno[1]#esquerda REAL>>>direita
                meio2 = retorno[2]#direita  REAL>>>esquerda
                fora2 = retorno[3]#direita  REAL>>>esquerda
                wait(100)
                if fora1 < 40 or meio1 < 40:
                    tanki.stop()
                    break
            tanki.stop()
            wait(100)
            tanki.turn(-30)
            tanki.stop()
            tanki.straight(-80)
            tanki.stop()
            wait(100)

########################################################################################
########################################################################################
        #IDENTIFICAR CURVA PRETO COM OS 4 SENSORES
        if fora1 <= 10:
            
            pretoesq = 140
            pretodir = 0

        if fora2 <= 10:
            
            pretodir = 140
            pretoesq = 0

        else:
             if pretoesq > 0:
                pretoesq = pretoesq - 1
    
             if pretodir > 0:
                pretodir = pretodir - 1
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################        
        alvo= 18.8
        # Verifica se viu verde
        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        
        if 0==0:
            retorno = sensor1.read(2)
            fora1 = retorno[0]
            meio1 = retorno[1]
            meio2 = retorno[2]
            fora2 = retorno[3]
            cloresq = retorno[17]
            clormind = retorno[18]
            clordir = retorno[19]
            guinada=guinadaAA.read(0)[0]
            H1 = (retorno[20]*2)
            S1 = (retorno[21]*2)
            V1 = (retorno[22]*2)
            H2 = (retorno[26]*2)
            S2 = (retorno[27]*2)
            V2 = (retorno[28]*2)
            if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo) and fora1 > meio1 and fora2 > meio2 :
                wait(30)
                if verdeDireita :
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    guinada
                    motorB.run(-70)
                    motorC.run(70)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        guinada=guinadaAA.read(0)[0]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        #tanki.stop()
                        if verdeEsquerda:
                            contE= 1
                        if contE > 0:
                            contE = contE + 1
                        if contE >= 2:   
                            print("2verdes")
                            verde=2
                            break
                        print(contE)
                        if verdeDireita and fora1 > meio1 and fora2 > meio2:
                            print("direita")
                            verde=1
                            break
                    tanki.stop()
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    wait(100)
                    motorB.run(100)
                    motorC.run(-100)
                    while True:
                        wait(100)
                        print(motorB.angle(),motorC.angle())
                        if motorB.angle() >= 80:
                            tanki.stop()
                            break
                    tanki.stop()
                    wait(1000)
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    guinada=guinadaAA.read(0)[0]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    wait(100)
                    motorB.run(-100)
                    motorC.run(100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        guinada=guinadaAA.read(0)[0]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        wait(100)
                        print(motorB.angle(),motorC.angle())
                        if verdeDireita or verdeEsquerda:
                            tanki.stop()
                            verde=0
                            verde=0
                            break
                        elif fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                            tanki.stop()
                            verde=1
                            verde=1
                            break
                    tanki.stop()
                    print(verde)
                    wait(100)
                    if verde == 0:#vai pra tras conferir
                        motorB.reset_angle(0)
                        motorC.reset_angle(0)
                        wait(100)
                        motorB.run(-100)
                        motorC.run(100)
                        while True:
                            wait(100)
                            print(motorB.angle(),motorC.angle())
                            if motorB.angle() <= -30 and verdeDireita or verdeEsquerda:
                                tanki.stop()
                                verde= 10
                                break
                            if motorB.angle() <= -35:
                                tanki.stop()
                                print("ele passou muito pra tras")
                                verde=11
                                break
                        tanki.stop()
                        print(verde)
                        wait(100)
                    #######conefirir
                    if verde == 11:
                        print("ele veio aqui")
                        motorB.reset_angle(0)
                        motorC.reset_angle(0)
                        wait(100)
                        motorB.run(100)
                        motorC.run(-100)
                        while True:
                            wait(100)
                            print(motorB.angle(),motorC.angle())
                            if motorB.angle() >= 90:
                                tanki.stop()
                                break
                        tanki.stop()
                        wait(100)
                    if verde == 10:
                        tanki.stop()
                        print("verde antes")
                        verde = 1
                        
                        tanki.stop()
                    wait(100)
                    ###########################################3
                    if verde ==1:
                        motorB.run(-100)
                        motorC.run(100)
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            cloresq = retorno[17]
                            clormind = retorno[18]
                            clordir = retorno[19]
                            guinada=guinadaAA.read(0)[0]
                            H1 = (retorno[20]*2)
                            S1 = (retorno[21]*2)
                            V1 = (retorno[22]*2)
                            H2 = (retorno[26]*2)
                            S2 = (retorno[27]*2)
                            V2 = (retorno[28]*2)
                            verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                            verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                            wait(100)
                            print(motorB.angle(),motorC.angle())
                            if verdeEsquerda:
                                if verdeDireita:
                                    tanki.stop()
                                    verde=2
                                    break
                            elif motorB.angle() < -100:
                                tanki.stop()
                                break
                        print(verde)        
                        wait(100)
                    if verde == 1:
                        print("verde direita")
                        tanki.turn(80)
                        tanki.straight(80)
                        tanki.stop()
                        motorB.run(999)
                        motorC.run(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                        tanki.turn(-10)
                        tanki.stop()
                    elif verde == 2:
                        print("2verdesss")
                        tanki.turn(30)
                        tanki.straight(190)
                        tanki.stop()
                        motorB.dc(999)
                        motorC.dc(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                        tanki.turn(-10)
                        tanki.stop()
                    

#############################################################################################################################################################################################
            retorno = sensor1.read(2)
            fora1 = retorno[0]
            meio1 = retorno[1]
            meio2 = retorno[2]
            fora2 = retorno[3]
            cloresq = retorno[17]
            clormind = retorno[18]
            clordir = retorno[19]
            guinada=guinadaAA.read(0)[0]
            H1 = (retorno[20]*2)
            S1 = (retorno[21]*2)
            V1 = (retorno[22]*2)
            H2 = (retorno[26]*2)
            S2 = (retorno[27]*2)
            V2 = (retorno[28]*2)
            if H2 >=(90-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo) and fora1 > meio1 and fora2 > meio2:
                wait(30)
                if verdeEsquerda :
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    guinada
                    motorB.run(-70)
                    motorC.run(70)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        guinada=guinadaAA.read(0)[0]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        #tanki.stop()
                        if verdeDireita:
                            contD= 1
                        if contD > 0:
                            contD = contD + 1
                        if contD >= 2:   
                            print("2verdes")
                            verde=2
                            break
                        print(contD)
                        if verdeEsquerda and fora1 > meio1 or fora2 > meio2:
                            print("esquerda")
                            verde=1
                            break
                    tanki.stop()
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    wait(100)
                    motorB.run(100)
                    motorC.run(-100)
                    while True:
                        wait(100)
                        print(motorB.angle(),motorC.angle())
                        if motorB.angle() >= 80:
                            tanki.stop()
                            break
                    tanki.stop()
                    wait(1000)
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]
                    cloresq = retorno[17]
                    clormind = retorno[18]
                    clordir = retorno[19]
                    guinada=guinadaAA.read(0)[0]
                    H1 = (retorno[20]*2)
                    S1 = (retorno[21]*2)
                    V1 = (retorno[22]*2)
                    H2 = (retorno[26]*2)
                    S2 = (retorno[27]*2)
                    V2 = (retorno[28]*2)
                    verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                    verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                    motorB.reset_angle(0)
                    motorC.reset_angle(0)
                    wait(100)
                    motorB.run(-100)
                    motorC.run(100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        cloresq = retorno[17]
                        clormind = retorno[18]
                        clordir = retorno[19]
                        guinada=guinadaAA.read(0)[0]
                        H1 = (retorno[20]*2)
                        S1 = (retorno[21]*2)
                        V1 = (retorno[22]*2)
                        H2 = (retorno[26]*2)
                        S2 = (retorno[27]*2)
                        V2 = (retorno[28]*2)
                        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        wait(100)
                        print(motorB.angle(),motorC.angle())
                        if verdeDireita or verdeEsquerda:
                            tanki.stop()
                            verde=0
                            verde=0
                            break
                        elif fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                            tanki.stop()
                            verde=1
                            verde=1
                            break
                    tanki.stop()
                    print(verde)
                    wait(1000)
                    if verde ==0:
                        motorB.reset_angle(0)
                        motorC.reset_angle(0)
                        wait(100)
                        motorB.run(100)
                        motorC.run(-100)
                        while True:
                            wait(100)
                            print(motorB.angle(),motorC.angle())
                            if motorB.angle() >= 90:
                                tanki.stop()
                                break
                        tanki.stop()
                        wait(1000)
                    ###########################################3
                    if verde ==1:
                        motorB.run(-100)
                        motorC.run(100)
                        while True:
                            retorno = sensor1.read(2)
                            fora1 = retorno[0]
                            meio1 = retorno[1]
                            meio2 = retorno[2]
                            fora2 = retorno[3]
                            cloresq = retorno[17]
                            clormind = retorno[18]
                            clordir = retorno[19]
                            guinada=guinadaAA.read(0)[0]
                            H1 = (retorno[20]*2)
                            S1 = (retorno[21]*2)
                            V1 = (retorno[22]*2)
                            H2 = (retorno[26]*2)
                            S2 = (retorno[27]*2)
                            V2 = (retorno[28]*2)
                            verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                            verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                            wait(100)
                            print(motorB.angle(),motorC.angle())
                            if verdeDireita:
                                if verdeEsquerda:
                                    tanki.stop()
                                    verde=2
                                    break
                            elif motorB.angle() < -100:
                                tanki.stop()
                                break
                        print(verde)       
                        wait(1000)
                    if verde == 1 and verde == 1:
                        print("verde esquerda")
                        tanki.turn(50)
                        tanki.straight(-50)
                        tanki.stop()
                        motorB.run(-999)
                        motorC.run(-999)  
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                        tanki.turn(-10)
                        tanki.stop()
                    elif verde == 2 and verde == 2:
                        print("2verdesss")
                        tanki.turn(30)
                        tanki.straight(190)
                        tanki.stop()
                        motorB.dc(999)
                        motorC.dc(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                        tanki.turn(-10)
                        tanki.stop()

######################################################################################################################################################################################################
            if H3 >=(90-alvo) and H3 <=(110+alvo) and S3 >=(50-alvo) and S3 <=(70+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo):
                wait(50)
                if verdeMeio and not fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:      
                    ev3.speaker.beep(600,100)
                    if verdeEsquerda or verdeDireita:
                        if verdeMeio and verdeDireita and fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                            print("FdireitaMM")
                            tanki.turn(70)
                            tanki.straight(50)
                            tanki.stop()
                            motorB.run(999)
                            motorC.run(999)
                            while True:
                                retorno = sensor1.read(2)
                                meio1 = retorno[1]
                                if meio1 <= 65:
                                    tanki.stop()
                                    contD = 0
                                    contE = 0
                                    contM = 0
                                    pretodir = 0
                                    pretoesq = 0
                                    break        
                            motorB.stop()
                            motorC.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                        elif verdeMeio and verdeEsquerda and fora1 < 40 and fora2 < 40 and meio1 < 40 and meio2 < 40:
                            print("fesquerdaMM")
                            tanki.turn(70)
                            tanki.straight(-50)
                            tanki.stop()
                            motorB.run(-999)
                            motorC.run(-999)
                            while True:
                                retorno = sensor1.read(2)
                                meio1 = retorno[2]
                                if meio1 <= 65:
                                    tanki.stop()
                                    contD = 0
                                    contE = 0
                                    contM = 0
                                    pretodir = 0
                                    pretoesq = 0
                                    break        
                            motorB.stop()
                            motorC.stop()
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                    elif fora1 <= 40 or meio2 <= 40:
                        print("curva para direitaMM")
                        tanki.turn(50)
                        tanki.straight(50)
                        tanki.stop()
                        motorB.run(999)
                        motorC.run(999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[1]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                    elif fora2 <= 40 or meio1 <= 40:
                        print("curva para esquerdaMM")
                        tanki.turn(50)
                        tanki.straight(-50)
                        tanki.stop()
                        motorB.run(-999)
                        motorC.run(-999)
                        while True:
                            retorno = sensor1.read(2)
                            meio1 = retorno[2]
                            if meio1 <= 65:
                                tanki.stop()
                                contD = 0
                                contE = 0
                                contM = 0
                                pretodir = 0
                                pretoesq = 0
                                break        
                        motorB.stop()
                        motorC.stop()
                        contD = 0
                        contE = 0
                        contM = 0
                        pretodir = 0
                        pretoesq = 0
                    
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
            #tsttttttttttttttttttt verdeeeeeeeeeeeeeeeeeeeeeeeeeeee
        
        if fora1 >= 90 and fora2 >= 90 and meio1 >= 90 and meio2 >= 90:
            if pretodir > 0: 
                print("90preto esquerda")
                tanki.turn(10)
                tanki.stop() 
                motorB.stop()
                wait(1000)
                ev3.speaker.beep()
                motorB.dc(-100)
                motorC.dc(-100)
                motorB.dc(-100)
                motorC.dc(-100)
                retorno = sensor1.read(0)
                fora2 = retorno[3]#direita  REAL>>>esquerda
                wait(100)
                while True:
                    retorno = sensor1.read(0)
                    fora2 = retorno[3]#direita  REAL>>>esquerda
                    wait(100)
                    print(fora2)
                    if fora2 <= 50 :
                        tanki.stop()
                        pretodir = 0
                        pretoesq = 0
                        contGap=0
                        break
                print("fez")
                wait(1000)
                motorB.stop()
                motorC.stop()
                
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa
            #tsttttttttttttttttttt direitaaaaaaaaaaaa

            elif pretoesq > 0:
                print("90preto direita")
                tanki.turn(10)
                tanki.stop() 
                motorB.stop()
                wait(1000)
                ev3.speaker.beep()
                motorB.dc(100)
                motorC.dc(100)
                motorB.dc(100)
                motorC.dc(100)
                retorno = sensor1.read(0)
                fora1 = retorno[0]#esquerda REAL>>>direita
                wait(100)
                while True:
                    retorno = sensor1.read(0)
                    fora1 = retorno[0]#esquerda REAL>>>direita
                    wait(100)
                    print(fora1)
                    if fora1 <= 50 :
                        tanki.stop()
                        pretodir = 0
                        pretoesq = 0
                        contGap=0
                        break
                print("fez")
                wait(1000)
                motorB.stop()
                motorC.stop()
                
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            else:
                # GAP
                ev3.speaker.beep(600,100)
                pretodir = 0
                pretoesq = 0
                contGap = 0
                tanki.stop()
                print("gaap")
                motorB.run(-300)
                motorC.run(300)
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

                    if contGap > 170 or meio1 < 40 or meio2 < 40:
                        print("linha do gap")
                        tanki.stop()
                        break
                tanki.stop()
                # verifica curva s/n s:para n:gaap
                retorno = sensor1.read(2)
                fora1 = retorno[0]
                meio1 = retorno[1]
                meio2 = retorno[2]
                fora2 = retorno[3]
                wait(100)
                if meio1 > 90 or meio2 > 90:
                    wait(20)
                    if fora1 > 90 and fora2 > 90:
                        #n:gaap
                        motorB.reset_angle(0)
                        motorB.run(400)
                        motorC.run(-400)
                        wait(200) #ajeitar
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
                
                #fazer com que o robo agora va para o outro lado
                #ou seja fazer com que o robo va para frente ate ver a linha preta
                #utilizar os sensores fora1,meio1,meio2,fora2 para poder identificar a linha
                #importante que o gap não atrapalhe a correção quando o robo perde a linha

                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
        PESO_MEIO = 1
        PESO_FORA = 1.75
        ki = 0.001  
        base = ((45) * 10)

        esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
        direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
        error = (esquerda - direita) * 0.5

        integral += error * 0.01 
        derivative = error - old_error
        corr = (error * (kp * (1))) + (derivative * (kd * (1))) + (integral * ki)
    
        powerB = base - corr
        powerC = -base - corr
        increPLUS=0.5
        INCREplus=0.75
        powerB = max(min(int(powerB * (increPLUS if powerB > 0 else INCREplus)), 900), -900)
        powerC = max(min(int(powerC * (INCREplus if powerC > 0 else increPLUS)), 900), -900)

        motorB.run(powerB)
        motorC.run(powerC)
        #print(motorB.speed(),motorC.speed(),"__", powerB,powerC)
        #print(tanki.state())
        old_error = error

        if botao_parar > 0:
            print("parar programação!")
            motorB.stop()
            motorC.stop()
            ev3.speaker.beep(500,1000)
            sys.exit()
        if botao_stop > 0:
            print("parado")
            motorB.stop()
            motorC.stop()
            wait(100)
            while True:
                contD = 0
                contE = 0
                contM = 0
                pretodir = 0
                pretoesq = 0
                if botao_stop == 1:
                    break
                if botao_stop == 0:
                    motorB.stop()
                    motorC.stop() 
#calibraBranco()
#calibraPreto()
sensor()