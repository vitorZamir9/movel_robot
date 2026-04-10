
#!/bin/bash
rm /dev/tty_ev3-ports\:in5
rm /dev/tty_ev3-ports\:in6
ln -s /dev/ttyUSB0 /dev/tty_ev3-ports\:in5
ln -s /dev/ttyUSB1 /dev/tty_ev3-ports\:in6

