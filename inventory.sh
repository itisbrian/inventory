#!/bin/bash

####################################################################
################################################ SUPREME ###############################
echo ""
echo ""
echo -e "           \e[32m███████\e[0m╗\e[32m██\e[0m╗   \e[32m██\e[0m╗\e[32m███████\e[0m╗\e[32m██\e[0m╗      \e[32m█████\e[0m╗ \e[32m██████\e[0m╗ "
echo -e "           \e[32m██\e[0m╔════╝╚\e[32m██\e[0m╗ \e[32m██\e[0m╔╝\e[32m██\e[0m╔════╝\e[32m██\e[0m║     \e[32m██\e[0m╔══\e[32m██\e[0m╗\e[32m██\e[0m╔══\e[32m██\e[0m╗"
echo -e "           \e[32m███████\e[0m╗ ╚\e[32m████\e[0m╔╝ \e[32m███████\e[0m╗\e[32m██\e[0m║     \e[32m███████\e[0m║\e[32m██████\e[0m╔╝"
echo -e "           ╚════\e[32m██\e[0m║  ╚\e[32m██\e[0m╔╝  ╚════\e[32m██\e[0m║\e[32m██\e[0m║     \e[32m██\e[0m╔══\e[32m██\e[0m║\e[32m██\e[0m╔══\e[32m██\e[0m╗"
echo -e "           \e[32m███████\e[0m║   \e[32m██\e[0m║   \e[32m███████\e[0m║\e[32m███████\e[0m╗\e[32m██\e[0m║  \e[32m██\e[0m║\e[32m██████\e[0m╔╝"
echo -e "           ╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝ "
echo " "
echo -e " \e[5m                         SYSLAB Inventory Service\e[25m"
echo -e "\e[32m                report errors to brianchen@supermicro.com \e[0m"
echo " "
echo "--------------------------------------------------------------------------------------------------------------------------------"
sleep 5

yum install -y python-pip
pip install requests

#get IPMI IP Address
#cat /root/stage2.conf | grep "SYS_DIR" > /root/flasher_config.sh
#source /root/flasher_config.sh
##################################################################################################

echo "Checking BMC IP:" 
A=`ipmitool lan print | egrep -i IP\ Address |grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'`
if [[ ${A:0:7} == "172.16." ]] ; then
	echo "${A} is on 16 network." 
elif [[ ${A:0:7} == "172.31." ]]; then
    echo "${A} is on 31 network." 
    echo "Connect BMC to 16 network and  try again." 
    echo "Exiting."
	exit 1
else
	echo "Check your BMC Connection using 'ipmitool lan print' and try again. " 
	echo "Exiting." 
	exit 1
fi

##################################################################################################
#get IPMI MAC
B=`ipmitool lan print | grep -i "MAC Address" | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'`


if [[ ${B} == "00:00:00:00:00:00" ]] ; then
	echo "IPMI MAC Address error."
	echo "IPMI MAC Address returned: 00:00:00:00:00:00"
	echo "Exiting."
	exit 1
fi
if [[ ${B} == "" ]]; then
	echo "IPMI MAC Address error."
	echo "IPMI MAC Address returned nothing."
	echo "Exiting."
	exit 1
fi
##################################################################################################
# ./amidelnx_64 SK _________  - write system product in type 1
# ./amidelnx_64 BP _________  - write system board name
# ./amidelnx_64 BS _________  - write system board serial

# KEY LIST:

# 1. BMC_IP     -compare bmc ip, if incorrect, stop
# 2. SKU        -get SKU and write
# 3. BOARD_NAME -get board name and write
# 4. BOARD_SERIAL - get board serial and write

####################
#check BMC IP is valid

bmcip_key="BMC_IP"
retbmcip_key=$(j2s ${bmcip_key}/data $(curl "http://172.16.95.158:8003/jfind/?bmc_mac=${B}&find_key=${bmcip_key}" 2>/dev/null) | grep -v "not found")
if [ -n "$retbmcip_key" ]; then
    echo "BMC IP is: ${retbmcip_key}"
    if [[ ${retbmcip_key} -ne ${A} ]] ; then
        echo "BMC IP mismatch."
        echo "Check your inputs and register the system again."
        echo "Exiting."
        exit 1
    fi   
else
    echo "Didn't find any BMC IP key."
    echo "Check your inputs and register the system again."
    echo "Exiting."
    exit 1
fi

########################
#get and write SKU
sku_key="SKU"
retsku_key=$(j2s ${sku_key}/data $(curl "http://172.16.95.158:8003/jfind/?bmc_mac=${B}&find_key=${sku_key}" 2>/dev/null) | grep -v "not found")
if [ -n "$retsku_key" ]; then
    echo "SKU is: ${retsku_key}"
    echo "Writing SKU to DMI."
    amidelnx_64_524 /SK ${retsku_key}
else
    echo "Didn't find any SKU key."
    echo "Check your inputs and register the system again."
    echo "Exiting."
    exit 1
fi
########################


boardname_key="BOARD_NAME"
retboardname_key=$(j2s ${boardname_key}/data $(curl "http://172.16.95.158:8003/jfind/?bmc_mac=${B}&find_key=${boardname_key}" 2>/dev/null) | grep -v "not found")
if [ -n "$retboardname_key" ]; then
    echo "Board Name is: ${retboardname_key}"
    echo "Writing Board Name to DMI."
    amidelnx_64_524 /BP ${retboardname_key}
else
    echo "Didn't find any Board Name key."
    echo "Check your inputs and register the system again."
    echo "Exiting."
    exit 1
fi


########################


#boardserial_key="BOARD_SERIAL"
#retboardserial_key=$(j2s ${boardserial_key}/data $(curl "http://172.16.95.158:8003/jfind/?bmc_mac=${B}&find_key=${boardserial_key}" 2>/dev/null) | grep -v "not found")
#if [ -n "$retboardserial_key" ]; then
#    echo "Board Serial is: ${retboardserial_key}"
#    echo "Writing Board Serial to DMI."
#    amidelnx_64_524 /BS ${retboardserial_key}
#else
#    echo "Didn't find any Board Serial key."
#    echo "Check your inputs and register the system again."
#    echo "Exiting."
#    exit 1
#fi


########################
dmidecode --type 1
dmidecode --type 2


#remove PXE command
#C=`ifconfig eth0 | grep -i "ether" | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'`

#curl --header "Content-Type: application/json" --request POST --data '{"unpxe":"ok","ipmi_ip":"$A","eth_mac":"$C"}' http://172.16.95.157:8005/do_web_cmd/ &>/dev/null

echo "Pushing data:"
python /usr/local/sbin/inventory.py /root

source /root/stage1.conf
C=${LNK_MAC}
python /usr/local/sbin/inventory.py unpxe ${C}

echo "End of Test."
echo "---------------------------------------------------------"










