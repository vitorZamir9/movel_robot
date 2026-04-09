
#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pybricks.iodevices import UARTDevice
from servos import Servos
import sys

#=================================================================
ev3 = EV3Brick()

guinadaAA = LUMPDevice(Port.S4)
multiplex1 = LUMPDevice(Port.S3)
sensor1 = LUMPDevice(Port.S1)

motorB = Motor(Port.B, gears=[12,20], positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.C, gears=[12,20], positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S4, baudrate=115200, timeout=0.1)
servosp = Servos(serial=ser, true)

#VARIAVEIS/IMPORT
kp = 5
ki = 0
kd = 0
casa = 0
cont = 0
powerB = 0
powerC = 0
corr = 0
old_error = 0
pretoesq = 0
pretodir = 0
integral = 0
derivative = 0
contGAP = 0
contd = 0
forsado = 0
ultimacoisa=0
ultimofrente=0
ultimaSILVER=0
ultimaBLACK=0
vendoTRIANGULO=0
vendoTRIANGULOVERDE=0
vendoTRIANGULOVERMELHO=0
prafrente=0
lado = None
javiantes=None
chegounavitima=None
saiudoRESGATE=None
parado = 0
agora = None

tanki = DriveBase(motorB, motorC, wheel_diameter=65.0 , axle_track=120.0)
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=999999)

resgatt=0

def calibraBranco():
    retorno = sensor1.read(3)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(3)
        wait(100)
    print('Calibrado Branco')

def calibraPreto():
    retorno = sensor1.read(4)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(4)
        wait(100)
    print('Calibrado Preto')

#=================================================================

def botao():
    global multiplex1
    retornoM = multiplex1.read(0)
    if retornoM[4] > 0:
        print("parado")
        motorB.stop()
        motorC.stop()

def sensor():
    global old_error
    global sensor1
    global pretoesq
    global pretodir
    global guinadaAA
    global error
    global integral
    global derivative
    global motorC
    global motorB
    global cont
    global tanki
    global multiplex1
    global ser
    global resgatt
    global agora
    global verdeDireita
    global verdeMeio
    global verdeEsquerda
    global ultraDireita
    global ultraFrente
    global ultraEsquerda
    global kd
    global ki
    global kp
    global powerB
    global powerC
    global forsado
    global contGAP
    global contd
    global vendoTRIANGULO
    global vendoTRIANGULOVERDE
    global vendoTRIANGULOVERMELHO
    global prafrente
    global lado
    global javiantes
    global chegounavitima
    global saiudoRESGATE
    global parado
    global detected

    while True:
        ev3.screen.clear()
        ev3.screen.print("V3")
        ser.write(b"OFF\r\n")

        retornoM= multiplex1.read(0)
        ultradireita= retornoM[0]
        ultrafrente= retornoM[1]
        ultraesquerda= retornoM[2]
        botao_parar= retornoM[4]
        botao_parar2= retornoM[5]
        ChoqueDIR= retornoM[6]
        ChoqueESQ= retornoM[7]
        
        retorno = sensor1.read(2)
        meio1 = retorno[1] #esquerda REAL>>direita
        meio2 = retorno[2] #direita REAL>>esquerda
        fora1 = retorno[0] #esquerda REAL>>esquerda
        fora2 = retorno[3] #direita REAL>>esquerda
        
        red_tape = retorno[18]
        red_tape1 = retorno[19]
        G1 = (retorno[4])
        G2 = (retorno[5])
        G3 = (retorno[6])
        C1 = (retorno[7])

        C2 = (retorno[8])
        C3 = (retorno[9])
        S1 = (retorno[10])
        S2 = (retorno[11])
        S3 = (retorno[12])

        H1 = (retorno[26]*2)
        H2 = (retorno[27]*2)
        H3 = (retorno[28]*2)
        V1 = (retorno[24]*2)
        V2 = (retorno[25]*2)
        V3 = (retorno[29]*2)

        clordir = retorno[16]
        cloresq = retorno[17]
        contgap = retorno[29]*2

        # atualizar de acordo com o sensor
        guinada=guinadaAA.read(0)[0]
        tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=999999)

        # =======================================================
        # Verifica se identificou uma rampa
        mprint=afagom 
        # mprint -= 85 # ajustar de acordo com o sensor
        print("Rampa detectada!")
        
        if afagom < -5:
            afagom = -5
            
        if afagom > -1 and casa == 10:
            print("pegou")
            motorB.run(100)
            motorC.run(100)
            wait(50)
            tanki.stop()
            kp = 5.0
            
            if tanki.state()[1] < 20:
                parado = parado + 1
            if tanki.state()[1] > 60:
                parado = 0
            if parado > 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                tanki.stop()
                break

        tanki.stop()
        tanki.turn(-150)
        tanki.stop()
        
        #conferir se triangulo mesmo:
        while True:
            data = ser.read_all()
            if data:
                try:
                    data_str = data.decode('utf-8').strip()
                    retangulo = None
                    lado = None
                    for line in data_str.split('\n'):
                        if not line.strip():
                            continue
                        if 'Retangulo' in line:
                            retangulo = line
                        if 'Lado' in line:
                            lado = line.split(':')[1].strip()
                            
                    if retangulo:
                        print("Alinhando com o tri ngulo. Lado atual:", lado)
                        # loop para alinhar at ficar no meio
                        while lado != "meio":
                            # Atualiza a leitura da serial a cada volta
                            data = ser.read_all()
                            if data:
                                try:
                                    data_str = data.decode('utf-8').strip()
                                    for line in data_str.split('\n'):
                                        if not line.strip():
                                            continue
                                        if 'Lado' in line:
                                            lado = line.split(':')[1].strip()
                                except Exception as e:
                                    pass
                            
                            # Comando de giro baseado no lado atual
                            if lado == "esquerda":
                                motorB.dc(-900)
                                motorC.dc(900)
                            elif lado == "direita":
                                motorB.dc(900)
                                motorC.dc(-900)
                                
                            wait(50)
                            motorB.stop()
                            motorC.stop()
                            
                        ev3.speaker.beep(400)
                        if "Vermelho" in retangulo:
                            vendoTRIANGULOVERMELHO += 1
                            vendoTRIANGULO += 1
                        elif "Verde" in retangulo:
                            vendoTRIANGULOVERDE += 1
                            vendoTRIANGULO += 1
                        tanki.stop()
                        break # Sai do while True principal
                        
                except ValueError:
                    print("Aviso: Dados recebidos n o s o UTF-8 v lido. Ignorando...")
                    ser.flushInput()
                    continue
                except Exception as e:
                    print("Erro inesperado:", e)
                    ser.flushInput()
                    continue
            else:
                print("N o vendo tri ngulo")
                wait(250)
                motorB.reset_angle(0)
                motorC.reset_angle(0)
                motorB.dc(-100)
                motorC.dc(-100)
                while True:
                    wait(100)
                    if motorB.angle() >= 30: 
                        tanki.stop()
                        break
                tanki.stop()

        #=========================================================================
        #ir pro triangulo
        motorB.reset_angle(0)
        motorC.reset_angle(0)
        wait(100)
        motorB.dc(-100)
        motorC.dc(-100)
        while True:
            retornoM = multiplex1.read(0)
            ChoqueESQ = retornoM[7]
            ChoqueDIR = retornoM[6]
            print(motorB.angle(), motorC.angle(), tanki.state()[1], "parado:", parado, ChoqueESQ, ChoqueDIR)
            if tanki.state()[1] < 20:
                parado = parado + 1
            if tanki.state()[1] > 60:
                parado = 0
            if parado >= 20 or ChoqueESQ == 1 or ChoqueDIR == 1:
                tanki.stop()
                break
                
        tanki.turn(-150)
        tanki.turn(150)
        tanki.stop()
        motorB.stop()
        motorC.stop()
        wait(100)

        #=========================================================================
        guinada=guinadaAA.read(0)[0]
        wait(100)
        Anguly.read(4)
        wait(1000)
        guinada=guinadaAA.read(0)[0]
        ev3.speaker.beep()
        
        motorB.reset_angle(0)
        motorC.reset_angle(0)
        wait(100)
        motorB.dc(100)
        motorC.dc(100)
        
        while True: # girarr
            guinada=guinadaAA.read(0)[0]
            wait(50)
            print(motorB.angle(), motorC.angle(), parado, "guinada:", guinada)
            if tanki.state()[1] < 20:
                parado = parado + 1
            if tanki.state()[1] > 60:
                parado = 0
            if abs(guinada) >= 70 or parado >= 20:
                tanki.stop()
                break
        tanki.stop()
        
        motorB.reset_angle(0)
        motorC.reset_angle(0)
        wait(100)
        motorB.dc(-100)
        motorC.dc(-100)
        print("pra tras")
        
        while True: # ir para tras
            wait(50)
            print(motorB.angle(), motorC.angle(), parado)
            if tanki.state()[1] < 20:
                parado = parado + 1
            if tanki.state()[1] > 60:
                parado = 0
            if motorB.angle() <= -1000 or parado >= 20:
                tanki.stop()
                break
                
        tanki.stop()
        motorB.stop()
        motorC.stop()

        tanki.turn(150)# vai pra frente depois que girou
        tanki.stop()

        motorB.reset_angle(0)
        motorC.reset_angle(0)
        wait(100)
        motorB.dc(100)
        motorC.dc(100)
        ev3.speaker.beep()

        while True: # ir para tras denovo
            wait(50)
            print(motorB.angle(), motorC.angle(), parado)
            if tanki.state()[1] < 20:
                parado = parado + 1
            if tanki.state()[1] > 60:
                parado = 0
            if motorB.angle() >= 1000 or parado >= 20:
                tanki.stop()
                break
        tanki.stop()

        #====================acima para se gabaritar no triangulo
        print(vendoTRIANGULOCOR, vendoTRIANGULOVERDE, vendoTRIANGULOVERMELHO)
        wait(1000)

        if vendoTRIANGULOCOR == "verde":
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(500)
            motorB.dc(100)
            motorC.dc(100)
            wait(1000)
            
            while True: # ir pra tras pra ter certeza que ta no triangulo
                wait(50)
                print(motorB.angle(), motorC.angle(), parado, "state:", tanki.state()[1])
                if tanki.state()[1] < 20:
                    parado = parado + 1
                if tanki.state()[1] > 60:
                    parado = 0
                if motorB.angle() <= -1000 or parado > 20:
                    tanki.stop()
                    break
            tanki.stop()

            servosp.desativa(1)
            servosp.desativa(2)
            servosp.desativa(3)
            servosp.desativa(4)
            servosp.desativa(5)
            wait(500)
            servosp.move(5,0)# abrir
            wait(1000)

            for c in range(1,4):
                motorB.reset_angle(0)
                motorC.reset_angle(0)
                wait(500)
                
                servosp.desativa(3)
                servosp.desativa(4)
                servosp.desativa(5)
                wait(500)
                servosp.move(5,40)#fechar
                wait(1000)

                motorB.dc(-100)
                motorC.dc(-100)
                print("pra frente")

                while True:# ir para frente
                    wait(50)
                    print(motorB.angle(), motorC.angle(), parado)
                    if tanki.state()[1] < 20:
                        parado = parado + 1
                    if tanki.state()[1] > 60:
                        parado = 0
                    if motorB.angle() >= 100 or parado > 20:
                        tanki.stop()
                        break
                        
                motorB.stop()
                motorC.stop()
                tanki.stop()
                wait(500)

                motorB.reset_angle(0)
                motorC.reset_angle(0)
                wait(500)
                motorB.dc(100)
                motorC.dc(100)

                servosp.desativa(1)
                servosp.desativa(2)
                servosp.desativa(3)
                servosp.desativa(4)
                servosp.desativa(5)
                wait(500)
                servosp.move(5,0)# abrir
                wait(1000)

                while True:#pra trasssss
                    wait(50)
                    print(motorB.angle(), motorC.angle(), parado)
                    if tanki.state()[1] < 20:
                        parado = parado + 1
                    if tanki.state()[1] > 60:
                        parado = 0
                    if motorB.angle() <= -1000 or parado > 20:
                        tanki.stop()
                        break
                tanki.stop()
                
            servosp.desativa(3)
            servosp.desativa(4)
            servosp.desativa(5)
            wait(500)
            servosp.move(5,40)#fechar
            wait(1000)
            
            motorB.dc(-100)
            motorC.dc(-100)
            print("pra frente")
            
            while True:# ir para frente
                wait(50)
                print(motorB.angle(), motorC.angle(), parado)
                if tanki.state()[1] < 20:
                    parado = parado + 1
                if tanki.state()[1] > 60:
                    parado = 0
                if motorB.angle() >= 100 or parado > 20:
                    tanki.stop()
                    break
                    
            motorB.stop()
            motorC.stop()
            tanki.stop()
            wait(500)

        elif vendoTRIANGULOCOR == "vermelho":
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(500)
            motorB.dc(100)
            motorC.dc(100)
            wait(1000)
            
            while True: # ir pra tras pra ter certeza que ta no triangulo
                wait(50)
                print(motorB.angle(), motorC.angle(), parado, "state:", tanki.state()[1])
                if tanki.state()[1] < 20:
                    parado = parado + 1
                if tanki.state()[1] > 60:
                    parado = 0
                if motorB.angle() <= -1000 or parado > 20:
                    tanki.stop()
                    break
            tanki.stop()
            
            tanki.turn(150)
            tanki.stop()
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(500)
            motorB.dc(-100)
            motorC.dc(-100)
            
            while True: # ir pra tras pra ter certeza que ta no triangulo
                wait(50)
                print(motorB.angle(), motorC.angle(), parado, "state:", tanki.state()[1])
                if tanki.state()[1] < 20:
                    parado = parado + 1
                if tanki.state()[1] > 60:
                    parado = 0
                if motorB.angle() >= 1000 or parado > 20:
                    tanki.stop()
                    break
            tanki.stop()

            servosp.desativa(1)
            servosp.desativa(2)
            servosp.desativa(3)
            servosp.desativa(4)
            servosp.desativa(5)
            wait(500)
            servosp.move(5,0)# abrir
            wait(1000)

            for c in range(1,4):
                motorB.reset_angle(0)
                motorC.reset_angle(0)
                wait(500)
                
                servosp.desativa(3)
                servosp.desativa(4)
                servosp.desativa(5)
                wait(500)
                servosp.move(5,40)#fechar
                wait(1000)

                motorB.dc(-100)
                motorC.dc(-100)
                print("pra frente")

                while True:# ir para frente
                    wait(50)
                    print(motorB.angle(), motorC.angle(), parado)
                    if tanki.state()[1] < 20:
                        parado = parado + 1
                    if tanki.state()[1] > 60:
                        parado = 0
                    if motorB.angle() >= 100 or parado > 20:
                        tanki.stop()
                        break
                        
                motorB.stop()
                motorC.stop()
                tanki.stop()
                wait(500)

                motorB.reset_angle(0)
                motorC.reset_angle(0)
                wait(500)
                motorB.dc(100)
                motorC.dc(100)

                servosp.desativa(1)
                servosp.desativa(2)
                servosp.desativa(3)
                servosp.desativa(4)
                servosp.desativa(5)
                wait(500)
                servosp.move(5,0)# abrir
                wait(1000)

                while True:#pra trasssss
                    wait(50)
                    print(motorB.angle(), motorC.angle(), parado)
                    if tanki.state()[1] < 20:
                        parado = parado + 1
                    if tanki.state()[1] > 60:
                        parado = 0
                    if motorB.angle() <= -1000 or parado > 20:
                        tanki.stop()
                        break
                tanki.stop()
                
            servosp.desativa(3)
            servosp.desativa(4)
            servosp.desativa(5)
            wait(500)
            servosp.move(5,40)#fechar
            wait(1000)
            
            motorB.dc(-100)
            motorC.dc(-100)
            print("pra frente")
            
            while True:# ir para frente
                wait(50)
                print(motorB.angle(), motorC.angle(), parado)
                if tanki.state()[1] < 20:
                    parado = parado + 1
                if tanki.state()[1] > 60:
                    parado = 0
                if motorB.angle() >= 100 or parado > 20:
                    tanki.stop()
                    break
                    
            motorB.stop()
            motorC.stop()
            tanki.stop()
            wait(500)

        tanki.turn(-150)
        tanki.stop()
        
        if saiudoRESGATE == 1: #fugir do resgate
            print("sair do resgate")
            motorB.dc(100)
            motorC.dc(100)
            wait(10000)
            tanki.stop()

        #========================================================================
        
        while True:
            retornoM = multiplex1.read(0)
            ultrafrente = retornoM[1]
            ultradireita = retornoM[0]
            ultraesquerda = retornoM[2]
            
            wait(100)
            wait(999999)
            
            # Verifica se ha um obstaculo 
            #ta faltando inserir a parte onde ele identifica o obstaculo com a camera
            
            retornoM = multiplex1.read(0)
            ultrafrente = retornoM[1]
            ultradireita = retornoM[0]
            ultraesquerda = retornoM[2]
            botao_stop = retornoM[4]
            botao_stop2 = retornoM[5]
            ChoqueDIR = retornoM[6]
            ChoqueESQ = retornoM[7]
            if ChoqueESQ == 1 or ChoqueDIR == 1:
                print("obst culo detectado!")
                tanki.stop()
                tanki.turn(-50)
                tanki.straight(-150)
                tanki.stop()
                motorB.dc(100)
                motorC.dc(-100)
                contOBS=0
                wait(1000)
                while True:
                    guinada=guinadaAA.read(0)[0]
                    retorno = sensor1.read(2)
                    meio1 = retorno[1] #esquerda REAL>>direita
                    meio2 = retorno[2] #direita REAL>>esquerda
                    fora1 = retorno[0] #esquerda REAL>>esquerda
                    fora2 = retorno[3] #direita REAL>>esquerda
                    wait(100)
                    if meio1 > 40 or meio2 > 40:
                        tanki.stop()
                        break
                tanki.stop()
                wait(100)
                tanki.stop()
                tanki.stop()
                tanki.stop()
                tanki.stop()
                
        #=================================================================================
        if fora1 < 10:
            pretoesq = 140
            
        elif fora2 < 10:
            pretodir = 140
            
        else:
            if pretoesq > 0:
                pretoesq = pretoesq - 1
            if pretodir > 0:
                pretodir = pretodir - 1
                
        #=================================================================================
        #  verifica se viu verde
        verdedireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdemeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeesquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        
        if G>0:
            retorno = sensor1.read(2)
            fora1 = retorno[0]
            meio1 = retorno[1]
            meio2 = retorno[2]
            fora2 = retorno[3]
            cloresq = retorno[17]
            clordir = retorno[18]
            guinada=guinadaAA.read(0)[0]
            H1 = (retorno[26]*2)
            S1 = (retorno[27]*2)
            V1 = (retorno[28]*2)
            H2 = (retorno[24]*2)
            S2 = (retorno[25]*2)
            V2 = (retorno[29]*2)
            
            if H1 >=(90-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo) and fora1 > meio1:
                wait(100)
                if verdedireita:
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
                        clordir = retorno[18]
                        guinada=guinadaAA.read(0)[0]
                        H1 = (retorno[26]*2)
                        
                        verdedireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(73+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
                        verdeesquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(73+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
                        
                        if verdedireita:
                            cont1 += 1
                        if cont1 == 1:
                            contf = cont1 + 1
                            if contf > 1:
                                print("2verdes")
                                verde=2
                                break
                                
                        print(cont1)
                        if (verdedireita and fora1 > meio1 and fora2 > meio2):
                            print("direita")
                            verde=1
                            break
                            
            tanki.stop()
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(100)
            motorB.run(-100)
            motorC.run(100)
            wait(100)
            while True:
                print(motorB.angle(),motorC.angle())
                if motorB.angle() >= 80:
                    tanki.stop()
                    break
            
            tanki.stop()
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(100)
            retorno = sensor1.read(2)
            meio1 = retorno[1]
            meio2 = retorno[2]
            
            if cont1 == 2:
                print("2verdes")
                verde=2
                break
                
            if (verdedireita and fora1 > meio1 and fora2 > meio2):
                print("direita")
                verde=1
                break
                
            tanki.stop()
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(100)
            motorB.run(100)
            motorC.run(-100)
            wait(100)
            
            while True:
                print(motorB.angle(),motorC.angle())
                if motorB.angle() <= 80:
                    tanki.stop()
                    break
                    
            tanki.stop()
            motorB.reset_angle(0)
            motorC.reset_angle(0)
            wait(100)
            retorno = sensor1.read(2)
            meio1 = retorno[1]
            meio2 = retorno[2]
            
            if (verdeesquerda and fora1 > meio1 and fora2 > meio2):
                print("esquerda")
                verde=3
                break

        #=================================================================================
        # PID / SEGUIDOR DE LINHA
        
        # Calcula o erro baseado na diferença entre os sensores do meio
        error = meio1 - meio2
        
        # Calcula os termos Proporcional, Integral e Derivativo
        integral = integral + error
        derivative = error - old_error
        
        # Calcula a correção total (Turn)
        Turn = (kp * error) + (ki * integral) + (kd * derivative)
        
        # Aplica a força nos motores (velocidade base + correção)
        # Ajuste a velocidade base (aqui está 30, mas você pode mudar conforme precisar)
        powerB = 30 + Turn
        powerC = 30 - Turn

        # Garante que a potência não ultrapasse os limites de -100 a 100
        if powerB > 100: powerB = 100
        if powerB < -100: powerB = -100
        if powerC > 100: powerC = 100
        if powerC < -100: powerC = -100

        # Aciona os motores
        motorB.dc(powerB)
        motorC.dc(powerC)

        # Atualiza o erro antigo para a próxima iteração do loop
        old_error = error

#=================================================================
# INÍCIO DO PROGRAMA PRINCIPAL
#=================================================================

ev3.speaker.beep()
print("Iniciando robô...")

# Se precisar calibrar, descomente as linhas abaixo:
# calibraBranco()
# calibraPreto()

# Loop principal infinito
while True:
    botao()   # Verifica se o botão de parada de emergência foi pressionado
    sensor()  # Roda a lógica principal de navegação e resgate
