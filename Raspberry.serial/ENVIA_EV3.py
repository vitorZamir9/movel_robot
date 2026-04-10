import serial
import time

# Abre a porta serial (ajuste caso use ttyUSB0 ou outra)
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

print("Iniciando envio pela serial...")
time.sleep(5)
try:
    while True:
        # Envia um byte único
        #ser.write(b'A')  # envia o byte 0x41 (letra A)
        
        # OU: envie uma string (com \n no final)
        ser.write(b"Mensagem da Raspberry\n")

        print("Mensagem enviada!")
        time.sleep(1)  # espera 1 segundo antes de mandar de novo

except KeyboardInterrupt:
    print("Parando envio...")
    ser.close()
