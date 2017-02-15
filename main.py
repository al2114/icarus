import machine
import time
import socket
import network
import dht

from umqtt.simple import MQTTClient

# ============================================================== PARAMETERS ============================================================== 

# Network setup data
#MQTT_BROKER = "192.168.0.10"
MQTT_BROKER = "172.24.1.145"
MQTT_NODE = machine.unique_id()
#MQTT_NODE = "garden"

# Pin numbers
HUMIDITY_PIN = const(2)
I2C_SDA_PIN = const(4)
I2C_SCL_PIN = const(5)
LED_GREEN = const(13)
LED_YELLOW = const(14)
LED_RED = const(0)
#TEMP_SENSOR_ADDR = 71
HUMIDIFIER = const(14)

# Frequency parameters
PUBLISH_FREQUENCY = const(5000)   # in milliseconds
CONTROL_FREQUENCY = const(5)      # in seconds
LED_FREQ = const(1000)

# Topics
STATUS_TOPIC = "esys/icarus/status"
PARAMS_TOPIC = "esys/icarus/params"
ALARM_TOPIC = "esys/icarus/alarm"

# JSON_KEYS
JSON_TIME = "time"
JSON_TEMP = "temp"
JSON_HUM = "hum"
JSON_PLANT = "plant"
JSON_ALARM = "alarm"

# Controller parameters
TEMP_GAIN = const(10)
TEMP_MIN = const(.0)
TEMP_MAX = const(400.)
HUM_GAIN = const(10)
HUM_MIN = const(.0)
HUM_MAX = const(400.)

# ============================================================== SETUP FUNCTIONS ============================================================== 
def networkSetup(network_id=None, network_password=None):
    """
    Initialize newtork connection
    """
    network_id = "EEERover" if network_id is None else network_id
    network_password = "exhibition" if network_password is None else network_password
    #sta_if.connect("John's iPhone", 'icrsislife2k16')

    # Wi-Fi interface for station
    sta_if = network.WLAN(network.STA_IF)

    # Remove conenction from previous network and connect to the new one
    sta_if.active(False)
    sta_if.active(True)

    # Set Wi-Fi interface for access point to False
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

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
    """
    Connect to mqtt server
    """
    client_id = MQTT_NODE if client_id is None else client_id
    addr = MQTT_BROKER if addr is None else addr

    print(client_id)
    client = MQTTClient(client_id, addr)
    client.connect()
    return client


def initI2C():
    """
    Initialize I2C interface
    """
    pin_sda = machine.Pin(I2C_SDA_PIN)
    pin_scl = machine.Pin(I2C_SCL_PIN)
    i2c = machine.I2C(scl=pin_scl,sda=pin_sda,freq=100000)

    return i2c

def initHumidity(pin_num=None):
    """
    Initialize Humidity sensor interface
    """
    pin_num = HUMIDITY_PIN if pin_num is None else pin_num 
    d = dht.DHT22(machine.Pin(HUMIDITY_PIN))
    time.sleep(1)
    return d

def initLED(pin, freq=None):
    """
    Initialize a LED
    """
    freq = LED_FREQ if freq is None else freq
    led = machine.PWM(machine.Pin(pin))
    led.freq(freq)
    return led

# ============================================================== FUNCTIONALITY ============================================================== 

def init():
    """
    Initialize all interfaces
    """

    #Init i2c and get sensor address
    i2c = initI2C()
    print("I2C initiliazed")

    # Init Temperature sensor
    temp_sensor = i2c.scan()[0]
    print("Temp sensor initiliazed")

    # Init humidity sensor
    hum_sensor = initHumidity()
    print("Humidity sensor initialized")

    # Init LEDs
    green = initLED(LED_GREEN)
    yellow = initLED(LED_YELLOW)
    red = initLED(LED_RED)
    print("LEDs initialized")

    #Setup network
    networkSetup("John's iPhone", "icrsislife2k16")
    #networkSetup()
    print("Connected to network")

    # Initialize MQTT client
    mqtt_client = connectMQTT() 
    print("Client initialized")

    # Initialize static variables
    temp_range = TEMP_MAX - TEMP_MIN
    controlTemp.green_min = TEMP_MIN
    controlTemp.green_max = temp_range/3.
    controlTemp.yellow_min = controlTemp.green_min
    controlTemp.yellow_max = 2*controlTemp.yellow_min
    controlTemp.red_min = 2*controlTemp.yellow_max
    controlTemp.red_max = TEMP_MAX

def bytes2temp(byte_list):
    """
    Convert a raw temperature sensor reading to a value 
    """
    if byte_list[1] & 1:
        print("Invalid reading from Temperature sensor")
        raise OSError
    return (((byte_list[0]<<8)+byte_list[1])>>2)/32.0


def getTemp():
    try:
        temp_raw = i2c.readfrom_mem(temp_sensor,3,2)
        temp = bytes2temp(temp_raw)
        return temp
    except OSError:
        publishAlarm("Problem with Temperature Sensor")
        raise

def getHumidity():
    try:
        hum_sensor.measure()
        #hum_sensor.temperature()
        return hum_sensor.humidity()
    except OSError:
        publishAlarm("Problem with Humidity Sensor")
        raise

def publishStatus():
    try:
        temp = getTemp()
        humidity = getHumidty()
        timestamp = time.ticks_diff(time.ticks_ms(), start_time)

        data = {}
        data[JSON_TIME] = timestamp/1000.
        data[JSON_HUM] = hum
        data[JSON_TEMP] = temp
        data[JSON_PLANT] = target[JSON_PLANT]

        mqtt_client.publish(STATUS_TOPIC, bytes(data,'utf-8'))
    except OSError:
        pass


def publishAlarm(alarm_msg):
    data = {}
    data[JSON_ALARM] = alarm_msg
    mqtt_client.publish(ALARM_TOPIC, bytes(data,'utf-8'))


def controlTemp():
    def setLED(temp, LED, min_out, max_out):
        if temp < max_out and temp >= min_out:
            LED.duty(int(temp/TEMP_MAX*LED_FREQ))
        else:
            LED.duty(0)

    error = target[JSON_TEMP] - getTemp()
    temp = error * TEMP_GAIN
    temp = TEMP_MAX if temp > TEMP_MAX else temp
    temp = TEMP_MIN if temp < TEMP_MAX else temp

    setLED(temp, green, controlTemp.green_min, controlTemp.green_max)
    setLED(temp, yellow, controlTemp.yellow_min, controlTemp.yellow_max)
    setLED(temp, red, controlTemp.red_min, controlTemp.red_max)


def controlHumidity(hum):
    '''
    # Could use proper feedback loop or PID here
    error = target[JSON_HUM] - getHumidity()
    hum = error * HUM_GAIN
    hum = HUM_MAX if hum > HUM_MAX else hum
    hum = HUM_MIN if hum < HUM_MIN else hum
    '''
    target_max = target[JSON_HUM]+3
    target_min = target[JSON_HUM]-3

    isHumidifier = False

    if getHumidity() < target_min && !isHumidifier:
        isHumidifier = !isHumidifier
        humdifier() #dummy humidifier on/off
    elif getHumidity() >= target_max && isHumidifier:
        isHumidifier = !isHumidifier
        humdifier()
  

def processParams(topic, msg):
    #if topic == PARAMS_TOPIC:
    target = msg
    target[JSON_TEMP] = float(target[JSON_TEMP])
    target[JSON_HUM] = float(target[JSON_HUM])


def main():
    # Initialize global vars for interfaces
    global i2c              # i2c interface
    global mqtt_client      # mqtt client object
    global hum_sensor       # humidity sensor object
    global temp_sensor      # temperature sensor object

    global green            # green LED
    global yellow           # yellow LED
    global red              # red LED

    global start_time
    global target           # target parameters

    # initialize interfaces
    init()

    target = {}

    # Initialize a timer which publishes data to MQTT server
    publish_timer = machine.Timer(-1)
    publish_timer.init(period=PUBLISH_FREQUENCY, mode=machine.Timer.PERIODIC, callback=lambda: publishStatus())

    # Subscribe to topic to listen for new instructions
    mqtt_client.set_callback()
    mqtt_client.subscribe(PARAMS_TOPIC)

    # Monitor performance
    while True:
        # Check for new profile
        mqtt_client.check_msg()

        # Perform temperature control        
        try:
            controlTemp()
        except OSError:
            pass

        # Perform humidity control        
        try:
            controlHumidity()
        except OSError:
            pass

        # Allow for other actions to use the CPU and for some changes to take place
        time.sleep(CONTROL_FREQUENCY)

        # Average readings and publish status
        temp = getTemp()
        hum = getHumidity()
        publishStatus()


    # Disconnect from server
    mqtt_client.disconnect()

if(__name__ == "__main__"):
    main()
