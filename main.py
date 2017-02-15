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
TEMP_GAIN = 10
TEMP_MIN = .0
TEMP_MAX = 400.
HUM_GAIN = 10
HUM_MIN = .0
HUM_MAX = 400.


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


class GardenController():

    def __init__(self):
        # Public variables
        mqtt_client = None      # mqtt client object

        # Private variables
        _i2c = None              # i2c interface
        _hum_sensor = None       # humidity sensor object
        _temp_sensor = None      # temperature sensor object

        _green = None            # green LED
        _yellow = None           # yellow LED
        _red = None              # red LED

        _humidifier = None        # humidifier

        _target = {}           # target parameters


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
        self._green = initLED(LED_GREEN)
        self._yellow = initLED(LED_YELLOW)
        self._red = initLED(LED_RED)
        print("LEDs initialized")

        # Init Humidifier
        self._humidifier = machine.Pin(14, machine.Pin.OUT, value=1)
        print("Humidifier initialized")

        #Setup network
        networkSetup("John's iPhone", "icrsislife2k16")
        #networkSetup()
        print("Connected to network")

        # Initialize MQTT client
        self.mqtt_client = connectMQTT() 
        print("Client initialized")

        # Initialize static variables
        temp_range = TEMP_MAX - TEMP_MIN
        self._green_min = TEMP_MIN
        self._green_max = temp_range/3.
        self._yellow_min = self._green_min
        self._yellow_max = 2 * self._yellow_min
        self._red_min = 2 * self._yellow_max
        self._red_max = TEMP_MAX


    def publishAlarm(self, alarm_msg):
        data = {}
        data[JSON_ALARM] = alarm_msg
        self.mqtt_client.publish(ALARM_TOPIC, bytes(data,'utf-8'))


    def _bytes2temp(self, byte_list):
        """
        Convert a raw temperature sensor reading to a value 
        """
        if byte_list[1] & 1:
            print("Invalid reading from Temperature sensor")
            raise OSError
        return (((byte_list[0]<<8)+byte_list[1])>>2)/32.0


    def getTemp(self):
        try:
            temp_raw = self._i2c.readfrom_mem(self._temp_sensor,3,2)
            temp = self._bytes2temp(temp_raw)
            return temp
        except OSError:
            self.publishAlarm("Problem with Temperature Sensor")
            raise

    def getHumidity(self):
        try:
            self._hum_sensor.measure()
            #hum_sensor.temperature()
            return self._hum_sensor.humidity()
        except OSError:
            self.publishAlarm("Problem with Humidity Sensor")
            raise


    def publishStatus(self):
        try:
            temp = self.getTemp()
            humidity = self.getHumidity()
            timestamp = time.ticks_diff(time.ticks_ms(), start_time)

            data = {}
            data[JSON_TIME] = timestamp/1000.
            data[JSON_HUM] = hum
            data[JSON_TEMP] = temp
            data[JSON_PLANT] = target[JSON_PLANT]

            self.mqtt_client.publish(STATUS_TOPIC, bytes(data,'utf-8'))
        except OSError:
            pass


    def _setLED(self, temp, LED, min_out, max_out):
        if temp < max_out and temp >= min_out:
            LED.duty(int(temp/TEMP_MAX*LED_FREQ))
        else:
            LED.duty(0)

    def _toggleHum(self):
        self._humidifier.low()
        sleep(0.5)
        self._humidifier.high()       


    def controlTemp(self):
        error = target[JSON_TEMP] - self.getTemp()
        temp = error * TEMP_GAIN
        temp = TEMP_MAX if temp > TEMP_MAX else temp
        temp = TEMP_MIN if temp < TEMP_MAX else temp

        self._setLED(temp, self._green, self._green_min, self._green_max)
        self._setLED(temp, self._yellow, self._yellow_min, self._yellow_max)
        self._setLED(temp, self._red, self._red_min, self._red_max)


    def controlHumidity(self, hum):
        """
        Could use proper feedback loop or PID here
        error = target[JSON_HUM] - getHumidity()
        hum = error * HUM_GAIN
        hum = HUM_MAX if hum > HUM_MAX else hum
        hum = HUM_MIN if hum < HUM_MIN else hum
        """
        target_max = target[JSON_HUM]+3
        target_min = target[JSON_HUM]-3

        isHumidifier = False

        if (self.getHumidity() < target_min) and  (not isHumidifier):
            isHumidifier =  not isHumidifier
            self._toggleHum() #dummy humidifier on/off
        elif (self.getHumidity() >= target_max) and isHumidifier:
            isHumidifier = not isHumidifier
            self._toggleHum()

    
    def processParams(self, topic, msg):
        #if topic == PARAMS_TOPIC:
        self._target = msg
        self._target[JSON_TEMP] = float(self._target[JSON_TEMP])
        self._target[JSON_HUM] = float(self._target[JSON_HUM])

    def test(self):
        print('Starting Test')

        print('Testing Sensors')
        print('Test1: Temp = %f', self.getTemp())
        print('Test2: Humidity = %f', self.getHumidity())

        print('Testing Peripherals')
        print('Test4: LEDs - Please check manually')
        self._red.high()
        sleep(1)
        self._green.high()
        sleep(1)
        self._yellow.high()
        sleep(1)
        print('Test5: Humidifier - Please check manually')
        self._toggleHum()
        sleep(5)
        self._toggleHum()

        print('All hardware tests complete!')

        print('Sending MQTT JSON message. Please confirm')
        self.publishStatus()


def main():
    garden = GardenController()

    # Initialize 
    garden.setup()


    # Initialize a timer which publishes data to MQTT server
    publish_timer = machine.Timer(-1)
    publish_timer.init(period=PUBLISH_FREQUENCY, mode=machine.Timer.PERIODIC, callback=lambda: garden.publishStatus())

    # Subscribe to topic to listen for new instructions
    garden.mqtt_client.set_callback(garden.processParams)
    garden.mqtt_client.subscribe(PARAMS_TOPIC)

    garden.test()

    # Monitor performance
    while True:
        # Check for new profile
        garden.mqtt_client.check_msg()

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

        # Average readings and publish status
        temp = garden.getTemp()
        hum = garden.getHumidity()
        garden.publishStatus()


    # Disconnect from server
    garden.mqtt_client.disconnect()

if(__name__ == "__main__"):
    main()
