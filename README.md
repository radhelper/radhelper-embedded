# radhelper-embedded

This is a version of [radhelper](https://github.com/radhelper/radiation-setup) focused on embedded setups.

This python module runs on a host machine executing Linux. It is connected through the tty ports to embedded devices that can communicate through the UART.

When the setup is at ChipIR, the _lindy_switch() function can be used for the IP controlled outlets. Each of them will have a predefined static IP address.

## target board requirements and constraints

These are constriants that apply to the setup as it is now.

- No Ethernet connection
- Output via UART protocol
- Capability to reprogram the board on host PC.
- Survive reboots without needing to reprogram.


# Setups that work

## Trenz Smartfusion2

The SFs can be connected through the twins to the control room. There they can be reprogrammed when the shutter is closed.

Additionally, this allows them to be power-cycled through the outlets of the twins. 

The UART output is made through the PMOD headers and the UART/USB converters connected to the raspberry.


# ChipIR

## Equipment

### IP power outlets

These outlets are controlled via an IP address. They can be accessed through the browser for human control, or preferebly, through a script runing on a machine connected to the same netmask.

### Mirror switch

Mirror switches are just that, switches that mirror ports on each side. This makes it possible to connect inside the beam room. Its also possible to provide internet through them in this manner.

### Twins

The twins are a set of USB extenders that are available on the facility. There are 2 modules connected through the mirror switch and hooked up to the IP power outlets. They can sometimes error-out, so they need to be monitored for resets (probably by a human monitoring the setup).

They mirror "exactly" the behavior of a USB, so they show up on COM ports and TTYs, but this means that they also need to be connected to provide power to the USB at the other end.

This is usefull to know when programming a device such as the Trenz Smartfusion boards, which can be programmed from inside the control room, and be turned on and off via the IP outlets powering the twins.





