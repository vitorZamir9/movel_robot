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
from servos import Servos
from segue import Segue
from green import Green
from black909 import Black909
from silver import Silver
from gapwhite import Gapwhite

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
kp_atual = 2.5
kd_atual = 0.01
ki_atual = 0.01
base_atual = 120
error = 0
powerB = 0
powerC = 0
corr = 0
old_error = 0
pretodir = 0
pretoesq = 0
integral = 0
derivative = 0
PESO_MEIO = 1.0
PESO_FORA = 2.275
parado=0
#----> drivebase <----
tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5 , axle_track=104.0) #isso funciona para movimentos do robô, alguns, mas é melhor usar o motorB e C dc
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

#------> funções classes <------
motores = Segue(motorB, motorC, PESO_FORA, PESO_MEIO)
grein = Green(tanki, motorB, motorC, sensor1, ev3, ser, motores)
blackMove = Black909(tanki, motorB, motorC, sensor1, ev3)
silver = Silver(
    tanki      = tanki,
    motorB     = motorB,
    motorC     = motorC,
    sensor1    = sensor1,
    multiplex1 = multiplex1,
    ev3        = ev3,
    ser        = ser,
    servosP    = servosP
)
gap = Gapwhite(tanki, motorB, motorC, sensor1, ev3)
# ---> VARIÁVEIS DE COMUNICAÇÃO COM A RASPBERRY <---
gyro_rasp_z = 0.0
gyro_rasp_y = 0.0
previsao_camera = None # Memória da câmara para o verde
# --->Variáveis de controle do obstáculo pela câmera<---
obstaculo_camera_pendente = False        # câmera avisou que viu obstáculo
obstaculo_camera_aguardando_linha = False  # esperando câmera dizer os lados
obstaculo_camera_resultado_linha = None  # "linha esquerda/direita/ambos/nenhum"
tempo_espera_linha = 0.0                 # para o timeout de 3s
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
    global kp_atual
    global kd_atual
    global ki_atual
    global base_atual
    global derivative
    global integral
    global motorB
    global motorC
    global gyro_rasp_z
    global gyro_rasp_y
    global previsao_camera
    global pretodir
    global pretoesq
    global multiplex1
    global parado
    global obstaculo_camera_pendente
    global obstaculo_camera_aguardando_linha
    global obstaculo_camera_resultado_linha
    global tempo_espera_linha

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
        fora1 = retorno[3] # esquerda
        meio1 = retorno[2] # esquerda
        meio2 = retorno[1] # direita
        fora2 = retorno[0] # direita

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

        alvo = 18 # Alvo para a calibração do HSV do verde
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
        # 1.2 LEITURA SERIAL — GIROSCÓPIO E CÂMERA
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

                    # --- LEITURA DO MPU ---
                    if "[MPU]" in cmd:
                        try:
                            texto_roll = cmd.split("Roll: ")[1].split("°")[0]
                            gyro_rasp_x = float(texto_roll)
                            texto_pitch = cmd.split("Pitch: ")[1].split("°")[0]
                            gyro_rasp_y = float(texto_pitch)
                            texto_yaw = cmd.split("Yaw: ")[1].split("°")[0]
                            gyro_rasp_z = float(texto_yaw)
                        except (IndexError, ValueError):
                            pass
                        continue

                    # --- OBSTÁCULO DETECTADO PELA CÂMERA ---
                    if "obstaculo detectado" in cmd:
                        print("CÂMERA: Possível obstáculo à frente!")
                        obstaculo_camera_pendente = True
                        continue

                    # --- RESPOSTA DA CÂMERA SOBRE OS LADOS DA LINHA ---
                    if "linha " in cmd and obstaculo_camera_aguardando_linha:
                        print("CÂMERA: Resultado da linha -> ", cmd)
                        obstaculo_camera_resultado_linha = cmd  # "linha esquerda/direita/ambos/nenhum"
                        obstaculo_camera_aguardando_linha = False
                        continue

                    # --- PREVISÃO DE VERDE ---
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
        # 2. VERIFICAÇÃO DE INCLINAÇÃO
        # gyro_rasp_y já está atualizado pelo módulo 1.2
        # ==========================================
        if gyro_rasp_y > 10:
            print("subindo")
            kp_atual, ki_atual, base_atual = 3.0, 0.02, 180   # subindo
        elif gyro_rasp_y < -10:
            print("descendo")
            kp_atual, ki_atual, base_atual = 2.0, 0.01, 100   # descendo
        else:
            print("plano")
            kp_atual, ki_atual, base_atual = 2.0, 0.01, 120   # plano
        # ==========================================
        # 3. VERIFICAÇÃO SE O ROBÔ ESTÁ PARADO
        # ==========================================
        # tanki.state()[3] > rotação do eixo graus por segundos
        #parado=0
        #print(tanki.state()[3],"parado: ",parado)
        if tanki.state()[3] > 60:
            # Se estiver alta a rotação dos eixos ele zera a informação que ta parado
            parado = 0
        elif tanki.state()[3] < 20:
            # Se tiver baixa a rotação dos eixos ele começa a somar
            parado = parado + 1
        elif parado > 100 :
            tanki.stop()
            ev3.speaker.beep(600)# aviso sonoro
            # Aqui coloca a lógica doq fazer quando ele estiver totalmente parado
            print("saiu do codigo pq o robo ficou travado!")
            break
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
        y=0
        if esqgray1 and mindgray1 and dirgray1 or esqgray1 and mindgray1 and dirgray1:
            wait(10)
            if esqgray1 and mindgray1 and dirgray1 or esqgray1 and mindgray1 and dirgray1 and y==0:
                tanki.stop()
                ev3.speaker.beep(900)

                # ==========================================
                # RESGATE — chama a classe Silver
                # ==========================================
                entrada_resgate_lado = silver.enter(esqgray, mindgray, dirgray, esqgray1, mindgray1, dirgray1)
                print("Entrada no resgate:", entrada_resgate_lado)

                # Pegar vítimas vivas (Silver Ball) — 2 no total
                resultado_vivas = silver.clawLife()
                print("Resultado clawLife:", resultado_vivas)

                # Pegar vítima morta (Black Ball) — 1 no total
                resultado_mortas = silver.clawDead()
                print("Resultado clawDead:", resultado_mortas)

                # Verificação dos dados de vítimas
                print("=== VERIFICAÇÃO FINAL DE VÍTIMAS ===")
                print("Total:", silver.vitimas,
                      "| Black:", silver.vitimaBLACK,
                      "| Silver:", silver.vitimaSILVER)

                # Entregar nos triângulos (se pegou todas)
                if resultado_mortas["sairdoRESGATE"] == 0:
                    silver.triangulo()

                # Sair do resgate
                silver.exit()

                # Retomar seguir linha
                tanki.settings(straight_speed=999999, straight_acceleration=999999,
                                turn_rate=999999, turn_acceleration=99999)
                continue  # volta pro loop de seguir linha
        # ==========================================
        # 6. BUMPER / CÂMERA / ULTRASSÔNICO
        # ==========================================
        # A câmera avisou que viu algo grande na frente.
        # O EV3 para, confirma pra câmera, espera o resultado dos lados, e desvia.
        if obstaculo_camera_pendente and not obstaculo_camera_aguardando_linha:
            print("EV3: Obstáculo pela câmera! Parando para confirmar...")
            tanki.stop()
            wait(100)
            # ALTERAR AQUI[] COM A IDENTIFICAÇÃO DO ULTRASSONICO
            # Confirma pra Rasp que o EV3 também percebeu e quer saber os lados
            ser.write(b"confirma obstaculo\n")
            obstaculo_camera_pendente = False
            obstaculo_camera_aguardando_linha = True
            obstaculo_camera_resultado_linha = None
            tempo_espera_linha = time.time()

        # Aguardando o resultado dos lados da linha da câmera (com timeout de 3s)
        if obstaculo_camera_aguardando_linha:
            if obstaculo_camera_resultado_linha is not None:
                resultado = obstaculo_camera_resultado_linha
                obstaculo_camera_aguardando_linha = False
                obstaculo_camera_resultado_linha = None
                print("EV3: Executando desvio com base em ", resultado)

                # -----------------------------------------------
                # LÓGICA DE DESVIO BASEADA NOS LADOS DA LINHA
                # -----------------------------------------------
                # "linha esquerda"  → linha só na esq  → desvia pela DIREITA
                # "linha direita"   → linha só na dir  → desvia pela ESQUERDA
                # "linha ambos"     → linha dos dois   → desvia pelo lado com mais espaço (usa direita como padrão)
                # "linha nenhum"    → sem linha visível → desvio padrão (esquerda)
                # -----------------------------------------------
                if resultado == "linha esquerda":
                    # Linha à esquerda → espaço livre à direita → desvia pela direita
                    print("Desvio: DIREITA (linha só na esq)")
                    tanki.turn(50)
                    tanki.straight(-150)
                    tanki.stop()
                    motorB.dc(-10)
                    motorC.dc(100)
                    wait(1000)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[3]
                        meio1 = retorno[2]
                        meio2 = retorno[1]
                        fora2 = retorno[0]
                        wait(100)
                        if fora2 < 40 or meio2 < 40:
                            tanki.stop()
                            break
                    tanki.stop()
                    wait(100)
                    tanki.turn(30)
                    tanki.stop()
                    tanki.straight(-80)
                    tanki.stop()
                    wait(100)

                elif resultado == "linha direita":
                    # Linha à direita → espaço livre à esquerda → desvia pela esquerda (comportamento original)
                    print("Desvio: ESQUERDA (linha só na dir)")
                    tanki.turn(-50)
                    tanki.straight(-150)
                    tanki.stop()
                    motorB.dc(100)
                    motorC.dc(-10)
                    wait(1000)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[3]
                        meio1 = retorno[2]
                        meio2 = retorno[1]
                        fora2 = retorno[0]
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

                elif resultado == "linha ambos":
                    # Linha dos dois lados → usa direita como padrão (mais seguro pro layout da pista)
                    print("Desvio: DIREITA padrão (linha em ambos os lados)")
                    tanki.turn(50)
                    tanki.straight(-150)
                    tanki.stop()
                    motorB.dc(-10)
                    motorC.dc(100)
                    wait(1000)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[3]
                        meio1 = retorno[2]
                        meio2 = retorno[1]
                        fora2 = retorno[0]
                        wait(100)
                        if fora2 < 40 or meio2 < 40:
                            tanki.stop()
                            break
                    tanki.stop()
                    wait(100)
                    tanki.turn(30)
                    tanki.stop()
                    tanki.straight(-80)
                    tanki.stop()
                    wait(100)

                else:
                    # "linha nenhum" ou qualquer outro caso → desvio padrão esquerda
                    print("Desvio: ESQUERDA padrão (sem linha visível)")
                    tanki.turn(-50)
                    tanki.straight(-150)
                    tanki.stop()
                    motorB.dc(100)
                    motorC.dc(-10)
                    wait(1000)
                    while True:
                        retorno = sensor1.read(2)
                        fora1 = retorno[3]
                        meio1 = retorno[2]
                        meio2 = retorno[1]
                        fora2 = retorno[0]
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

            elif (time.time() - tempo_espera_linha) > 3.0:
                # Timeout: câmera não respondeu a tempo → desvio padrão esquerda
                print("EV3: Timeout da câmera! Desvio padrão esquerda.")
                obstaculo_camera_aguardando_linha = False
                obstaculo_camera_resultado_linha = None
                tanki.turn(-50)
                tanki.straight(-150)
                tanki.stop()
                motorB.dc(100)
                motorC.dc(-10)
                wait(1000)
                while True:
                    retorno = sensor1.read(2)
                    fora1 = retorno[3]
                    meio1 = retorno[2]
                    meio2 = retorno[1]
                    fora2 = retorno[0]
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

        # --- 6B. BUMPER FÍSICO (mantido igual, funciona independente da câmera) ---
        if ChoqueESQ == 1 or ChoqueDIR == 1:
            print("Obstáculo detectado pelo bumper!")
            tanki.turn(-50)
            tanki.straight(-150)
            tanki.stop()
            motorB.dc(100)
            motorC.dc(-10)
            wait(1000)
            while True:
                retorno = sensor1.read(2)
                fora1 = retorno[3]
                meio1 = retorno[2]
                meio2 = retorno[1]
                fora2 = retorno[0]
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
        # 8. GREEN
        # A leitura serial foi movida para o módulo 1.2
        # ==========================================
        previsao_camera = grein.MoveGreen(
        H1, S1, V1, H2, S2, V2, H3, S3, V3, alvo,
        fora1, meio1, meio2, fora2, previsao_camera, cloresq, clordir,
        pretoesq, pretodir)
        # ==========================================
        # 9. ALL SENSORS DETECTED WHITE
        # ==========================================

        if fora1 > 90 and meio1 > 90 and meio2 > 90 and fora2 > 90:

            print("tudo branco")

            #motorB.dc(-70)
            #motorC.dc(70) #trás
            retorno = sensor1.read(2)
            # while True:
            #     retorno = sensor1.read(2)
            #     fora1 = retorno[3] # esquerda
            #     meio1 = retorno[2] # esquerda
            #     meio2 = retorno[1] # direita
            #     fora2 = retorno[0] # direita
            #     if fora1 < 50 or meio1 < 50 or meio2 < 50 or fora2 < 50:
            #         motorB.stop()
            #         motorC.stop()
            #         break
            if fora1 < 50 or fora2 < 50:
                pretoesq, pretodir = blackMove.blackORwhite(fora1, meio1, meio2, fora2, pretoesq, pretodir)
            #else:
            #     gap.Litleshirt(fora1, meio1, meio2, fora2, pretoesq, pretodir)
        # ==========================================
        # 10. CONTROLE PID (SEGUIR LINHA)
        # ==========================================
        motores.PID(fora1,meio1,meio2,fora2,kp_atual,kd_atual,ki_atual,base_atual)
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

def teste_Linha():
    while True:
        retorno = sensor1.read(2)

        # Leitura dos sensores para seguir linha
        fora1 = retorno[3] # esquerda
        meio1 = retorno[2] # esquerda
        meio2 = retorno[1] # direita
        fora2 = retorno[0] # direita

        print("fora1: ", fora1,"meio1: ", meio1,"meio2: ", meio2,"fora2: ", fora2)
        wait(10)

def serial():
    global ser
    while True:
        ser.write(b'\r\ bolas\r\n')
        #ser.write(b'\r\bolas\r\n')
        #ser.write(b'\r\triangulo\r\n')
        #ser.read_all()
        print(ser.read_all())
        wait(100)
# ==========================================
# MESA DE CALIBRAR
# ==========================================
# Primeiro calibrar o branco e depois o preto
#calibraBranco()
#calibraPreto()
sensor()
#teste()
#serial()