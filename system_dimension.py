# Property of KPM Power for the ANZEN Battery Management System
# Code developed by Saba Azimi
# Created: June 05, 2020
# Last Modified: Nov 01, 2020
# Modified by: Saba Azimi

import can
import binascii
import connect_can
import time

chemistry_type = {
    "1": "lfp",
    "2": "lto",
    "3": "lmo",
    "4": "nmc",
    "5": "nizn",
    "6": "nilead2v",
    "7": "nilead6v",
    "8": "nilead12v",
    "9": "nilead8v",

}


def send_request(arbitration_id, data):
    send_params = can.Message(
        arbitration_id=arbitration_id, data=data, extended_id=True)
    connect_can.can0.send(send_params)


def get_num_batt_temp():  # get and store num cells and num thermistors
    NUMBER_OF_CELLS = 0
    NUMBER_OF_THERMISTORS = 0
    NUMBER_OF_SLAVES = 0
    startTime = time.time()
    send_request(0x181fe8f4, [
        0x14, 0, 0, 0, 0, 0, 0, 0])
    while True:
        try:
            if time.time() - startTime > 5:
                send_request(0x181fe8f4, [
                             0x14, 0, 0, 0, 0, 0, 0, 0])
                startTime = time.time()
            message = connect_can.can0.recv(10.0)
            if message:
                data = binascii.hexlify(message.data)
                frame = hex(message.arbitration_id)
                if frame[2:10] == "1814f4e8" and int(data[0:2], 16) == 1:
                    NUMBER_OF_CELLS = int(data[6:8], 16)
                    NUMBER_OF_THERMISTORS = int(data[10:12], 16)
                    NUMBER_OF_SLAVES = int(data[2:4], 16)
                    break
            else:
                NUMBER_OF_CELLS = 16
                NUMBER_OF_THERMISTORS = 4
        except Exception as e:
            print("error is ", str(e))

    return {
        "NUMBER_OF_CELLS": NUMBER_OF_CELLS,
        "NUMBER_OF_SLAVES": NUMBER_OF_SLAVES,
        "NUMBER_OF_THERMISTORS": NUMBER_OF_THERMISTORS
    }


def send_req(arbitration_id, nos):
    for i in range(nos):
        send_request(arbitration_id, [0x02, i+1, 0, 0, 0, 0, 0, 0])


def slave_configuration():   # Blocking --> 0x1802 frame is generating only when it is available ( Acid ), mnust be prompted to acquire the value using send Request
    system_conf = get_num_batt_temp()
    nos = system_conf["NUMBER_OF_SLAVES"]
    # TO Do : find the proper send Request msg to prompt the response
    count = 0
    # for i in range(nos):
    #     send_request(0x181fe8f4, [0x02, i+1, 0, 0, 0, 0, 0, 0])
    send_req(0x181fe8f4, nos)
    startTime = time.time()
    slave_array = [None for i in range(nos)]
    # print(slave_array)
    while True:
        msg = connect_can.can0.recv(10.0)
        if msg:
            if time.time() - startTime > 3:
                send_req(0x181fe8f4, nos)
                startTime = time.time()
            data = binascii.hexlify(msg.data)
            frame_id = hex(msg.arbitration_id)
            if frame_id == "0x1802f4e8":
                if int(data[:2], 16) == 5:
                    if slave_array[int(data[2:4], 16) - 1] == None:
                        count = count + 1
                        slave_array[int(data[2:4], 16) -
                                    1] = int(data[4:6], 16)
            if count == nos:
                break
    return slave_array


def system_chemistry():
    send_request(0x181fe8f4, [
        0x16, 0, 0, 0, 0, 0, 0, 0])
    chem_type = 0   # if chem_type == 0  --> NO Chemistry available !!!!
    startTime = time.time()
    while True:
        msg = connect_can.can0.recv(10.0)
        if time.time() - startTime > 3:
            send_request(0x181fe8f4, [
                0x16, 0, 0, 0, 0, 0, 0, 0])
            startTime = time.time()
        if msg:
            data = binascii.hexlify(msg.data)
            frame_id = hex(msg.arbitration_id)
            if frame_id[2:10] == '1816f4e8':
                chem_type = int(data[:2], 16)
                break
    # return chemistry_type[str(chem_type)]
    return chem_type


if __name__ == "__main__":
    get_num_batt_temp()
    # print(get_num_batt_temp())
    # print(slave_conf())
    # print(system_chemistry())
    # print(slave_conf())
