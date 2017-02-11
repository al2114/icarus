import machine
import time
import socket
import network

from umqtt.simple import MQTTClient

MQTT_BROKER = "192.168.0.10"
#MQTT_NODE = "garden"
MQTT_NODE = machine.unique_id()
TOPIC = "esys/icarus/temp_sensor"

def bytes2temp(byte_str):
    return (((byte_str[0]<<8)+byte_str[1])>>2)/32


def networkSetup(network_id=None, network_password=None):
    network_id = "EEERover" if network_id is None else network_id
    network_password = "exhibition" if network_password is None else network_password
    #sta_if.connect("John's iPhone", 'icrsislife2k16')

    # Wi-Fi interface for station
    sta_if = network.WLAN(network.STA_IF)

    # Remove conenction from previous network and connect to the new one
    sta_if.active(False)
    sta_if.active(True)

    # Wi-Fi interface for access point
    #ap_if = network.WLAN(network.AP_IF)
    #ap_if.active(False)

    print(sta_if.active())

    if sta_if.isconnected():
        print("Already connected to " + sta_if.ifconfig()[0])
        return

    sta_if.connect(network_id, network_password)

    while not sta_if.isconnected():
        time.sleep(0.1)

    if sta_if.isconnected():
        print("Connected to " + network_id + " with ip: " + sta_if.ifconfig()[0])


def connectMQTT(client_id=None, addr=None):
    client_id = MQTT_NODE if client_id is None else client_id
    addr = MQTT_BROKER if addr is None else addr

    print(client_id)
    client = MQTTClient(client_id, addr)
    client.connect()
    return client


def initI2C():
    #Init pins
    pin_sda = machine.Pin(4)
    pin_scl = machine.Pin(5)

    i2c = machine.I2C(scl=pin_scl,sda=pin_sda,freq=100000)

    return i2c

def main():

    """
    #Init i2c and get sensor address
    i2c = initI2C()

    addr = i2c.scan()
    sensor_addr = addr[0]
    print(sensor_addr)

    #Test sensor
    x = i2c.readfrom_mem(sensor_addr,3,2)
    print(x)
    print(x[0])
    print(x[1])


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
    """

    #Setup network
    networkSetup()
    print("Connected to network")
    mqtt_client = connectMQTT() 
    print("Client initialized")
    data = 0
    while(True):
        data+=1
        string = str(data)
        mqtt_client.publish(TOPIC, bytes(string,'utf-8'))



if(__name__ == "__main__"):
    main()
