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
import time

####################################################################################################
ev3= EV3Brick()
sensor1 = LUMPDevice(Port.S1)
multiplex1 = LUMPDevice(Port.S2)
motorB = Motor(Port.B,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)
serialservo = UARTDevice(Port.S5, baudrate=115200, timeout=0.1)
servosP= Servos(serialservo,True)

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

def botao():
    global multiplex1
    while True:
        retorno1 = multiplex1.read(0)
        botao_stop = retorno1[6]
        if botao_stop > 0:
            print("parado")
            motorB.stop()
            motorC.stop()
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
    global multiplex1
    
    buffer_serial = ""
    
    while True:
        # ==========================================
        # 0.0 Ligar tela-desafio surpresa/Enviar msg rasp
        # ==========================================
        ev3.screen.clear()
        ev3.screen.print("-7")

        #ser.write(b'OFF\r\n')
        # ==========================================
        # 1.0 LEITURA DO SENSOR DE COR
        # ==========================================
        retorno = sensor1.read(2)

        # Leitura dos sensores para seguir linha
        fora1 = retorno[0] # esquerda REAL>>>direita
        meio1 = retorno[1] # esquerda REAL>>>direita
        meio2 = retorno[2] # direita  REAL>>>esquerda
        fora2 = retorno[3] # direita  REAL>>>esquerda

        # Leitura da posição do sensor sobre a linha preta
        posicao = (retorno[29]*2)
        
        # Leitura unitária dos sensores de cor
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]

        # Leitura RGBC dos sensores
        R1, R3, R2 = (retorno[4]), (retorno[8]), (retorno[12])
        G1, G3, G2 = (retorno[5]), (retorno[9]), (retorno[13])
        B1, B3, B2 = (retorno[6]), (retorno[10]), (retorno[14])
        C1, C3, C2 = (retorno[7]), (retorno[11]), (retorno[15])

        # Leitura HSV para o verde
        H1, H3, H2 = (retorno[20]*2), (retorno[23]*2), (retorno[26]*2)
        S1, S3, S2 = (retorno[21]*2), (retorno[24]*2), (retorno[27]*2)
        V1, V3, V2 = (retorno[22]*2), (retorno[25]*2), (retorno[28]*2)
        
        alvo = 15 # Alvo para a calibração do HSV do verde
        # ==========================================
        # 1.1 LEITURA DO SENSOR MULTIPLEX
        # ==========================================
        retorno1= multiplex1.read(0)

        # Leitura dos sensores ultrasônicos
        ultrafrente= retorno1[2]
        ultradireita= retorno1[3]
        ultraesquerda= retorno1[0]

        # Leitura dos botões para função pro robô
        botao_stop=retorno1[6]
        botao_parar= retorno1[5]

        # Leitura dos botôes que servem pro parachoque
        ChoqueESQ= retorno1[4]
        ChoqueDIR= retorno1[7]
        # ==========================================
        # 2. VERIFICAÇÃO DE INCLINAÇÃO
        # ==========================================
        #print(afagem)

        # ==========================================
        # 3. VERIFICAÇÃO SE O ROBÔ ESTÁ PARADO
        # ==========================================

        # ==========================================
        # 4. RED TAPE
        # ==========================================
        if cloresq ==2 and clormind ==2 and clordir ==2:
            ev3.speaker.beep(1200)
            motorB.stop()
            motorC.stop()
            break
        # ==========================================
        # 5. SILVER TAPE
        # ==========================================
        clear = 35
        rgb=85
        esqgray = R1 > rgb and G1 > rgb and B1 > rgb and C1 > clear 
        mindgray = R3 > rgb and G3 > rgb and B3 > rgb and C3 > clear #prata reflectivo
        dirgray = R2 > rgb and G2 > rgb and B2 > rgb and C2 > clear 
        
        esqgray1 = B1 > 50 and B1 < 66 and C1 > 24 and C1 < 31 and cloresq == 6
        mindgray1 = B3 > 50 and B3 < 66 and C3 > 24 and C3 < 31 and clormind == 6 #calibrar o prata não reflectivo
        dirgray1 = B2 > 50 and B2 < 66 and C2> 24 and C2 < 31 and clordir == 6
        # ==========================================
        # 6. BUMPER PRESSED/ULTRASSÔNICO
        # ==========================================
        if ChoqueESQ == 1 or ChoqueDIR == 1 :  #aqui só esta a identificação do parachoque.Precisa atualizar e adicionar com o ultrassônico
            print("Obstáculo detectado!")
            tanki.turn(-50)
            tanki.straight(-150)
            tanki.stop()
            motorB.dc(100)
            motorC.dc(-10)
            wait(1000)
            while True:
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
        # ==========================================
        # 7. SEEING BLACK AT THE EDGE SENSORS
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
        # 8. ATUALIZAR LEITURA CÂMERA PRÉ-GREEN
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
        # 8.1 GREEN
        # ==========================================
        verdeDireita = H1 >=(95-alvo) and H1 <=(140+alvo) and S1 >=(47-alvo) and S1 <=(70+alvo) and V1 >=(40-alvo) and V1 <=(80+alvo)
        verdeMeio = H3 >=(95-alvo) and H3 <=(140+alvo) and S3 >=(47-alvo) and S3 <=(73+alvo) and V3 >=(40-alvo) and V3 <=(80+alvo)
        verdeEsquerda = H2 >=(95-alvo) and H2 <=(140+alvo) and S2 >=(47-alvo) and S2 <=(70+alvo) and V2 >=(40-alvo) and V2 <=(80+alvo)
        if verdeDireita or verdeEsquerda or verdeMeio:
            if  previsao_camera == "direita" and verdeDireita  :
                tanki.stop()
                tanki.turn(70)
                tanki.straight(90)
                tanki.stop()
                ev3.speaker.beep(400) 
                print(">>> EXECUTANDO VERDE DIREITA")
                tanki.stop()
                # --- LÓGICA NOVA: GIROSCÓPIO ---
                # Defina aqui quanto você quer somar ao valor atual (ex: 90 ou -90 dependendo do seu eixo)
                angulo_desejado = 90 
                alvo_giro = gyro_rasp_z + angulo_desejado
                # -------------------------------
                motorB.dc(999)
                motorC.dc(999)
                wait(200)      
                # --- NOVO WHILE COM GIROSCÓPIO ---
                while True:
                    # Atualiza o giroscópio no meio do giro
                    data = ser.read_all()
                    retorno = sensor1.read(0)
                    fora1 = retorno[0]#esquerda REAL>>>direita
                    wait(100)
                    print(fora1)
                    if data:
                        try:
                            buffer_serial += data.decode('utf-8', 'ignore')
                            while '\n' in buffer_serial:
                                linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                                cmd = linha_cmd.strip()
                                if cmd.startswith("MPU_Z:"):
                                    try:
                                        gyro_rasp_z = float(cmd.split(":")[1].strip())
                                    except:
                                        pass
                        except:
                            pass
                    # Verifica se cruzou a linha do alvo
                    if angulo_desejado > 0 or fora1 <= 50:
                        if gyro_rasp_z >= alvo_giro or fora1 <= 50: 
                            tanki.stop()
                            pretodir = 0
                            pretoesq = 0
                            break
                    else:
                        if gyro_rasp_z <= alvo_giro or fora1 <= 50: 
                            tanki.stop()
                            pretodir = 0
                            pretoesq = 0
                            break
                # ---------------------------------
                motorB.stop()
                motorC.stop()
                previsao_camera = None
            elif previsao_camera == "esquerda" and verdeEsquerda :
                tanki.stop()
                tanki.turn(70)
                tanki.straight(-90)
                tanki.stop()
                ev3.speaker.beep(200) 
                print(">>> EXECUTANDO VERDE ESQUERDA")
                tanki.stop()
                # --- LÓGICA NOVA: GIROSCÓPIO ---
                angulo_desejado = -90 # Ajuste para o ângulo exato de esquerda do seu robô
                alvo_giro = gyro_rasp_z + angulo_desejado
                # -------------------------------
                motorB.dc(-999)
                motorC.dc(-999)
                wait(200)
                # --- NOVO WHILE COM GIROSCÓPIO ---
                while True:
                    data = ser.read_all()
                    retorno = sensor1.read(0)
                    fora2 = retorno[3]#direita  REAL>>>esquerda
                    wait(100)
                    print(fora2)
                    if data:
                        try:
                            buffer_serial += data.decode('utf-8', 'ignore')
                            while '\n' in buffer_serial:
                                linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                                cmd = linha_cmd.strip()
                                if cmd.startswith("MPU_Z:"):
                                    try:
                                        gyro_rasp_z = float(cmd.split(":")[1].strip())
                                    except:
                                        pass
                        except:
                            pass                      
                    if angulo_desejado > 0 or fora2 <= 50:
                        if gyro_rasp_z >= alvo_giro or fora2 <= 50: 
                            tanki.stop()
                            break
                    else:
                        if gyro_rasp_z <= alvo_giro or fora2 <= 50: 
                            tanki.stop()
                            break
                # ---------------------------------
                motorB.stop()
                motorC.stop()
                previsao_camera = None 
            elif previsao_camera == "beco" and verdeDireita and verdeEsquerda:
                tanki.stop()
                ev3.speaker.beep(600) 
                print(">>> EXECUTANDO BECO")
                tanki.turn(30)
                tanki.straight(190)
                tanki.stop()
                # --- LÓGICA NOVA: GIROSCÓPIO ---
                angulo_desejado = 180 # Alvo do Beco (ajuste sinal se ele girar pra direita/esquerda)
                alvo_giro = gyro_rasp_z + angulo_desejado
                # -------------------------------
                motorB.dc(999)
                motorC.dc(999)
                # --- NOVO WHILE COM GIROSCÓPIO ---
                while True:
                    data = ser.read_all()
                    if data:
                        try:
                            buffer_serial += data.decode('utf-8', 'ignore')
                            while '\n' in buffer_serial:
                                linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                                cmd = linha_cmd.strip()
                                if cmd.startswith("MPU_Z:"):
                                    try:
                                        gyro_rasp_z = float(cmd.split(":")[1].strip())
                                    except:
                                        pass
                        except:
                            pass    
                    if angulo_desejado > 0:
                        if gyro_rasp_z >= alvo_giro: 
                            tanki.stop()
                            # Zerando as variáveis originais
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break
                    else:
                        if gyro_rasp_z <= alvo_giro: 
                            tanki.stop()
                            # Zerando as variáveis originais
                            contD = 0
                            contE = 0
                            contM = 0
                            pretodir = 0
                            pretoesq = 0
                            break
                # ---------------------------------
                motorB.stop()
                motorC.stop()
                tanki.turn(-50)
                tanki.stop()
                previsao_camera = None # Limpa a memória
            elif previsao_camera == "depois":
                tanki.stop()
                ev3.speaker.beep(800, 200) 
                print(">>> SEGUINDO POR TEMPO (GAP/DEPOIS)")
                cronometro = StopWatch()
                tempo_limite = 500  # <--- DEFINE AQUI O TEMPO EM MILISSEGUNDOS (1.5s)
                while cronometro.time() < tempo_limite:
                    # É OBRIGATÓRIO ler os sensores dentro do while para o PID funcionar
                    retorno = sensor1.read(2)
                    fora1 = retorno[0]
                    meio1 = retorno[1]
                    meio2 = retorno[2]
                    fora2 = retorno[3]

                    kp = 2
                    kd = 0
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
                print(">>> TEMPO ESGOTADO: Voltando ao loop principal")
        # ==========================================
        # 9. ALL SENSORS DETECTED WHITE
        # ==========================================
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
        # ==========================================
        # 10. CONTROLO PID (SEGUIR LINHA)
        # ==========================================
        kp = 2.5 #essas 4 variaveis vao sair daqui quando ja estiver com a programação que o robo identifica inclinação
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
        # 11. BUTTON STOP IS ACTIVE
        # ==========================================
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
# ==========================================
# MESA DE CALIBRAR
# ==========================================
# Primeiro calibrar o branco e depois o preto
#calibraBranco()
#calibraPreto()
sensor()