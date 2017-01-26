import machine
from machine import I2C
import time
import socket
import network


def bytes2temp(byte_str):
    return (((byte_str[0]<<8)+byte_str[1])>>2)/32


def networkSetup():

    sta_if = network.WLAN(network.STA_IF)
    #ap_if = network.WLAN(network.AP_IF)

    sta_if.active(False)
    #ap_if.active(False)


    sta_if.active(True)

    print(sta_if.active())

    if sta_if.isconnected():
        print("Already connected to John's iPhone with ip: " + sta_if.ifconfig()[0])
        return

    sta_if.connect("John's iPhone", 'icrsislife2k16')

    while not sta_if.isconnected():
        time.sleep(0.1)

    if sta_if.isconnected():
        print("Connected to John's iPhone with ip: " + sta_if.ifconfig()[0])

    return


def main():

    #Init pins

    pin_sda = machine.Pin(4)
    pin_scl = machine.Pin(5)

    #Init i2c and get sensor address

    i2c = I2C(scl=pin_scl,sda=pin_sda,freq=100000)

    addr = i2c.scan()
    sensor_addr = addr[0]

    print(sensor_addr)

    #Test sensor

    x = i2c.readfrom_mem(sensor_addr,3,2)

    print(x)

    print(x[0])
    print(x[1])

    #Setup network
    networkSetup()

    #Setup socket
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on', addr)

    while True:

        cl, addr = s.accept()
        print('client connected from', addr)

        #Read code
        x = i2c.readfrom_mem(sensor_addr,3,2)
        not_detect = x[1]&1
        if not_detect:
            print("Can't detect shit!!")
        temp = bytes2temp(x)
        print(temp)

        cl.send(str(temp))
        cl.close()

main()
