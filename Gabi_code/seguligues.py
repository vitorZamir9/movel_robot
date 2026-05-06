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

tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5 , axle_track=104.0)
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

#### initi ####
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
    global derivative
    global integral
    global motorB
    global motorC
    global gyro_rasp_z 
    global previsao_camera
    global pretodir
    global pretoesq
    
    buffer_serial = ""
    alvo = 8 # Alvo para a calibração do HSV do verde
    
    while True:
        # ==========================================
        # 1. LEITURA DOS SENSORES FÍSICOS
        # ==========================================
        retorno = sensor1.read(2)
        fora1 = retorno[0] # esquerda REAL>>>direita
        meio1 = retorno[1] # esquerda REAL>>>direita
        meio2 = retorno[2] # direita  REAL>>>esquerda
        fora2 = retorno[3] # direita  REAL>>>esquerda
        
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
        # 4. LEITURA DA CÂMARA E GIROSCÓPIO (MEMÓRIA)
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
        
        # Se algum sensor pisar no verde físico, acionamos a memória da câmara!
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

                # --- JEITO QUE TAVA ANTES (COMENTADO) ---
                # while True:
                #     retorno = sensor1.read(2)
                #     if retorno[1] <= 65: # Verifica meio1
                #         tanki.stop()
                #         break        
                # ----------------------------------------
                
                # --- NOVO WHILE COM GIROSCÓPIO ---
                while True:
                    # Atualiza o giroscópio no meio do giro
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
                    
                    # Verifica se cruzou a linha do alvo
                    if angulo_desejado > 0:
                        if gyro_rasp_z >= alvo_giro: 
                            tanki.stop()
                            break
                    else:
                        if gyro_rasp_z <= alvo_giro: 
                            tanki.stop()
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

                # --- JEITO QUE TAVA ANTES (COMENTADO) ---
                # while True:
                #     retorno = sensor1.read(2)
                #     if retorno[2] <= 65: # Verifica meio2 (direita pra esquerda)
                #         tanki.stop()
                #         break        
                # ----------------------------------------
                
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
                            break
                    else:
                        if gyro_rasp_z <= alvo_giro: 
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
                
                # --- JEITO QUE TAVA ANTES (COMENTADO) ---
                # while True:
                #     retorno = sensor1.read(2)
                #     meio1 = retorno[1]
                #     if meio1 <= 65:
                #         tanki.stop()
                #         contD = 0
                #         contE = 0
                #         contM = 0
                #         pretodir = 0
                #         pretoesq = 0
                #         break        
                # ----------------------------------------

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

                    # Teu PID específico para este trecho
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
        
#calibraBranco()
#calibraPreto()
sensor()
