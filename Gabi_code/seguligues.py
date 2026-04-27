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

####################################################################################################
ev3= EV3Brick()
sensor1 = LUMPDevice(Port.S1)
motorB = Motor(Port.B,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
#ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)
#serialservo = UARTDevice(Port.S5, baudrate=115200, timeout=0.1)

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
PESO_MEIO = 0.95
PESO_FORA = 2.85
contE = 0
contD = 0

# ---> VARIÁVEL PARA GUARDAR O GIROSCÓPIO DA RASPBERRY <---
gyro_rasp_z = 0.0 

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
    global gyro_rasp_z # Puxando a variável global do giroscópio
    
    # Manda a Raspberry Pi entrar no modo de linha
    #ser.write(b'linha\r\n')
    
    # 1. CRIE O BUFFER VAZIO ANTES DO LOOP
    buffer_serial = ""
    
    while True:
       # ==========================================
        # LÓGICA DE SEGUIR LINHA (PID DINÂMICO)
        # ==========================================
        retorno = sensor1.read(2)
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
       
        # VALORES DE ALTA PERFORMANCE (Ajuste o Kd e o K_v na pista!)
        kp = 13
        kd = 80 
        ki = 0      # Zere isso para retas de alta velocidade
        
        velocidade_maxima = 700  # Sua base antiga era 50 * 10

        esquerda = (meio1 * PESO_MEIO) + (fora1 * PESO_FORA)
        direita = (meio2 * PESO_MEIO) + (fora2 * PESO_FORA)
        error = (direita - esquerda) * 0.5

        derivative = error - old_error
        corr = (error * (kp * (-1))) + (derivative * kd)
    
       # --- O FREIO INTELIGENTE COM ZONA MORTA ---
        K_v = 2.0         # Aumentei o freio para ser mais agressivo quando precisar
        ZONA_MORTA = 20   # Erros abaixo de 20 são considerados "reta"
        
        # O freio só calcula o que passar da Zona Morta
        if abs(error) > ZONA_MORTA:
            # Subtrai da base apenas a intensidade da curva que excede a zona morta
            frenagem = (abs(error) - ZONA_MORTA) * K_v
            base_dinamica = velocidade_maxima - frenagem
        else:
            # Na reta (erro pequeno), velocidade total sem restrições!
            base_dinamica = velocidade_maxima
        
        # Trava de segurança para não parar na curva
        base_dinamica = max(base_dinamica, 100) 

        # Aplica a força de forma SIMÉTRICA
        powerB = base_dinamica - corr
        powerC = -base_dinamica - corr
        
        # ==========================================
        # FALTAVA ISSO AQUI: Trava de limites e envio pro motor!
        # ==========================================
        powerB = max(min(int(powerB), 900), -900)
        powerC = max(min(int(powerC), 900), -900)

        motorB.dc(powerB)
        motorC.dc(powerC)
        # ==========================================

        old_error = error
        
        # ==========================================
        # LEITURA SERIAL NÃO-BLOQUEANTE DA CÂMERA E GIROSCÓPIO
        # ==========================================
        data = 1#ser.read_all()
        
        if data:
            try:
                buffer_serial += data.decode('utf-8', 'ignore')
                
                while '\n' in buffer_serial:
                    linha_cmd, buffer_serial = buffer_serial.split('\n', 1)
                    cmd = linha_cmd.strip()
                    
                    if not cmd or cmd == "frente":
                        continue
                    
                    # ==========================================
                    # LEITURA DO GIROSCÓPIO
                    # ==========================================
                    if cmd.startswith("MPU_Z:"):
                        try:
                            # Corta a string "MPU_Z: 45.2" e guarda só o número na variável
                            gyro_rasp_z = float(cmd.split(":")[1].strip())
                        except:
                            pass
                        continue # Pula os prints e beeps pra não poluir, volta pro loop

                    print("LIDO DA CAMERA:", cmd)

                    # ==========================================
                    # LÓGICAS DO VERDE COM BEEPS E AÇÕES
                    # ==========================================
                    if "1 verde esquerda antes" in cmd:
                        ev3.speaker.beep(200) 
                        print("Ação: Virar 90 graus para ESQUERDA")
                        
                    elif "1 verde direita antes" in cmd:
                        ev3.speaker.beep(400) 
                        print("Ação: Virar 90 graus para DIREITA")
                        
                    elif "dois verdes antes" in cmd:
                        ev3.speaker.beep(600) 
                        print("Ação: Beco (Meia volta)")
                        tanki.stop()
                        motorB.dc(999)
                        motorC.dc(999)
                        wait(1200)
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
                        
                    elif "depois da linha preta" in cmd:
                        ev3.speaker.beep(800, 200)
                        print("Ação: Encruzilhada com Gap")
                        
            except ValueError:
                pass
            except Exception as e:
                print("Erro inesperado na serial:", e)
                pass

#calibraBranco()
#calibraPreto()
sensor()
