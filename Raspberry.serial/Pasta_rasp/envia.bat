@echo off
@rem Altere o IP para o IP do Orange Pi
scp -r Raspberry.serial\newprogForev3V2.py* new@192.168.137.237:~\programacao_rasp4
@rem ssh new@192.168.137.237 "killall progEV3.py"
