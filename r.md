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
