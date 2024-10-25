# radhelper-embedded

This repository contains an embedded focused version of the [radhelper project](https://github.com/radhelper/radiation-setup).
It is designed to manage and control embedded devices connected through UART or other low-throughput interfaces, and can operate via tty or Ethernet ports on a host Linux machine.

When deployed at ChipIR, the _lindy_switch() function can be used to control IP-managed power outlets. Each switch is assigned a static IP address.

## Target Board Requirements and Constraints

These constraints apply to the connected device:

- Must output data via the UART protocol.
- Must survive reboots without requiring reprogramming.

## Getting Started

### 1. Clone this Repository

```bash
$ git clone git@gitlab.utwente.nl:dcs-group/radiation-setups/radhelper-embedded.git
$ cd radhelper-embedded
```

### 2. Set Up a Virtual Environment

Create a new virtual environment in the venv folder and install radcontrol as an editable package.

```bash
$ python3.9 -m venv .venv
$ source .venv/bin/activate
$ python -m pip install --upgrade pip
$ pip install -e .
```

## Configuring Frame Decoding

The `frame_id_formatting.yaml` file contains the frame ID formatting configurations. Each entry maps a format string to a frame ID, used to dynamically unpack the payload data based on the frame ID.

Note: Adjust these values according to your benchmarks for optimal performance.

## Configuring the TTYs Interfaces

1. Update the `dut_config.yaml` file to reflect your setup. The url field should follow the format specified by [PySerial](https://pyserial.readthedocs.io/en/latest/url_handlers.html).

2. Ensure that the `server_config.yaml` file is configured correctly for your environment.
    

## Configuring IP-UART devices

Modify the `dut_config.yaml` file to add or remove devices dynamically using the command line interface. If the DUT port is set to a value greater than 8, the device will not be power switched, which is useful for bench testing.

## Running the Server

1. Activate the virtual environment:
    ```sh
    $ source .venv/bin/activate
    ```

2. Start the server using the `radcontrol` package:
    ```sh
    $ radcontrol
    ```

## Example Output

Below is an example output when launching radcontrol with a device named "example_device" which receives the UART 
communication through an ethernet adapter. 
This demonstrates the server's startup process and how it initializes the device.

```bash
$ radcontrol
2024-10-25 13:37:23 [    INFO] [Server] Starting server with the following arguments:
2024-10-25 13:37:23 [    INFO] [Server] power_cycle_interval: 2
2024-10-25 13:37:23 [    INFO] [Server] is_debug_test: True
2024-10-25 13:37:23 [ WARNING] [Server] Test is set as debug mode
2024-10-25 13:37:24 [    INFO] [Server] Initializing DUT: example_device
2024-10-25 13:37:24 [    INFO] [Server] Added and initialized DUT with info:
 {
    "name": "example_device",
    "url": "socket://192.168.0.104:20108",
    "timeout": 4,
    "baudrate": 115200,
    "power_switch_port": 9,
    "power_port_IP": "192.168.0.216"
}
Select an option (1-4), or type 0 for help: 
```

After initialization, the server enters monitoring mode with an interactive user interface. 
The user is prompted to select one of the following options:

```bash
Select an option (1-4), or type 0 for help: 0

        Available options:
        0: Help - Displays this help message
        1: Refresh Device Table - Refreshes the table of devices
        2: Power Cycle Device - Power cycles the selected device
        3: Print Status - Prints the currently active devices
        4: Stop - Stops the program
```
- Refresh Device Table: Refreshes the table of connected devices. If devices had some parameter modified, they are relaunched. This also adds or removes devices if they are commented out of `dut_config.yaml`.
- Power Cycle Device: Allows the user to power cycle a specific device. User will be prompted to select a device by name.
- Print Status: Prints information about the currently active devices, including their configurations and status.
- Stop: Stops the server and ends the monitoring session.

## Additional Notes

- Use the provided YAML files for configuring device connections and server settings.

- Currently, no automatic backup is made of the log file. Ensure you have a mechanism to back up logs if needed.
