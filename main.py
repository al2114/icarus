import machine
import time
import socket
import network
import dht
import ujson
import array

from umqtt.simple import MQTTClient

# ============================================================== PARAMETERS ============================================================== 

# Network setup data
#MQTT_BROKER = "192.168.0.10"           # original broker
#MQTT_BROKER = "169.254.219.181"
#MQTT_BROKER = "172.24.1.145"           # Andrew's broker
#MQTT_BROKER = "169.254.219.181"        # Andrew's iphone
MQTT_BROKER = "192.168.43.93"           # Ben's phone
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
PUBLISH_FREQUENCY = const(5000)         # in milliseconds
CONTROL_FREQUENCY = const(5)            # in seconds
#CONTROL_FREQUENCY = const(1)           # in seconds
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
TEMP_GAIN = 30
TEMP_MAX = 400.
ALLOWED_ERROR = const(3)
#TEMP_MIN = .0


# ============================================================== SETUP FUNCTIONS ============================================================== 
def networkSetup(network_id=None, network_password=None):
    """
    Initialize newtork connection
    """
    network_id = "EEERover" if network_id is None else network_id
    network_password = "exhibition" if network_password is None else network_password

    # Wi-Fi interface for station
    sta_if = network.WLAN(network.STA_IF)

    # Remove conenction from previous network and connect to the new one
    sta_if.active(False)
    sta_if.active(True)

    # Set Wi-Fi interface for access point to False
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

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
    d = dht.DHT22(machine.Pin(pin_num))
    time.sleep(2)
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


class GardenController():
    def __init__(self):
        # Public variables
        self.mqtt_client = None      # mqtt client object
        self.params_init = False

        self.hum_data = array.array("f") 
        self.temp_data = array.array("f") 

        # Private variables
        self._hum_on = False
        self._i2c = None              # i2c interface
        self._hum_sensor = None       # humidity sensor object
        self._temp_sensor = None      # temperature sensor object

        self._green = None            # green LED
        self._yellow = None           # yellow LED
        self._red = None              # red LED

        self._humidifier = None        # humidifier

        self._target = dict()          # target parameters



    def setup(self):
        """
        Initialize all interfaces
        """

        #Init i2c and get sensor address
        self._i2c = initI2C()
        print("I2C initiliazed")

        # Init Temperature sensor
        self._temp_sensor = self._i2c.scan()[0]
        print("Temp sensor initiliazed")

        # Init humidity sensor
        self._hum_sensor = initHumidity()
        print("Humidity sensor initialized")

        # Init LEDs
        self._red = initLED(LED_RED)
        self._red_on = False
        print("LEDs initialized")

        # Init Humidifier
        self._humidifier = machine.Pin(14, machine.Pin.OUT, value=1)
        print("Humidifier initialized")

        #Setup network
        #networkSetup("John's iPhone", "icrsislife2k16")
        #networkSetup("Andrew's iPhone", "aaaaaaaa")
        #networkSetup("MB", "icarus2011")
        #networkSetup("icarus", "")
        networkSetup()
        print("Connected to network")

        # Initialize MQTT client
        self.mqtt_client = connectMQTT() 
        print("Client initialized")

        # Make sure to have measurement before running the control loop
        self.measureTemp()
        self.measureHumidity()


    def _bytes2temp(self, byte_list):
        """
        Convert a raw temperature sensor reading to a value 
        """
        if byte_list[1] & 1:
            print("Invalid reading from Temperature sensor")
            raise OSError
        return (((byte_list[0]<<8)+byte_list[1])>>2)/32.0


    def _setLED(self, temp, LED, min_out, max_out):
        """
        Set the duty cycle for the PWM of the LED
        """
        if temp < max_out and temp >= min_out:
            LED.duty(int(temp/TEMP_MAX*LED_FREQ))
        else:
            LED.duty(0)

    def _toggleHum(self):
        self._humidifier.low()
        time.sleep(0.5)
        self._humidifier.high()       

        self._hum_on = not self._hum_on


    def _resetTemp(self):
        """
        Flush all temperature readings except for the last one
        """
        temp = self.temp_data[-1]
        self.temp_data = array.array("f")
        self.temp_data.append(temp)


    def _resetHum(self):
        """
        Flush all humidity readings except for the last one
        """
        hum = self.hum_data[-1]
        self.hum_data = array.array("f")
        self.hum_data.append(hum)


    def publishAlarm(self, alarm_msg):
        """
        Alarm the server that something is wrong with the device
        """
        data = {}
        data[JSON_ALARM] = alarm_msg
        self.mqtt_client.publish(ALARM_TOPIC, bytes(ujson.dumps(data),'utf-8'))


    def getTemp(self):
        """
        Average the humidity readings since the last time status was published
        """
        return sum(self.temp_data)/len(self.temp_data)


    def measureTemp(self):
        """
        Make a measurement with the temperature sensor
        """
        try:
            temp_raw = self._i2c.readfrom_mem(self._temp_sensor,3,2)
            temp = self._bytes2temp(temp_raw)
            self.temp_data.append(temp)
            return
        except OSError:
            print("Problem with Temperature Sensor")
            self.publishAlarm("Problem with Temperature Sensor")
            raise


    def getHumidity(self):
        """
        Average the humidity readings since the last time status was published
        """
        return sum(self.hum_data)/len(self.hum_data)


    def measureHumidity(self):
        """
        Make a measurement with the humidity sensor
        """
        tries = 0
        while(True):
            try:
                self._hum_sensor.measure()
                #hum_sensor.temperature()
                hum = self._hum_sensor.humidity()
                self.hum_data.append(hum)
                return
            except OSError:
                tries +=1
                if (tries >= 3):
                    print("Problem with Humidity Sensor")
                    self.publishAlarm("Problem with Humidity Sensor")
                    raise


    def publishStatus(self):
        """
        Publish the current status of the system 
        """
        try:
            temp = self.getTemp()
            hum = self.getHumidity()

            data = {}
            data[JSON_HUM] = hum
            data[JSON_TEMP] = temp
            data[JSON_PLANT] = self._target[JSON_PLANT]

            #print("publishStatus - publishing")
            self.mqtt_client.publish(STATUS_TOPIC, bytes(ujson.dumps(data),'utf-8'))

            self._resetHum()
            self._resetTemp()

        except OSError:
            pass


    def controlTemp(self):
        """
        Control Temperature levels
        """
        target_min = self._target[JSON_TEMP] - ALLOWED_ERROR
        temp = self.getTemp()
        error = self._target[JSON_TEMP] - temp
        val = TEMP_GAIN * error

        print("Temp value: %f", temp)
        print("Temp min: %f", target_min)
        print("Temp error: %f", error)
        print("Temp setting: %f", val)

        if temp < target_min:
            self._red.duty(int(val))
        else:
            self._red.duty(0)


    def controlHumidity(self):
        """
        Control Humidity levels
        """
        target_max = self._target[JSON_HUM] + ALLOWED_ERROR
        target_min = self._target[JSON_HUM] - ALLOWED_ERROR
        hum = self.getHumidity()
        
        print("Humidity on: %r", self._hum_on)
        print("Humidity value: %f", hum)
        print("Humidity min: %f", target_min)
        print("Humidity max: %f", target_max)

        if (hum < target_min) and  (not self._hum_on):
            self._toggleHum()
        elif (hum >= target_max) and self._hum_on:
            self._toggleHum()

    
    def processParams(self, topic, msg):
        """
        Parse the parameters sent by the webserver
        """
        self.params_init = True
        data = ujson.loads(msg)
        self._target = data
        self._target[JSON_TEMP] = float(self._target[JSON_TEMP])
        self._target[JSON_HUM] = float(self._target[JSON_HUM])

def main():
    garden = GardenController()

    # Initialize 
    garden.setup()

    # Initialize a timer which publishes data to MQTT server
    pub_timer = machine.Timer(-1)
    pub_timer.init(period=PUBLISH_FREQUENCY, mode=machine.Timer.PERIODIC, callback= lambda _ : garden.publishStatus())

    # Subscribe to topic to listen for new instructions
    print("Setting callback")
    garden.mqtt_client.set_callback(garden.processParams)
    garden.mqtt_client.subscribe(PARAMS_TOPIC)

    # Request parameters at init
    garden.publishAlarm("request")
    while not garden.params_init:
        garden.mqtt_client.check_msg()

    print("initialized")

    # Monitor performance
    while True:
        # Check for new profile
        garden.mqtt_client.check_msg()
        print("looped")

        # Perform temperature control        
        try:
            garden.controlTemp()
        except OSError:
            pass

        # Perform humidity control        
        try:
            garden.controlHumidity()
        except OSError:
            pass

        # Allow for other actions to use the CPU and for some changes to take place
        time.sleep(CONTROL_FREQUENCY)

        # Make sensor measurements
        garden.measureTemp()
        garden.measureHumidity()

    # Disconnect from server on exit
    garden.mqtt_client.disconnect()

if(__name__ == "__main__"):

    main()
