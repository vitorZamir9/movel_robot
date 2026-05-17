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

####################################################################################################
ev3= EV3Brick()
sensor1 = LUMPDevice(Port.S1)
motorB = Motor(Port.B,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)

# VARIAVEIS / IMPORT
error = 0
powerB = 0
powerC = 0
corr = 0
old_error = 0
pretoesq = 0
pretodir = 0
integral = 0
derivative = 0
PESO_MEIO = 1.0
PESO_FORA = 2.25

# ---> VARIÁVEIS DE COMUNICAÇÃO COM A RASPBERRY <---
gyro_rasp_z = 0.0 

previsao_camera = None # Memória da câmara para o verde

tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5 , axle_track=104.0) #isso funciona para movimentos do robô, alguns, mas é melhor usar o motorB e C dc
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

#### initi ####
def calibraBranco(): #todos os sensores no branco, o mínimo de sommbra possível, robô virado para a luz
    retorno = sensor1.read(3)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(3)
        wait(100)
    print("Calibrado Branco")

def calibraPreto(): #tudo preto, verifique para ver se está certo mesmo
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
    global derivative
    global integral
    global motorB
    global motorC
    global gyro_rasp_z 
    global previsao_camera
    global pretodir
    global pretoesq
    
    buffer_serial = ""
    alvo = 15 # Alvo para a calibração do HSV do verde
    
    while True:
        # ==========================================
        # 1. LEITURA DOS SENSORES FÍSICOS
        # ==========================================
        retorno = sensor1.read(2)
        fora1 = retorno[0] # esquerda REAL>>>direita
        meio1 = retorno[1] # esquerda REAL>>>direita
        meio2 = retorno[2] # direita  REAL>>>esquerda
        fora2 = retorno[3] # direita  REAL>>>esquerda
        posicao = (retorno[29]*2)
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        # Leitura HSV para o verde
        H1 = (retorno[20]*2)
        S1 = (retorno[21]*2)
        V1 = (retorno[22]*2)
        
        H3 = (retorno[23]*2)
        S3 = (retorno[24]*2)
        V3 = (retorno[25]*2)

        H2 = (retorno[26]*2)
        S2 = (retorno[27]*2)
        V2 = (retorno[28]*2)

        # ==========================================
        # 2. CONTROLO PID (SEGUIR LINHA)
        # ==========================================
        kp = 2.5
        kd = 0.1
        ki = 0.01
        base = 120

        esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
        direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
        error = (direita - esquerda) * 0.5

        integral += error * 0.01 
        derivative = error - old_error
        corr = (error * (kp * (-1))) + (derivative * kd) + (integral * ki)
    
        powerB = base - corr
        powerC = -base - corr
        increPLUS= 0.5
        INCREplus= 1.0
        powerB = max(min(int(powerB * (increPLUS if powerB > 0 else INCREplus)), 900), -900)
        powerC = max(min(int(powerC * (INCREplus if powerC > 0 else increPLUS)), 900), -900)

        motorB.dc(powerB)
        motorC.dc(powerC)

        old_error = error
        
        # ==========================================
        # 3. MEMÓRIA DAS CURVAS DE 90 GRAUS (PRETO)
        # ==========================================
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

       # ==========================================
        # 4. LEITURA DA CÂMERA E GIROSCÓPIO (MEMÓRIA)
        # ==========================================
        data = ser.read_all()
        if data:
            try:
                buffer_serial += data.decode('utf-8', 'ignore')
                while '\n' in buffer_serial:
                    linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                    cmd = linha_cmd.strip()
                    
                    if not cmd or cmd == "frente":
                        continue
                    
                    if cmd.startswith("MPU_Z:"):
                        try:
                            gyro_rasp_z = float(cmd.split(":")[1].strip())
                        except:
                            pass
                        continue 
                        
                    # Atualiza a Memória Tática da câmara para o verde
                    print("CAMERA VÊ O FUTURO:", cmd)
                    if "esquerda antes" in cmd:
                        previsao_camera = "esquerda"
                    elif "direita antes" in cmd:
                        previsao_camera = "direita"
                    elif "dois verdes" in cmd:
                        previsao_camera = "beco"
                    elif "verde depois" in cmd:
                        previsao_camera = "depois"  
                        
            except Exception as e:
                pass

        # ==========================================
        # 5. O GATILHO FÍSICO DO VERDE (REFLEXO)
        # ==========================================
        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        fora1 , meio1 , meio2 , fora2

        if verdeDireita or verdeEsquerda or verdeMeio or previsao_camera != None:
            
            if  previsao_camera == "direita" or verdeDireita :
                if meio1 >= 60 or meio2 >= 60 :
                    tanki.stop()
                    tanki.turn(70)
                    tanki.straight(90)
                    tanki.stop()
                    ev3.speaker.beep(400) 
                    print(">>> EXECUTANDO VERDE DIREITA + camera")
                    tanki.stop()
                    motorB.dc(100)
                    motorC.dc(100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        if fora1 <= 40  :
                            tanki.stop()
                            break
                    motorB.stop()
                    motorC.stop()
                    previsao_camera = None
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")
            elif verdeDireita:
                if meio1 >= 60 or meio2 >= 60 :
                    tanki.stop()
                    tanki.turn(70)
                    tanki.straight(90)
                    tanki.stop()
                    ev3.speaker.beep(400) 
                    print(">>> EXECUTANDO VERDE DIREITA")
                    tanki.stop()
                    motorB.dc(100)
                    motorC.dc(100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        if fora1 <= 40  :
                            tanki.stop()
                            break
                    motorB.stop()
                    motorC.stop()
                    previsao_camera = None
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")

            elif previsao_camera == "esquerda" or verdeEsquerda :
                if meio1 >= 60 or meio2 >= 60 :
                    tanki.stop()
                    tanki.turn(70)
                    tanki.straight(-90)
                    tanki.stop()
                    ev3.speaker.beep(200) 
                    print(">>> EXECUTANDO VERDE ESQUERDA + camera")
                    tanki.stop()
                    motorB.dc(-100)
                    motorC.dc(-100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        if fora2 <= 40  :
                            tanki.stop()
                            break
                    motorB.stop()
                    motorC.stop()
                    previsao_camera = None 
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")
            elif verdeEsquerda:
                if meio1 >= 60 or meio2 >= 60 :
                    tanki.stop()
                    tanki.turn(70)
                    tanki.straight(-90)
                    tanki.stop()
                    ev3.speaker.beep(200) 
                    print(">>> EXECUTANDO VERDE ESQUERDA")
                    tanki.stop()
                    motorB.dc(-100)
                    motorC.dc(-100)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[0]
                        meio1 = retorno[1]
                        meio2 = retorno[2]
                        fora2 = retorno[3]
                        if fora2 <= 40  :
                            tanki.stop()
                            break
                    motorB.stop()
                    motorC.stop()
                    previsao_camera = None 
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")
            elif previsao_camera == "dois verdes" or verdeDireita :
                wait(10)
                if verdeEsquerda :
                    tanki.stop()
                    ev3.speaker.beep(600) 
                    print(">>> EXECUTANDO BECO + camera")
                    tanki.turn(30)
                    tanki.straight(190)
                    tanki.stop()
                    
                    motorB.stop()
                    motorC.stop()
                    tanki.turn(-50)
                    tanki.stop()
                    previsao_camera = None # Limpa a memória
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")
            elif verdeDireita:
                if verdeEsquerda:
                    tanki.stop()
                    ev3.speaker.beep(600) 
                    print(">>> EXECUTANDO BECO")
                    tanki.turn(30)
                    tanki.straight(190)
                    tanki.stop()
                    
                    motorB.stop()
                    motorC.stop()
                    tanki.turn(-50)
                    tanki.stop()
                    previsao_camera = None # Limpa a memória
                    
                    # [NOVO - HANDSHAKE] Avisa a Raspberry que terminou o giro e ela pode destrancar
                    ser.write(b"passou_verde\n")

            elif previsao_camera == "depois" and meio1 <= 30 or meio2 <= 30 and cloresq == 1 or clordir == 1:
                tanki.stop()
                ev3.speaker.beep(800, 200) 
                print(">>> SEGUINDO POR TEMPO (GAP/DEPOIS)")
                
                cronometro = StopWatch()
                tempo_limite = 200  # <--- DEFINE AQUI O TEMPO EM MILISSEGUNDOS (1.5s)
                
                while cronometro.time() < tempo_limite:
                    # É OBRIGATÓRIO ler os sensores dentro do while para o PID funcionar
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]

                    # Teu PID específico para este trecho
                    kp = 2
                    kd = 0.5
                    ki = 0.15
                    base = 100

                    esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
                    direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
                    error = (direita - esquerda) * 0.5

                    integral += error * 0.01 
                    derivative = error - old_error
                    corr = (error * (kp * (-1))) + (derivative * kd) + (integral * ki)
                
                    powerB = base - corr
                    powerC = -base - corr
                    increPLUS = 0.5
                    INCREplus = 1.0
                    powerB = max(min(int(powerB * (increPLUS if powerB > 0 else INCREplus)), 900), -900)
                    powerC = max(min(int(powerC * (INCREplus if powerC > 0 else increPLUS)), 900), -900)

                    motorB.dc(powerB)
                    motorC.dc(powerC)
                    old_error = error
                    wait(10) # Pequena pausa para estabilizar o processador
                
                previsao_camera = None 
                
                # [NOVO - HANDSHAKE] Avisa a Raspberry que passou pelo gap/verde depois
                ser.write(b"passou_verde\n")
        
                print(">>> TEMPO ESGOTADO: Voltando ao loop principal")

        if fora1 >= 90 and fora2 >= 90 and meio1 >= 90 and meio2 >= 90:
            if pretodir > 0: 
                print("90preto esquerda")
                tanki.turn(10)
                tanki.stop() 
                motorB.stop()
                wait(100)
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
                wait(100)
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
                wait(100)
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
                wait(100)
                motorB.stop()
                motorC.stop()
                
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
                #tsttttttttttttttttttt esquerdaaaaaaaaaaaaa
            else:
                # GAP
                ev3.speaker.beep(100)
                tanki.stop()
               
                
                #fazer com que o robo agora va para o outro lado
                #ou seja fazer com que o robo va para frente ate ver a linha preta
                #utilizar os sensores fora1,meio1,meio2,fora2 para poder identificar a linha
                #importante que o gap não atrapalhe a correção quando o robo perde a linha

                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
                #tsttttttttttttttttttt gaaaaaaaaappppppppppp
#calibraBranco()
#calibraPreto()
sensor()




