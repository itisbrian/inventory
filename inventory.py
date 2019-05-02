#!/bin/python
# -*- coding: utf-8 -*-
# Kage Park
#
# Inventory Agent
# 2019/01/07
#
from __future__ import print_function
import requests
import json
import subprocess
import re,os
import ast
from datetime import datetime
import pprint
import socket, struct


version='0.1.1'
DJ_ADDR='172.16.95.158'
#DJ_ADDR='172.31.44.40'
DJ_PORT=8003
log_file=None
now=datetime.now().strftime('%s')

##################################################
# Came from kmisc.py
def str2url(string):
    return string.replace('/','%2F').replace(':','%3A').replace('=','%3D').replace(' ','+')

def is_ipv4(ipadd=None):
    if ipadd is None or type(ipadd) is not str or len(ipadd) == 0:
        return False
    ipa = ipadd.split(".")
    if len(ipa) != 4:
        return False
    for ip in ipa:
        if not ip.isdigit():
            return False
        if not 0 <= int(ip) <= 255:
            return False
    return True

def ip2num(ip):
    if is_ipv4(ip):
        return struct.unpack("!L", socket.inet_aton(ip))[0]
    return False

def ip_in_range(ip,start,end):
    ip=ip2num(ip)
    start=ip2num(start)
    end=ip2num(end)
    if start <= ip and ip <= end:
        return True
    return False
##################################################

##################################################
# Came from SM_Auto_FnD.py
def unset_cburn_auto_pxe(mac=None,ipmi_ip=None):
    if mac is None:
        os._exit(1)
    data=None
    if ip_in_range(ipmi_ip,'10.141.160.1','10.141.191.254'):
        eth_mac_str=mac.replace(':','-')
        data={'r_macaddr={0}'.format(eth_mac_str):'Remove'}
        host_url='http://10.135.0.253/self_register/'
    else:
        host_url='http://172.16.0.1/cgi-bin/autopxe.php?address={0}&action={1}'.format(str2url(mac),'Remove')
    ss = requests.Session()
    for i in range(0,30):
        try:
            if data is None:
                r = ss.get(host_url)
                print("Unset CBURN PXE ({0}) (USA)".format(mac))
                os._exit(0)
            else:
                r = ss.post(host_url, data=data)
                if len(re.compile('<div id="macaddr">{0}</div>'.format(eth_mac_str)).findall(r.text)) == 0:
                    print("Unset CBURN PXE ({0}) (Taiwan)".format(mac))
                    os._exit(0)
                print("Can not unset {0} at Auto PXE server(wait 10sec: {1}/30)".format(mac,i))
        except requests.exceptions.RequestException as e:
            print("Auto PXE server has no response (wait 10sec: {0}/30)".format(i))
        time.sleep(10)
    os._exit(1)

def django_try(host_url,data=None,files=None):
    ss = requests.Session()
    for i in range(0,30):
        try:
            if data is None and files is None:
                r = ss.get(host_url)
            elif files is None:
                r = ss.post(host_url, data=data)
            else:
                r = ss.post(host_url, files=files, data=data)
            return r
        except requests.exceptions.RequestException as e:
            print("Django server has no response (wait 10sec: {0}/30)".format(i))
        time.sleep(10)
    return False

##################################################

def sizeConvert(sz=None,unit='b:g'):
    if sz is None:
        return False
    unit_a=unit.lower().split(':')
    if len(unit_a) != 2:
        return False
    def inc(sz):
        return '%.1f'%(float(sz) / 1024)
    def dec(sz):
        return int(sz) * 1024
    sunit=unit_a[0]
    eunit=unit_a[1]
    unit_m=['b','k','m','g','t','p']
    si=unit_m.index(sunit)
    ei=unit_m.index(eunit)
    h=ei-si
    for i in range(0,abs(h)):
        if h > 0:
            sz=inc(sz)
        else:
            sz=dec(sz)
    return sz
    
def put_data(data=None,ipmi_ip=None):
    global DJ_ADDR
    if data is None:
        return 
    if ipmi_ip is not None:
        if ip_in_range(ipmi_ip,'10.141.160.1','10.141.191.254') or ip_in_range(ipmi_ip,'172.31.0.1','172.31.255.254'):
            DJ_ADDR='172.31.44.40'
    host_url='http://{0}:{1}/'.format(DJ_ADDR,DJ_PORT)
    if not django_try(host_url,data=data):
        log("Django server({0}:{1}) has no response".format(DJ_ADDR,DJ_PORT))
        return False
#    try:
#        r = requests.post(host_url,data=data)
#    except requests.exceptions.RequestException as e:
#        log("Django server({0}:{1}) has no response".format(django_addr,django_port))
#        return False


def get_data(bmc_mac=None,find_key=None,ipmi_ip=None):
    global DJ_ADDR
    if bmc_mac is None:
        return
    if ipmi_ip is not None:
        if ip_in_range(ipmi_ip,'10.141.160.1','10.141.191.254')  or ip_in_range(ipmi_ip,'172.31.0.1','172.31.255.254'):
            DJ_ADDR='172.31.44.40'
    if find_key is None:
        host_url='http://{0}:{1}/jfind/?bmc_mac={2}'.format(DJ_ADDR,DJ_PORT,str2url(bmc_mac))
    else:
        host_url='http://{0}:{1}/jfind/?bmc_mac={2}&find_key={3}'.format(DJ_ADDR,DJ_PORT,str2url(bmc_mac),str2url(find_key))

    r=django_try(host_url)
    if not r:
        log("Django server({0}) has no response".format(DJ_ADDR))
        return False
    json_data=json.loads(r.text)
    return json_data

#    ss = requests.Session()
#    try:
#        r = ss.get(host_url)
#    except requests.exceptions.RequestException as e:
#        return False
#    json_data=json.loads(r.text)
#    return json_data


def get_sku(sku=None,ip=None):
    global DJ_ADDR
    if ip is not None:
        if ip_in_range(ip,'10.141.160.1','10.141.191.254')  or ip_in_range(ip,'172.31.0.1','172.31.255.254'):
            DJ_ADDR='172.31.44.40'
    if sku is None:
        host_url='http://{0}:8010/jfind/?sku=all'.format(DJ_ADDR)
    else:
        host_url='http://{0}:8010/jfind/?sku={1}'.format(DJ_ADDR,str2url(sku))
    r=django_try(host_url)
    if r is False:
        log("Django server({0}) has no response".format(DJ_ADDR))
        return False
#    ss = requests.Session()
#    try:
#        r = ss.get(host_url)
#    except requests.exceptions.RequestException as e:
#        return False
    json_data=json.loads(r.text)
    return json_data

class Inventory:
    def __init__(self):
        pass

    def dmidecode():
        import dmidecode
        db={}
        for i in ['bios','system','baseboard','chassis','processor','cache','connector','slot']:
           if not i in db:
               db[i]={}
               tt=dmidecode.QuerySection(i)
               a=tt.keys()
               tt=tt[a[0]]
               for j in tt['data'].keys():
                   db[i].update({j:tt['data'][j]})

        db['memory']={}
        tt=dmidecode.QuerySection('memory')
        for i in tt.keys():
            if 'Maximum Capacity' in tt[i]['data']:
                db['memory'].update({'Maximum Capacity':tt[i]['data']['Maximum Capacity']})
            if 'Number Of Devices' in tt[i]['data']:
                db['memory'].update({'Number Of Devices':tt[i]['data']['Number Of Devices']})
            if 'Locator' in tt[i]['data']:
                db['memory'][tt[i]['data']['Locator']]={}
                db['memory'][tt[i]['data']['Locator']].update({'dmi_handle':'{0}'.format(i)})
                db['memory'][tt[i]['data']['Locator']].update(tt[i]['data'])
        return db

    def bmc():
        import kmisc as km
        db={}
        tmp=km.rshell("ipmitool lan print")
        if tmp[0] == 0:
            bmc_lan_info=tmp[1]
            for i in bmc_lan_info.split('\n'):
                line=i.split(':')
                if len(line) == 2:
                    key=line[0].strip()
                    val=line[1].strip()
                    if key != 'Cipher Suite Priv Max' and len(key) > 0 and len(val) > 0:
                        db.update({'{0}'.format(key):'{0}'.format(val)})
        tmp=km.rshell("ipmitool bmc info")
        if tmp[0] == 0:
            bmc_lan_info=tmp[1]
            for i in bmc_lan_info.split('\n'):
                line=i.split(':')
                if len(line) == 2:
                    key=line[0].strip()
                    val=line[1].strip()
                    if len(key) > 0 and len(val) > 0:
                        db.update({'{0}'.format(key):'{0}'.format(val)})
        return db

############################################################
def read_stage_item(name,data,item_date):
    tmp={}
    b='{0}="(\w.*)"'.format(name)
    a=re.compile(b).findall(data)
    if len(a) == 0:
        b='{0}=(\w.*)'.format(name)
        a=re.compile(b).findall(data)
    if len(a) == 0:
        d=None
    else:
        d=a[0]
    if name == 'MEM_SIZE_TOTAL':
        new_d=sizeConvert(d,unit='k:g')
        if new_d:
            d='{0} G'.format(new_d)
    tmp.update({name:{'data':d,'item_date':item_date}})
    return tmp

def compare_cpu(dic1=None,dic2=None,ignore=None):
    if dic1 is None or dic2 is None:
        return False
    for tt in dic1.keys():
        for idx in dic1[tt].keys():
            for name in dic1[tt][idx].keys():
                if ignore is not None and ignore == name:
                    continue
                if not tt in dic2 or not idx in dic2[tt] or not name in dic2[tt][idx]:
                    return False
                if dic1[tt][idx][name] != dic2[tt][idx][name]:
                    return False
    for tt in dic2.keys():
        for idx in dic2[tt].keys():
            for name in dic2[tt][idx].keys():
                if ignore is not None and ignore == name:
                    continue
                if not tt in dic1 or not idx in dic1[tt] or not name in dic1[tt][idx]:
                    return False
                if dic1[tt][idx][name] != dic2[tt][idx][name]:
                    return False
    return True


def read_stage_items(name,total_name,items,data,item_date):
    tmp={}
    total=0
    found_total=re.compile('{0}=(\d*)'.format(total_name)).findall(data)
    if len(found_total) > 0:
        total=int(found_total[0])
    if total == 0:
        return {}
    tmp[total]={}
    for i in range(total):
        tmp[total][i]={}
#        save=True
        for n in list(items):
            b='{0}_{1}_{2}="(\w.*)"'.format(name,i,n)
            a=re.compile(b).findall(data)
            if len(a) == 0:
                b='{0}_{1}_{2}=(\w.*)'.format(name,i,n)
                a=re.compile(b).findall(data)
            if len(a) == 0:
                d=None
            else:
                d=a[0]
            if (name == 'DIMM' and n == 'PART' and d == 'NO') or (name == 'POWER' and n=='STATUS' and d == 'NotPresent'):
                return {}
#                save=False
            #tmp[total][i].update({n:d})
#            if save:
            tmp[total][i].update({n:d})
#            else:
#                tmp[total].pop(i,None)
#    return tmp
    return {name:{'data':tmp,'item_date':item_date}}

def get_inventory(path=None):
    inv={}
    if path is None:
        stage1_file='/root/stage1.conf'
        stage2_file='/root/stage2.conf'
    else:
        stage1_file='{0}/stage1.conf'.format(path)
        stage2_file='{0}/stage2.conf'.format(path)

    if os.path.exists(stage1_file) and os.path.exists(stage2_file):
        with open(stage2_file,'r') as f:
            stage2=f.read()
        with open(stage1_file,'r') as f:
            stage1=f.read()
        file_stat=os.stat(stage2_file)
        file_time=int(file_stat.st_ctime)

        a=re.compile('SYS_DIR="(\w.*)"').findall(stage2)
        new_path=''
        path_a=None
        if len(a) == 1:
            path_a=a[0].split('/')
        elif path is not None:
            path_a=path.split('/')
            
        if path_a is not None:
            for i in path_a[2:]:
                new_path='{0}/{1}'.format(new_path,i)
            #path
            inv.update({'CBURN_DIR':{'data':'{0}'.format(new_path),'item_date':file_time}})

        #stage1
        for i in ['MBOARD_ID','LNK_MAC']:
            inv.update(read_stage_item(i,stage1,file_time))
        #stage2
        for i in ['BOARD_MANUFACTURER','BOARD_NAME','BOARD_SERIAL','BOARD_VER','BMC_MAC','BMC_IP','BMC_MODE','BMC_BOARD_MFR','EXPANDER_TOTAL','TPM_VER','MEM_SIZE_TOTAL','PHY_SIZE_TOTAL']:
            inv.update(read_stage_item(i,stage2,file_time))
        #stage2
        for i in [{0:'DIMM',1:'DIMM_SLOTS_TOTAL',2:['PART','TYPE','SIZE','SPEED','MANUFACTURER','SERIAL','RANK']},{0:'POWER',1:'POWER_TOTAL',2:['STATUS','MODEL','SERIAL','MANUFACTURER','LOCATION']},{0:'CPU',1:'CPU_NUM',2:['FAMILY','MODEL','MANUFACTURER','MAXSPEED','CORECOUNT','THREADCOUNT','SIGNATURE']},{0:'NET',1:'NET_TOTAL',2:['NAME','MAC','DRIVER','DRVER','BUS_NUM']},{0:'NVME',1:'NVME_TOTAL',2:['NAME','MANU','SERIAL','MODEL','FIRM','SIZE','BUS']},{0:'HDD',1:'HDD_TOTAL',2:['MODEL','SIZE','SERIAL','MODE','HOST','MANU','LNKSPD','PORT','NAME','FIRM','BUS']},{0:'GPU',1:'GPU_COUNT',2:['INDEX','NAME','SERIAL','UUID','VBIOS','INFOROM','DRIVER','BUSID','MECC','MCEVOL','MCEAGG','MUEVOL','MUEAGG']}]:
            read_inv=read_stage_items(i[0],i[1],i[2],stage2,file_time)
            if len(read_inv) > 0:
                inv.update(read_inv)
    else:
        print('stage1.conf and stage2.conf file not found in {0}'.format(path))
    return inv

def inventory_db(find_key=None,find_val=None,inventory=None,bmc_mac=None,inventory_path=None):
    if (inventory is None or type(inventory).__name__ != 'dict') and bmc_mac is None  and len(inventory) > 0:
        return
    if bmc_mac is None:
        if 'BMC_MAC' in inventory:
            bmc_mac=inventory['BMC_MAC']['data']
            inventory.pop('BMC_MAC',None)
    if bmc_mac is None:
        return 

#    print('Work for BMC Mac : {0}'.format(bmc_mac))
    if find_key is None:
        data=get_data(bmc_mac)
    else:
        data=get_data(bmc_mac,find_key)
    if data is False:
        return 
    rc=None
    if len(data) == 0:
        if type(inventory) is dict and len(inventory) > 0:
            inv=[]
            inv.append(inventory)
            pdata={'bmc_mac':'{0}'.format(bmc_mac),'inv':'{0}'.format(inv)}
#            print('\n\n initial initial >', pdata)
            rc=put_data(data=pdata)
            return rc
        elif find_val is not None and find_key is not None:
            tt=[]
            tt.append({find_key:{'data':find_val}})
            pdata={'bmc_mac':'{0}'.format(bmc_mac),'inv':'{0}'.format(tt)}
            print('\n\n initial for find >', pdata)
            rc=put_data(data=pdata)
            return rc
    else:
        if find_key is not None:
            if find_key in data.keys() and find_val is None:
                # Get finding key value
                return(data[find_key]['data'])
            elif find_val is not None:
                # Put finding data to DB
                tt=[]
                # TYPE2
                tt.append({find_key:{'data':find_val}})
                pdata={'bmc_mac':'{0}'.format(bmc_mac),'inv':'{0}'.format(tt)}
#                print("\n\n append finding key > {0}".format(pdata))
                print('++ {0} : Append(0)'.format(find_val))
                rc=put_data(data=pdata)
                return rc
        elif type(inventory) is dict and len(inventory) > 0:
            # Compare data and update DB (Not found then put data, removed data in local server then delete in DB)
            tt=[]
            for key in inventory.keys():
                if key in data.keys():
                    if key == 'item_del_date' or key == 'OOB' or key == 'DCMS' or key == 'DESC' or key == 'LOCATION' or key == 'CBURN_DIR':
                        continue
                    if 'data' in inventory[key] and inventory[key]['data'] == data[key]['data']:
                        #print('** {0} is same data ({1})'.format(key,data[key]))
                        print('== {0} : Same(1)'.format(key))
                    else:
                        if type(data[key]['data']).__name__ == 'unicode':
                            data_str='{0}'.format(data[key]['data'].decode('utf-8'))
                        else:
                            data_str=data[key]['data']
                        if type(data_str) is str:
                            try:
                                invs=ast.literal_eval(data_str)
                            except:
                                invs=data_str
                        else:
                            invs=data_str
                        if type(invs) is int:
                            invs=str(invs)

                        if 'data' in inventory[key]:
                            if inventory[key]['data'] == invs:
                                print('== {0} : Same(2)'.format(key))
                            else:
                                if int(data[key]['item_date']) < int(inventory[key]['item_date']): # Delete Old data in Django
                                    print('+- {0}: different data, del old data and add new data'.format(key))
                                    pdata={'bmc_mac':'{0}'.format(bmc_mac),'inv':'[{0}]'.format({key:{'data':invs,'item_del_date':int(now),'item_date':data[key]['item_date']}})}
                                    rc=put_data(data=pdata)
                                tt.append({key:inventory[key]}) # Add new data
                        else:
                            print('** data not found in {0}'.format(key))
                    data.pop(key,None)
                else:
                    print('++ {0} : Add new key to exist db'.format(key))
                    tt.append({key:inventory[key]})

            if len(data) > 0:
                for key in data.keys():
#                    if key != 'OOB' and key != 'DCMS' and key != 'DESC' and key != 'LOCATION' and key != 'item_del_date' and key != 'CBURN_DIR':
                    if not key in ['OOB','DCMS','DESC','LOCATION','RACK_LOCATION','item_del_date','ipmi_user','ipmi_pass','SKU']:
                        print('-- {0} : Delete'.format(key))
                        tt.append({key:{'data':data[key]['data'],'item_del_date':int(now),'item_date':data[key]['item_date']}})

            pdata={'bmc_mac':'{0}'.format(bmc_mac),'inv':'{0}'.format(tt)}
            rc=put_data(data=pdata)
            return rc

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        inventory_db(inventory=get_inventory(path=sys.argv[1]))
    elif len(sys.argv) == 3 and sys.argv[1] == 'unpxe':
        #unset_cburn_auto_pxe(mac=sys.argv[2],ipmi_ip=sys.argv[3])
        unset_cburn_auto_pxe(mac=sys.argv[2])
    else:
        print('{0} <cburn log directory>'.format(sys.argv[0]))
        print('{0} unpxe <cburn boot ethernet Mac Address>'.format(sys.argv[0]))

    # Add Inventory information
    #inventory_db(inventory=get_inventory())

    #bmc_mac='00:25:90:5f:55:5d'
#    print(inventory_db(find_key='OOB',find_val='EBAD-4ED0-63B3-282F-6858-7901',bmc_mac=bmc_mac))
    #inventory_db(find_key='DCMS',find_val='AAYAAAAAAAAAAAAAAAAAAMDkKFYoP1vML7xVO/ZvErdILzLg7nwaoqy1Y0uCf6XixZAbQYaf484awi341ncmaLEWvldXcMhXHZmM8v2vxQqedJehNuFrVSrTNyEgm8SfcOYQBWiO4RZO6H4gQdWlVJNGxTsbBhczZaMtsZLu2e1o/Y4Y+hA7CF70D9E7xnPLsf0UzVUByzQX9rZ1WhC3vxaZopOdSJFN4ZqMA8d3n3tpVAuElLRVPYpjv/k2uxZNcSdI7vqaLnMxsOyJamoA08fYgfThs2LsXNKRYqFOOOKPNbgRJidNp7rNQ4CDWXHoMqJmobIUnGjRSslSfsp6GQ==',bmc_mac=bmc_mac)
#    prod_key=inventory_db(find_key='OOB',inventory=get_inventory())
    #prod_key=inventory_db(find_key='DCMS',inventory=a)
#    prod_key=inventory_db(find_key='DCMS',bmc_mac=bmc_mac)
#    print(prod_key)
#    if prod_key is None:
#        inventory_db(find_key='OOB',find_val='EBAD-4ED0-63B3-282F-6858-7901',bmc_mac=bmc_mac)
#        inventory_db(find_key='DCMS',find_val='AAYAAAAAAAAAAAAAAAAAAMDkKFYoP1vML7xVO/ZvErdILzLg7nwaoqy1Y0uCf6XixZAbQYaf484awi341ncmaLEWvldXcMhXHZmM8v2vxQqedJehNuFrVSrTNyEgm8SfcOYQBWiO4RZO6H4gQdWlVJNGxTsbBhczZaMtsZLu2e1o/Y4Y+hA7CF70D9E7xnPLsf0UzVUByzQX9rZ1WhC3vxaZopOdSJFN4ZqMA8d3n3tpVAuElLRVPYpjv/k2uxZNcSdI7vqaLnMxsOyJamoA08fYgfThs2LsXNKRYqFOOOKPNbgRJidNp7rNQ4CDWXHoMqJmobIUnGjRSslSfsp6GQ==',bmc_mac=bmc_mac)
