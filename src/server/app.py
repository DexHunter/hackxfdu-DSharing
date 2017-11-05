# coding=utf-8

import os
import json
import random
import traceback
import time
import logging
from flask import Flask, request
import requests
from datetime import datetime
import dateutil.parser
from pyduino import *


app = Flask(__name__, static_url_path="")


# arduino control
a = Arduino(serial_port='/dev/ttyUSB0')
LED_PIN = 13
a.set_pin_mode(LED_PIN, '0')
print('Arduino initialized')


@app.route("/startRent", methods=['GET', 'POST'])
def start_rent():
    res = {}
    res['errorMsg'] = ""
    try:
        # generate post body
        log = ""
        logging.info( "----")
        param = request.get_json()
        houseId = param['houseId']
        renter = param['renter']
        tenant = param['tenant']
        money = param['money']
        payload = {
            'rentHouseId': ''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(16))),
            'payment': money,
            'house': houseId,
            'renter': renter,
            'tenant': tenant
        }
        # send post req
        log += "=========now start rent house========\n"
        log += "renter: " + renter + "\n"
        log += "tenant: " + tenant + "\n"
        log += "payment: " + str(money) + "\n"
        log += "strat to add one transaction=========>\n"

        rentReq = requests.post(
            "http://168.1.144.159:31090/api/RentHouse", data=payload)
        loggging.info( "Rent house return:%s " % rentReq.text)
        rentResult = json.loads(rentReq.text)
        if rentResult.has_key('error'):
            log += str(rentResult['error']['message']) + "\n"
            log += "!!!!!!!!!!!   Rent transaction operation failed   !!!!!!!!!!!\n"
            res['success'] = 0
            res['errorMsg'] += str(rentResult['error']['message']) + "\n"
        else:
            log += "Rent transaction operation success\n"


        transFormPayLoad = {
            'oldOwner': renter,
            'newOwner': tenant,
            'lock': houseId,
            'flag': True
        }
        log += "start to transform ownership=========>\n"
        log += "the house's owner change: " + renter + " --> " + tenant + "\n"
        log += "strat to add one transaction=========>\n"
        logging.info(log)
        transReq = requests.post(
            "http://168.1.144.159:31090/api/TransferOwnership", data=transFormPayLoad)
        logging.info( "TransForm ownership return: %s" % transReq.text)
        transformResult = json.loads(transReq.text)
        if transformResult.has_key('error'):
            log += str(transformResult['error']['message']) + "\n"
            log += "!!!!!!!!!!!   TransForm transaction operation failed   !!!!!!!!!!!\n"
            res['success'] = 0
            res['errorMsg'] = str(transformResult['error']['message'])
        else:
            log += "TransForm transaction operation success\n"
            res['success'] = 1
            res['errorMsg'] = ""

        res['Log'] = log
        logging.info(log)

    except Exception, e:
        logging.info(traceback.format_exc())
        logging.info("Rent Error!!!")

    return json.dumps(res)


@app.route("/openLock", methods=['GET', 'POST'])
def open_lock():
    res = {}
    try:
        log = ""
        param = request.get_json()
        houseId = param['houseId']
        renter = param['renter']
        tenant = param['tenant']
        payLoad = {
            'newOwner': tenant,
            'lock': houseId,
            'order': 'lock'
        }
        log += "=========now start lock house========\n"
        log += "renter: " + renter + "\n"
        log += "tenant: " + tenant + "\n"
        log += "houseId: " + houseId + "\n"
        log += "strat to add one transaction=========>\n"
        r = requests.post(
            "http://168.1.144.159:31090/api/LockOrder", data=payLoad)
        print "open lock return: " + r.text
        result = json.loads(r.text)
        if result.has_key('error'):
            log += str(result['error']['message']) + "\n"
            log += "!!!!!!!!!!!   Lock transaction operation failed   !!!!!!!!!!!\n"
            res['success'] = 0
            res['errorMsg'] = str(result['error']['message'])
        else:
            log += "Lock transaction operation success\n"
            res['success'] = 1
            res['errorMsg'] = ""
    except Exception:
        print(traceback.format_exc())
        print "open lock Error!!!"
        pass
    # if the first time, start timing

    res['Log'] = log

    return json.dumps(res)


@app.route("/Unlock", methods=['GET', 'POST'])
def unlock():
    log = ""
    res = {}
    start_time = time.time()
    param = request.get_json()
    houseId = param['houseId']
    renter = param['renter']
    tenant = param['tenant']
    payLoad = {
    'newOwner': tenant,
    'lock': houseId,
    'order': 'unlock'
    }
    r = requests.post("http://168.1.144.159:31090/api/LockOrder", data=payLoad)
    logging.info('%s'%r)
    a.digital_write(LED_PIN, 1) #set light on
    result = json.loads(r.text)
    if result.has_key('error'):
        log += str(result['error']['message']) + "\n"
        logging.info('%s'%result['error']['message'])
        log += "!!!!!!!!!!!   Unlock transaction operation failed   !!!!!!!!!!!\n"
        res['success'] = 0
        res['errorMsg'] = str(result['error']['message'])
    else:
        log += "Unlock transaction operation success\n"
        res['success'] = 1
        res['errorMsg'] = ""

    time.sleep(3)

    payLoad = {
    'newOwner': tenant,
    'lock': houseId,
    'order': 'lock'
    }
    r = requests.post("http://168.1.144.159:31090/api/LockOrder", data=payLoad)
    logging.info('%s'%r)
    a.digital_write(LED_PIN, 0) #set light off
    result = json.loads(r.text)
    if result.has_key('error'):
        log += str(result['error']['message']) + "\n"
        log += "!!!!!!!!!!!   Lock transaction operation failed   !!!!!!!!!!!\n"
        res['success'] = 0
        res['errorMsg'] = str(result['error']['message'])
    else:
        log += "Lock transaction operation success\n"
        res['success'] = 1
        res['errorMsg'] = ""

    return json.dumps(res)

@app.route("/AutoReturn", methods=['GET', 'POST'])
def auto_return():
    """
    Automatically return the house to renter
    """
    log = ""
    res = {}
    payLoad = {}

    start_time = time.time()
    if request.method == 'GET':
        print("GETTTTTTTTTTTTTTTTTTTTTTTTTTT")
        r = requests.get("http://168.1.144.159:31090/api/RentHouse")
        print(type(r))
        result = json.loads(r.content)
        logging.info('%s'%result)
        print type(result) #list
        for dic in result:
            for data in dic.keys():
                if data == 'timestamp':
                    print dic[data]
                    print datetime.utcfromtimestamp(dic[data])

    elif request.method == 'POST':
        param = request.get_json()
        rentHouseId = param.get('rentHouseId', 'rent1')
        payment = param.get('payment', 10)
        house = param.get('house', 'house1')
        renter = param.get('renter', 'renter1')
        tenant = param.get('tenant', 'tenant1')
        payLoad = {
            "rentHouseId": rentHouseId,
            "payment": payment,
            "house": house,
            "renter": renter,
            "tenant": tenant,
        }

        r = requests.post("http://168.1.144.159:31090/api/RentHouse", data=payLoad)
        result = json.loads(r.text)
        logging.info('%s'%result)

        if result.has_key('error'):
            log += str(result['error']['message']) + "\n"
            log += "!!!!!!!!!!!   Lock transaction operation failed   !!!!!!!!!!!\n"
            res['success'] = 0
            res['errorMsg'] = str(result['error']['message'])
        else:
            log += "Lock transaction operation success\n"
            res['success'] = 1
            res['errorMsg'] = ""

    return json.dumps(res)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
