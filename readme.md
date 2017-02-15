## JSON

embedded to server - topic `esys/icarus/status`
```
{
    time: "str"
    temp: float
    hum: float
    plant: "str"
}
```

server to embedded - topic `esys/icarus/params`
```
{
    time: "str"
    temp: float
    hum: float
    plant: "str"
}
```

topic 'esys/icarus/power'
```
{
    power: "str"
}
```

Note: sensor should get start time when it initializes and track its own time

embedded to server alarm - topic `esys/icarus/alarm`
```
{
    alarm: "str"    # Error msg
}
```


## Screen

```
screen /dev/tty* 115200
```

## Uploading

```
ampy --port /dev/tty* put main.py
```

## I2C API
```
writeto(bus_addr,data)
 - Opens write comm with slave at bus_addr, send each byte in data

readfrom(bus_addr,n)
 - Opens read comm with slave at bus_addr, read n bytes
 - Returns byte_array of n bytes

writeto_mem(bus_addr,reg_addr,data)
 - Opens write comm with slave at bus_addr, send reg_addr, send each byte in data

readfrom_mem(bus_addr,reg_addr,n)
 - Opens write comm with slave at bus_addr, send reg_addr, switch to read mode, read n bytes
 - Returns byte_array of n bytes
```

## MQTT
- MQTT documentation
http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/errata01/os/mqtt-v3.1.1-errata01-os-complete.html

- MQTT micropython
https://github.com/micropython/micropython-lib/tree/master/umqtt.simple

```
client = MQTTClient(CLIENT_ID,BROKER_ADDRESS)
client.connect()

client.publish(TOPIC,bytes(data,'utf-8'))

```

## Sensors
- Humidity
    datasheet http://akizukidenshi.com/download/ds/aosong/AM2302.pdf
    micropython https://adafruit-micropython.readthedocs.io/en/latest/docs/esp8266/tutorial/dht.html
 
 - Temperature
    datasheet http://www.ti.com/lit/ds/symlink/tmp007.pdf


## ESP8266
 - MicroPython https://docs.micropython.org/en/latest/esp8266/esp8266/quickref.html
 - Pins https://learn.adafruit.com/adafruit-feather-huzzah-esp8266/pinouts
 - Documentation https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-huzzah-esp8266.pdf
 - https://learn.adafruit.com/adafruit-feather-huzzah-esp8266?view=all

