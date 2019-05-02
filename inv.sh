#!/bin/bash


IP=westworld.bnet

echo " " |tee -a /dev/tty0

wget "http://${IP}/inv/getty-inv@.service" -O "/lib/systemd/system/getty-inv@.service" &> /dev/null
if [ $? -ne 0 ]
 then
	echo "Failed to acquire getty service for Inventory Service." | tee /dev/tty0
	return 1
	exit 1
fi
echo "Inventory Service installed." | tee /dev/tty0

############################################################################################################################
/usr/bin/systemctl daemon-reload
if [ $? -ne 0 ]
 then
	echo "Failed to reload systemd." | tee /dev/tty0
	return 2
#	exit 2
fi
echo "Systemd reload finished." | tee /dev/tty0
########################################################################################################################
wget "http://${IP}/inv/packages/j2s" -O "/usr/local/sbin/j2s" &> /dev/null
if [ $? -ne 0 ]
then
	echo "Failed to acquire j2s." 
	echo "Exiting." 
    exit 1
fi
chmod +x /usr/local/sbin/j2s
echo "J2s installed." 

wget "http://${IP}/inv/packages/amidelnx_64_524" -O "/usr/local/sbin/amidelnx_64_524" &> /dev/null
if [ $? -ne 0 ]
then
	echo "Failed to acquire AMI Edit." 
	echo "Exiting." 
    exit 1
fi
chmod +x /usr/local/sbin/amidelnx_64_524
echo "AMI Edit installed." 





########################################################################################################################

wget "http://${IP}/inv/inventory.sh" -O "/usr/local/sbin/startinv.sh" &> /dev/null
if [ $? -ne 0 ]
 then
	echo "Failed to get Inventory Script." | tee /dev/tty0
	echo "Exiting." 
    exit 1
fi
chmod +x /usr/local/sbin/startinv.sh

echo "Inventory Script installed." | tee /dev/tty0

wget "http://${IP}/inv/inventory.py" -O "/usr/local/sbin/inventory.py" &> /dev/null
if [ $? -ne 0 ]
 then
	echo "Failed to get Inventory Script 2." | tee /dev/tty0
	echo "Exiting." 
    exit 1
fi
chmod +x /usr/local/sbin/inventory.py

echo "Inventory Script 2 installed." | tee /dev/tty0



########################################################################################################################
/usr/bin/systemctl stop getty-auto-cburn@tty2.service
/usr/bin/systemctl stop getty-auto-root@tty2.service
/usr/bin/systemctl stop getty@tty2.service
echo " " |tee -a /dev/tty0
echo -e "\e[32mStarting Inventory Script. View Progress in Alt+F2\e[0m" |tee -a /dev/tty0
echo " " |tee -a /dev/tty0
/usr/bin/systemctl start getty-inv@tty2.service
