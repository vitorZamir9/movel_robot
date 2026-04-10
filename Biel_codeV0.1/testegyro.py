#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.iodevices import Ev3devSensor,I2CDevice
from pybricks.parameters import Port
from pybricks.tools import wait


ev3 = EV3Brick()

sensor= I2CDevice(Port.S1, 0x30)


for address in range(0x03, 0x77):  # endereços válidos
    try:
        device = I2CDevice(Port.S1, address)
        # Lê o registrador 0x00 (MODE1) para testar
        value = device.read(0x00, 1)[0]
        print("Encontrado endereço:", hex(address), "MODE1:", value)
    except:
        pass
