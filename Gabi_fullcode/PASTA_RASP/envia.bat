@echo off
@rem Altere o IP para o IP do Orange Pi
@rem scp -r RaspNewforEv3* new@100.88.179.72:~\programacao_rasp4
scp -r RaspNewforEv3* new@10.42.0.1:~\programacao_rasp4
@rem ssh new@100.88.179.72 "killall RaspNewforEv3.py"
@rem ssh new@10.10.42.0.1 "killall RaspNewforEv3.py"
