#!/usr/bin/env pybricks-micropython
from time import sleep
from pybricks.hubs import EV3Brick
from pybricks.iodevices import LUMPDevice, DCMotor, I2CDevice, Ev3devSensor,UARTDevice
from pybricks.parameters import Port
from pybricks.ev3devices import Motor,GyroSensor
from pybricks.tools import wait

# Configuração do EV3
ev3 = EV3Brick()
#angul0= GyroSensor(Port.S3,)
#Angul0=LUMPDevice(Port.S3)
#motorB = Motor(Port.C,gears=[12,50])
#motorC = Motor(Port.D,gears=[12,50])

#sensor1 = LUMPDevice(Port.S1)
#multiplex1 = LUMPDevice(Port.S2)
ser = UARTDevice(Port.S6, baudrate=115200, timeout=0.1)
#ARDUINO = UARTDevice(Port.S6, baudrate=9600, timeout=1)
# Modo do sensor

# primeiro 4 valores são os sensores de linha (0-3)
# depois vem os sensores de cor (RGBC) (4-7)(8-11)(12-15)
# depois temos o índice que diz a intensidade de luz do sol (16)
# depois vem a cor no sensor de cor, sendo BLACK 0, WHITE 1, RED 2, YELLOW 3, BLUE 4, GREEN 5, UNDEFINED 6 (17-19)
# depois vem os valores das cores via HSV (20-22)(23-25)(26-28)
# depois vem a posição do robo na linha (29)

# Função para ler dados do sensor


#sensor gyroscopio lego normal
#GYRO-ANG 0
#GYRO-RATE 1
#GYRO-FAS 2
#GYRO-G&A 3
#GYRO-CAL 4
#TILT-RATE 5
#TILT-ANG 6

#multiplex ultrasonicos
#esquerda 0
#nada 1
#direita 2
#frente 3
def serial():
    global ser
    while True:
        ser.write(b'\r\linha\r\n')
        ser.read_all()
        print(ser.read_all)
        wait(100)
def gira():
    while True:
        #tudo positivo giro para a direita
        #tudo negativo giro para a esquerda
        #motorB positivo e motorC negativo ele anda pra frente
        #motorB negativo e motorC positivo ele anda pra trás
        #motorB.dc(999)
        #motorC.dc(999)
        print('executado')
        #motorB.run(999)
        #motorC.run(999)
        #print(multiplex1.read(0))
        
       
       
        
def sensor():
    global sensor1
    while True:
        retorno = sensor1.read(2)
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
        fora1 = retorno[0]
        meio1 = retorno[1]
        meio2 = retorno[2]
        fora2 = retorno[3]
        cloresq = retorno[17]
        clormind = retorno[18]
        clordir = retorno[19]
        #print(retorno)
        print("sensorD:","RGBC>>",R1,G1,B1,C1,"<<RGBC","sensorM:","RGBC>>",R3,G3,B3,C3,"<<RGBC","sensorE:","RGBC>>",R2,G2,B2,C2,"<<RGBC",fora1,meio1,meio2,fora2,"undefined:",cloresq,clormind,clordir)
        alvo= 5
        if H1 >=(98-alvo) and H1 <=(105+alvo) and S1 >=(50-alvo) and S1 <=(65+alvo) and V1 >=(45-alvo) and V1 <=(75+alvo):
            wait(100)
            if H1 >=(98-alvo) and H1 <=(138+alvo) and S1 >=(50-alvo) and S1 <=(70+alvo) and V1 >=(45-alvo) and V1 <=(75+alvo):
                ev3.speaker.beep(300, 100)
       
        if H2 >=(98-alvo) and H2 <=(105+alvo) and S2 >=(50-alvo) and S2 <=(65+alvo) and V2 >=(45-alvo) and V2 <=(75+alvo):
            wait(100)
            if H2 >=(98-alvo) and H2 <=(138+alvo) and S2 >=(50-alvo) and S2 <=(70+alvo) and V2 >=(45-alvo) and V2 <=(75+alvo):
                ev3.speaker.beep(1000, 100)
        wait(15)
# Início do programa
#sensor()
#gira()
serial()
