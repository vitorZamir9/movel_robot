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
from talkingserial import TalkingSerial as ts

####################################################################################################
ev3= EV3Brick()
sensor1 = LUMPDevice(Port.S1)
multiplex1 = LUMPDevice(Port.S2)
Gyroangle = GyroSensor(Port.S3)
motorB = Motor(Port.B,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
motorC = Motor(Port.D,gears=[12,25],positive_direction=Direction.COUNTERCLOCKWISE)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)
ts = ts(ser,False)
serialservo = UARTDevice(Port.S5, baudrate=115200, timeout=0.1)
servosMove= Servos(serialservo,True)

# VARIAVEIS / IMPORT
kp_atual = 1.8
kd_atual = 0.5
ki_atual = 0.01
base_atual = 110

kp_padrao = 1.8
kd_padrao = 0.5
ki_padrao = 0.01
base_padrao = 110

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
PESO_FORA = 2.0
parado=0
resgate_uma_vez = 1
botao_STOPING = 0
triangulo = 0

#----> drivebase <----
tanki = DriveBase(motorB, motorC, wheel_diameter= 55.5 , axle_track=104.0) #isso funciona para movimentos do robô, alguns, mas é melhor usar o motorB e C dc
tanki.settings(straight_speed=999999, straight_acceleration=999999, turn_rate=999999, turn_acceleration=99999)

#------> funções classes <------
motores = Segue(motorB, motorC, PESO_FORA, PESO_MEIO)
grein = Green(tanki, motorB, motorC, sensor1, ev3, ser, motores)
blackMove = Black909(tanki, motorB, motorC, sensor1, ev3, ts)
silver = Silver(
    tanki      = tanki,
    motorB     = motorB,
    motorC     = motorC,
    sensor1    = sensor1,
    multiplex1 = multiplex1,
    ev3        = ev3,
    ser        = ser,
    servosP    = servosMove,
)
gap = Gapwhite(tanki, motorB, motorC, sensor1, ev3)
# ---> VARIÁVEIS DE COMUNICAÇÃO COM A RASPBERRY <---
gyro_rasp_z = 0.0 
gyro_rasp_y = 0.0
previsao_camera = None # Memória da câmara para o verde
ts.enviar("reset_mpu0")
Gyroangle.reset_angle(0)
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
    ev3.speaker.beep()

def calibraPreto(): #tudo preto, verifique para ver se está certo mesmo
    retorno = sensor1.read(4)
    wait(100)
    while retorno[0] == 0:
        retorno = sensor1.read(4)
        wait(100)
    print("Calibrado Preto")
    ev3.speaker.beep()


#################################################################
# DEF de atualizar informações do sensor
#################################################################
def atualiza_sensor1():
    global sensor1
    global R1, R2, R3
    global G1, G2, G3
    global B1, B2, B3, alvo
    global cloresq, clormind, clordir
    global fora1, meio1, meio2, fora2
    global H1, H2, H3
    global S1, S2, S3
    global V1, V2, V3
    global posicao
    global C1, C2, C3
    global triangulo
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
    alvo = 10 # Alvo para a calibração do HSV do verde

def atualiza_multiplex1():
    global multiplex1
    global ultra1, ultra2, ultrad3, ultra4
    global botao_stop, botao_parar
    global ChoqueESQ, ChoqueDIR
    # ==========================================
    # 1.1 LEITURA DO SENSOR MULTIPLEX
    # ==========================================
    retorno1= multiplex1.read(0)
    # Leitura dos sensores ultrasônicos
    ultra1  = retorno1[0] # frente
    ultra2  = retorno1[1] # direita
    ultrad3 = retorno1[2] # vitima
    ultra4  = retorno1[3] # esquerda
    if ultra1 or ultra2 or ultra4 or ultrad3 == -1:
        #print("não esta identificando os ultra")
        if ultra1 == -1:
            print("ultra1")
            return -1
        if ultra2 == -1:
            print("ultra2")
            return -1
        if ultrad3 == -1:
            print("ultra3")
            return -1
        if ultra4 == -1:
            print("ultra4")
            return -1
    # Leitura dos botões para função pro robô
    botao_stop  = retorno1[6]
    botao_parar = retorno1[5]
    # Leitura dos botôes que servem pro parachoque
    ChoqueESQ = retorno1[4]
    ChoqueDIR = retorno1[7]

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
    global resgate_uma_vez
    global gyro_rasp_z 
    global gyro_rasp_y
    global Gyroangle
    global previsao_camera
    global pretodir
    global pretoesq
    global multiplex1
    global parado
    global obstaculo_camera_pendente
    global obstaculo_camera_aguardando_linha
    global obstaculo_camera_resultado_linha
    global tempo_espera_linha
    global ultra1
    global ultra2
    global ultrad3
    global ultra4
    global R1, R2, R3
    global G1, G2, G3
    global B1, B2, B3, alvo
    global H1, H2, H3
    global S1, S2, S3
    global V1, V2, V3
    global posicao
    global C1, C2, C3
    global esqgray1, mindgray1, dirgray1
    global esqgray, mindgray, dirgray
    global rgb, clear
    global cloresq, clormind, clordir
    global fora1, meio1, meio2, fora2
    global botao_stop, botao_parar, botao_STOPING
    global ChoqueESQ, ChoqueDIR
    buffer_serial = ""
    global botaoVery
    global triangulo
    global servosMove
    global ts
    global ser
    global ev3
    global tanki
    global kp_padrao, kd_padrao, ki_padrao, base_padrao
    
    while True:
        
        # ==========================================
        # 0.0 Ligar tela-desafio surpresa/Enviar msg rasp
        # ==========================================
        
        #ts.set_modo("nadapross") 
        ts.set_modo("linha_gap")
        #ser.write(b'nadapross\r\n') 
        #ser.write(b'OFF\r\n')
        # ==========================================
        # 1.0 LEITURA DO SENSOR DE COR
        # ==========================================
        atualiza_sensor1()
        # ==========================================
        # 1.1 LEITURA DO SENSOR MULTIPLEX
        # ==========================================
        atualiza_multiplex1()
        if atualiza_multiplex1() == -1:
            print("problema em algum ultrassônico, verifique a conexão")
        retorno1= multiplex1.read(0)
        ChoqueESQ = retorno1[4]
        ChoqueDIR = retorno1[7]
        botao_stop  = retorno1[6]
        botao_parar = retorno1[5]
        botaoVery = False
        # ==========================================
        # 1.2 LEITURA SERIAL — GIROSCÓPIO E CÂMERA
        # ==========================================
        ev = ts.drenar_principal()

        # gyro vem direto dos atributoss
        gyro_rasp_y = ts.pitch  # pitch (rampa)
        gyro_rasp_z = ts.yaw  # yaw
        Afagem = Gyroangle.angle() # pitch negativo pra cima
        #print("Afagem: ", Afagem)

        # eventos do ciclo
        if ev["obstaculo_pendente"]:
            ts.confirmar_obstaculo()  # já seta aguardando_linha = True internamente
        if ev["resultado_linha"]:
            obstaculo_camera_resultado_linha = ev["resultado_linha"]
        if ev["previsao_camera"]:
            previsao_camera = ev["previsao_camera"]
        # ==========================================
        # 1.3 MOVIMENTO SERVOS
        # ==========================================
        servosMove.desativa(1) # Angular
        servosMove.desativa(2) # Pinça esquerda
        servosMove.desativa(3) # Pinça direita
        servosMove.desativa(4) # Caçamba
        servosMove.move(1, 0)  # posição fechada servo angulo garra
        servosMove.move(2, 0)  # aberto pinça esquerda
        servosMove.move(3, 60) # aberto pinça direita
        servosMove.move(4, 40) # posição fechada servo caçamba
        # ==========================================
        # 2. VERIFICAÇÃO DE INCLINAÇÃO
        # gyro_rasp_y já está atualizado pelo módulo 1.2
        # ==========================================
        #print("RAW pitch:", ts.gyro_y, "| raw yaw:", ts.gyro_z)
        if Afagem > 19 and 0 == 0: #pra cima
            ev3.speaker.beep(100)
            print("Afagem:",Afagem,"Parado:",parado,"Rotational speed:",tanki.state()[3],"Subindo")
            kp_atual, kd_atual, base_atual = 1.0, 0.7, 190   # subindo
            servosMove.desativa(1) # Angular
            servosMove.desativa(2) # Pinça esquerda
            servosMove.desativa(3) # Pinça direita
            servosMove.desativa(4) # Caçamba
            servosMove.move(2, 60)  # aberto pinça esquerda
            servosMove.move(3, 0) # aberto pinça direita
            # servosMove.move(1, 60)  # posição fechada servo angulo garra
            # tanki.turn(-20)
            tanki.stop()
            wait(100)
            tanki.stop()
            while True:
                # ==========================================
                # 1.0 LEITURA DO SENSOR DE COR
                # ==========================================
                retorno = sensor1.read(2)
                # Leitura dos sensores para seguir linha
                fora1 = retorno[3] # esquerda 
                meio1 = retorno[2] # esquerda 
                meio2 = retorno[1] # direita  
                fora2 = retorno[0] # direita  
                atualiza_sensor1()
                #############################################
                #atualizar giro
                ev = ts.drenar_principal()
                # gyro vem direto dos atributoss
                gyro_rasp_y = ts.pitch  # pitch (rampa)
                gyro_rasp_z = ts.yaw  # yaw
                Afagem = Gyroangle.angle() # pitch negativo pra cima
                print("Afagem: ", Afagem)

                #verificar angulo
                if Afagem <= 9: #desceu
                    print("DESCEUUUUUUUUUUUUUUUUUu")
                    tanki.stop()
                    ev3.speaker.beep(500,80)
                    Afagem = Gyroangle.angle() # pitch negativo pra cima
                    if Afagem <= -13:
                        tanki.turn(-20)
                        tanki.stop()
                        ev3.speaker.beep(1000,80)
                    break
                elif Afagem >= 1:
                    motores.PID(fora1,meio1,meio2,fora2,kp_atual,kd_atual,ki_atual,base_atual)
                    #servosMove.move(1, 0)  # posição fechada servo angulo garra   
            tanki.stop()
        elif Afagem <= -13 and 0==0: 
            ev3.speaker.beep(1000)
            print("Afagem:",Afagem,"Parado:",parado,"Rotational speed:",tanki.state()[3],"Descendo")
            kp_atual, kd_atual, base_atual = 2.0, 0.1, 80   # descendo

        else:
            print("Afagem:",Afagem,"Parado:",parado,"Rotational speed:",tanki.state()[3],"Plano","Enconders:",motorB.angle(),motorC.angle())
            kp_atual, ki_atual, kd_atual, base_atual = kp_padrao, ki_padrao, kd_padrao, base_padrao   # plano
        # ==========================================
        # 3. VERIFICAÇÃO SE O ROBÔ ESTÁ PARADO
        # ==========================================
        # tanki.state()[3] > rotação do eixo graus por segundos
        #parado=0
        #print(tanki.state()[3],"parado: ",parado)
        # verificar agr com o motor.angle()
        if tanki.state()[3] > 60:
            # Se estiver alta a rotação dos eixos ele zera a informação que ta parado
            parado = 0
        elif tanki.state()[3] < 20:
            # Se tiver baixa a rotação dos eixos ele começa a somar
            parado = parado + 1
        if parado > 70 :
            tanki.stop()
            ev3.speaker.beep(600)# aviso sonoro
            # Aqui coloca a lógica doq fazer quando ele estiver totalmente parado
            print("saiu do codigo pq o robo ficou travado!")
            motorB.dc(100)
            motorC.dc(-100)
            wait(1000)
            motorB.dc(-100)
            motorC.dc(100)
            motorB.stop()
            motorC.stop()
            tanki.stop()
            ev3.speaker.beep()
            parado=0
            continue
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
        # triangulo = 0
        # clear = 70
        # rgb=85
        # esqgray = R1 > rgb and G1 > rgb and B1 > rgb and C1 > clear 
        # mindgray = R3 > rgb and G3 > rgb and B3 > rgb and C3 > clear #prata reflectivo
        # dirgray = R2 > rgb and G2 > rgb and B2 > rgb and C2 > clear 
        
        # blue = 45
        # esqgray1 = B1 > blue and B1 < 70 and C1 > 21 and C1 < 30 and cloresq == 6
        # mindgray1 = B3 > blue and B3 < 70 and C3 > 21 and C3 < 30 and clormind == 6 #prata não reflectivo
        # dirgray1 = B2 > blue and B2 < 70 and C2> 21 and C2 < 30 and clordir == 6
        # y=1
        # # ^^^^^^se essa variavel ficar 0 ela vai fazer com que o robo ignore o seguidor e va direto pro resgate
        # if (esqgray1 or mindgray1 or dirgray1 or y==0 and resgate_uma_vez == 0) and triangulo == 999:
        #     print("prata")
        #     wait(10)
        #     if esqgray1 and mindgray1 and dirgray1 or y==0:
        #         tanki.stop()
        #         ev3.speaker.beep(900)
        #         # ==========================================
        #         # RESGATE — chama a classe Silver
        #         # ==========================================
        #         entrada_resgate_lado = silver.enter(esqgray1, mindgray1, dirgray1)
        #         print("Entrada no resgate:", entrada_resgate_lado)
        #         if entrada_resgate_lado is None:
        #             print("Erro na entrada do resgate. Retomando seguir linha.")
        #             continue  # volta pro loop de seguir linha
                
        #         silver.ir_pro_meio(entrada_resgate_lado)    

        #         # Pegar vítimas vivas (Silver Ball) — 2 no total
        #         resultado_vivas = silver.clawLife()
        #         print("Resultado clawLife:", resultado_vivas)
        #         if resultado_vivas == "sairdoRESGATE" :
        #             silver.exit(esqgray1, mindgray1, dirgray1)
        #             continue
        #         elif resultado_vivas == "Triangulo_verde":
        #             triangulo = 1
        #             silver.triangulo("Triangulo_verde")
        #             continue

        #         # Pegar vítima morta (Black Ball) — 1 no total
        #         if triangulo == 0 : resultado_mortas = silver.clawDead()
        #         print("Resultado clawDead:", resultado_mortas)
        #         if resultado_mortas == "sairdoRESGATE":
        #             silver.exit(esqgray1, mindgray1, dirgray1)
        #             continue
        #         elif resultado_mortas == "Triangulo_vermelho":
        #             silver.triangulo("Triangulo_vermelho")
        #             continue
 
        #         # Verificação dos dados de vítimas
        #         print("=== VERIFICAÇÃO FINAL DE VÍTIMAS ===")
        #         print("Total:", silver.vitimas,
        #               "| Black:", silver.vitimaBLACK,
        #               "| Silver:", silver.vitimaSILVER)
 
        #         # Entregar nos triângulos (se pegou todas)
        #         if resultado_mortas["sairdoRESGATE"] == 0 and triangulo == 0:
        #             silver.triangulo("todos")
        #         elif resultado_mortas["Triangulo_verde"]:
        #             silver.triangulo("Triangulo_verde")
        #         elif resultado_mortas["Triangulo_vermelho"]:
        #             silver.triangulo("Triangulo_vermelho")
 
        #         # Sair do resgate
        #         silver.exit(esqgray1, mindgray1, dirgray1)
        #         resgate_uma_vez = 1
        #         # Retomar seguir linha
        #         tanki.settings(straight_speed=999999, straight_acceleration=999999,
        #                         turn_rate=999999, turn_acceleration=99999)
        #         continue  # volta pro loop de seguir linha
        # ==========================================
        # 6. BUMPER / CÂMERA / ULTRASSÔNICO
        # ==========================================
        # --- 6B. BUMPER FÍSICO ---
        if ChoqueESQ == 1 or ChoqueDIR == 1:
            print("Obstáculo detectado pelo bumper!")
            tanki.turn(-50)
            tanki.straight(-150)
            tanki.stop()
            motorB.dc(100)
            motorC.dc(-10)
            wait(1000)
            while True:
                atualiza_sensor1()
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
        if fora1 <= 10  :
            pretoesq = 100
            pretodir = 0
        if fora2 <= 10 :
            pretodir = 100
            pretoesq = 0
        else:
             if pretoesq > 0:
                pretoesq -= 1
             if pretodir > 0:
                pretodir -= 1
        # ==========================================
        # 8. GREEN
        # ==========================================
        # previsao_camera = grein.MoveGreen(
        # H1, S1, V1, H2, S2, V2, H3, S3, V3, alvo, 
        # fora1, meio1, meio2, fora2, previsao_camera, cloresq, clordir,
        # pretoesq, pretodir)
        # ==========================================
        # 9. ALL SENSORS DETECTED WHITE
        #==========================================
        if fora1 > 80 and meio1 > 80 and meio2 > 80 and fora2 > 80 and clordir == 1 and cloresq == 1 and clormind == 1:
            ev3.speaker.beep(100)
            print("vendo alguma curva preta ou  gap")
            pretoesq, pretodir = blackMove.blackORwhite(fora1, meio1, meio2, fora2, pretoesq, pretodir)
        # ==========================================
        # 10. CONTROLE PID (SEGUIR LINHA)
        # ==========================================
        motores.PID(fora1,meio1,meio2,fora2,kp_atual,kd_atual,ki_atual,base_atual)
        # ==========================================
        #=============================
        # 11. BUTTON STOP IS ACTIVE
        #=============================
        if botao_parar > 0:
            print("parar programação!")
            motorB.stop()
            motorC.stop()
            ev3.speaker.beep(500,1000)
            sys.exit()
        if botao_stop == 1 and botaoVery == False:
            retorno1= multiplex1.read(0)
            botao_stop  = retorno1[6]
            botao_parar = retorno1[5]
            botaoVery = True
            print("parado")
            motorB.stop()
            motorC.stop()
            # ts.enviar("reset_mpu0")
            wait(100)
            while True:
                retorno1= multiplex1.read(0)
                botao_stop  = retorno1[6]
                botao_parar = retorno1[5]
                print(botao_stop, botaoVery)
                contD = 0
                contE = 0
                contM = 0
                pretodir = 0
                pretoesq = 0
                if botao_stop == 1:
                    botaoVery = False
                    retorno1= multiplex1.read(0)
                    botao_stop  = retorno1[6]
                    botao_parar = retorno1[5]
                    print(botao_stop, botaoVery)
                    wait(100)
                    ev3.speaker.beep()
                    break
                # Afagem = Gyroangle.angle() # pitch negativo pra cima
                # Afagem.reset_angle(0)
                motorB.stop()
                motorC.stop() 
                wait(100)
            botaoVery = False
       
        

def teste_Linha():
    while True:
        retorno = sensor1.read(2)
        
        posicao = (retorno[29]*2)
        # Leitura RGBC dos sensores
        R1, R3, R2 = (retorno[4]), (retorno[8]), (retorno[12])
        G1, G3, G2 = (retorno[5]), (retorno[9]), (retorno[13])
        B1, B3, B2 = (retorno[6]), (retorno[10]), (retorno[14])
        C1, C3, C2 = (retorno[7]), (retorno[11]), (retorno[15])

        # Leitura HSV para o verde
        H1, H3, H2 = (retorno[20]*2), (retorno[23]*2), (retorno[26]*2)
        S1, S3, S2 = (retorno[21]*2), (retorno[24]*2), (retorno[27]*2)
        V1, V3, V2 = (retorno[22]*2), (retorno[25]*2), (retorno[28]*2)

        # Leitura unitária dos sensores de cor
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
       
        clear = 40
        rgb=80
        esqgray = R1 > rgb and G1 > rgb and B1 > rgb and C1 > clear and C1 < (clear + 5)
        mindgray = R3 > rgb and G3 > rgb and B3 > rgb and C3 > clear and C3 < (clear + 5) #prata reflectivo
        dirgray = R2 > rgb and G2 > rgb and B2 > rgb and C2 > clear and C2 < (clear + 5)
        
        esqgray1 = B1 > 45 and B1 < 70 and C1 > 21 and C1 < 30 and cloresq == 6
        mindgray1 = B3 > 45 and B3 < 70 and C3 > 21 and C3 < 30 and clormind == 6 #calibrar o prata não reflectivo
        dirgray1 = B2 > 45 and B2 < 70 and C2> 21 and C2 < 30 and clordir == 6

        print("sensor esquerdo Reflectivo", "R1: ", R1,"G1: ", G1,"B1: ", B1,"C1:  ", C1)
        print("sensor medio Reflectivo   ",    "R3: ", R3,"G3: ", G3,"B3: ", B3,"C3:  ", C3)
        print("sensor direito Reflectivo ",  "R2: ", R2,"G2: ", G2,"B2: ", B2,"C2:  ", C2)
        print("poscao: ", posicao)

        #print("sensor esquerdo não Reflectivo","B1: ", B1,"G1: ", G1,"B1: ", B1,"C1: ", C1, "cloresq: ", cloresq)
        #print("sensor medio não Reflectivo",   "B3: ", B3,"G3: ", G3,"B3: ", B3,"C3: ", C3, "clormind: ", clormind)
        #print("sensor direito não Reflectivo", "B2: ", B2,"G2: ", G2,"B2: ", B2,"C2: ", C2, "clordir: ", clordir)
        if esqgray1 and mindgray1 and dirgray1  :
            wait(10)
            if esqgray1 and mindgray1 and dirgray1:
                print("prata não reflectivo detectado!")
                ev3.speaker.beep(500)
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

def servis():
    servosMove.desativa(1) # angulo
    servosMove.desativa(2) # esquerda
    servosMove.desativa(3) # direita
    servosMove.desativa(4) # despejo
    wait(00)
    #servosMove.move(2, 0)# aberto
    #servosMove.move(3, 60)# aberto
    #wait(1000)
    #servosMove.move(2, 60)
    #servosMove.move(3, 0)
    #wait(1000)
    servosMove.move(4, 0) # mortas
    wait(1000)
    servosMove.move(4, 60) 
    wait(1000)
    servosMove.move(4, 30) 
    
def seguidores():
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
    global ultra1
    global ultra2
    global ultrad3
    global ultra4
    global R1, R2, R3
    global G1, G2, G3
    global B1, B2, B3
    global esqgray1, mindgray1, dirgray1
    global esqgray, mindgray, dirgray
    global rgb, clear
    global cloresq, clormind, clordir
    global fora1, meio1, meio2, fora2
    while True :
        retorno = sensor1.read(2)

        # Leitura dos sensores para seguir linha
        fora1 = retorno[3] # esquerda 
        meio1 = retorno[2] # esquerda 
        meio2 = retorno[1] # direita  
        fora2 = retorno[0] # direita  

        motores.PID(fora1,meio1,meio2,fora2,kp_atual,kd_atual,ki_atual,base_atual)

def Angulo():
    global Gyroangle
    while True:
        Afagem = Gyroangle.angle()
        print("Afagem: ", Afagem)
        # wait(100)

def calibração():
    print("Pronto para a calibração!!")
    ev3.speaker.beep(500, 1000)
    wait(100)
    ev3.speaker.beep(1000)
    while True:
        # ==========================================
        # 1.1 LEITURA DO SENSOR MULTIPLEX
        # ==========================================
        atualiza_multiplex1()
        if atualiza_multiplex1() == -1:
            print("problema em algum ultrassônico, verifique a conexão")
        retorno1= multiplex1.read(0)
        ChoqueESQ = retorno1[4]
        ChoqueDIR = retorno1[7]
        botao_stop  = retorno1[6]
        botao_parar = retorno1[5]
        if botao_stop == 1:
            wait(100)
            calibraBranco()
        if botao_parar == 1:
            wait(100)
            calibraPreto()
        wait(100)
# ==========================================
# MESA DE CALIBRAR
# ==========================================
# Primeiro calibrar o branco e depois o preto
#calibração()
sensor()
#Angulo()
#teste_Linha()
#serial()
#servis()
#seguidores()