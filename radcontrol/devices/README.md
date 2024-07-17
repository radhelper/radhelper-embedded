# Device Communication Project

## Overview
This project provides a framework for communicating with devices using different strategies. It supports IP-based and TTY-based communication strategies, allowing flexibility in connecting to various types of devices. The main components of this project include abstract base classes for device strategies, concrete implementations for specific communication methods, and a central `Device Under Test (DUT)` class to manage device interactions.

## Project Structure

- **dut.py**: Contains the `DUT` class that manages device communication and monitoring.
- **device_strategy.py**: Abstract base class for device communication strategies.
- **ip_strategy.py**: Implementation of the `DeviceStrategy` for IP-based communication.
- **tty_strategy.py**: Implementation of the `DeviceStrategy` for TTY-based communication.

## Files

### dut.py
This file defines the `DUT` class, which is responsible for:
- Initializing the device with relevant details.
- Selecting the appropriate communication strategy (USB or Ethernet).
- Starting and monitoring the device communication through a separate thread.
- Handling power cycles and logging device data.
- Stopping the device communication and cleanup.

### device_strategy.py
Defines the `DeviceStrategy` abstract base class:
- Contains the abstract method `read`, which must be implemented by any concrete strategy class.
- Designed to read data from a device and put it into an output queue.

### ip_strategy.py
Concrete implementation of `DeviceStrategy` for IP-based communication:
- Initializes with DUT information containing IP address and baud rate.
- Implements the `read` method to simulate reading data from an IP device and placing it in the output queue.

### tty_strategy.py
Concrete implementation of `DeviceStrategy` for TTY-based communication:
- Initializes with DUT information containing TTY port and baud rate.
- Implements the `read` method to read data from a TTY device.
- Processes and validates the data, and handles any transmission errors.

## Usage

### Initializing a Device
```python
from dut import DUT
from power_switch_controller import PowerSwitchController

dut_info = {
    "name": "Device1",
    "connection": "usb",  # or "ether"
    "power_switch_port": "port1",
    "power_port_IP": "192.168.0.10",
    "tty": "/dev/ttyUSB0",
    "baudrate": 9600,
    "ip": "192.168.0.100"
}

power_controller = PowerSwitchController()
device = DUT(dut_info, power_controller)
```
## Monitoring a Device
```python
device.monitor()
```

## Stopping a Device
```python
device.stop()
```