# Device Communication Project

## Overview
This project provides a framework for communicating with devices using different strategies. It supports IP-based and TTY-based communication strategies, allowing flexibility in connecting to various types of devices. The main components of this project include abstract base classes for device strategies, concrete implementations for specific communication methods, and a central `Device Under Test (DUT)` class to manage device interactions.

This class defines the `DUT` class, which is responsible for:
- Initializing the device with relevant details.
- Starting and monitoring the device communication through a separate thread.
- Implements the `read` method to read data from device.
- Processes and validates the data, and handles any transmission errors.
- Handling power cycles and logging device data.
- Stopping the device communication and cleanup.

## Usage

### Initializing a Device
```python
from dut import DUT
from power_switch_controller import PowerSwitchController

dut_info = {
    "name": "Device1",
    "power_switch_port": "port1",
    "power_port_IP": "192.168.0.10",
    "url": "/dev/ttyUSB0",
    "baudrate": 9600,
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
