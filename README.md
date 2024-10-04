# radhelper-embedded

This is a version of [radhelper](https://github.com/radhelper/radiation-setup) focused on embedded setups.

This python module runs on a host machine executing Linux. It is connected through the tty ports to embedded devices that can communicate through the UART.

When the setup is at ChipIR, the _lindy_switch() function can be used for the IP controlled outlets. Each of them will have a predefined static IP address.

## Target board requirements and constraints

These are constraints that apply to the device with the current setup:

- Output via UART protocol
- Survive reboots without needing to reprogram.

## Getting Started

1. Clone this repository:
    ```sh
    $ git clone git@gitlab.utwente.nl:dcs-group/radiation-setups/radhelper-embedded.git
    $ cd radhelper-embedded
    ```

2. Create a new virtual environment in the `venv` folder and install `radcontrol` as an editable package.
    ```sh
    $ python3.9 -m venv .venv
    $ source .venv/bin/activate
    $ python -m pip install --upgrade pip
    $ pip install -e .
    ```

## Configure the Frame Decoding

The frame_id_formatting.yaml YAML file contains the frame ID formatting configurations. Each entry maps a format string to a frame ID. The format strings are used for unpacking the payload data dynamically based on the frame ID. The documentation to do this is on the file. The frame IDs are integer values that identify the type of frame.

**!!!Remember to adjust them according to your benchmarks!!!**

## Configuring the TTYs

1. Edit the `dut_config.yaml` file to match your setup. The url field follows the format as specified by [PySerial](https://pyserial.readthedocs.io/en/latest/url_handlers.html).

2. Ensure the `server_config.yaml` file is correctly set up for your environment:
    

## Configuring the IP-UART devices

TBD

## Running the Server

1. Activate the virtual environment:
    ```sh
    $ source .venv/bin/activate
    ```

2. Run the server using the `radcontrol` package:
    ```sh
    $ radcontrol
    ```

## Installing the script as a systemd service

1. Create a systemd service file:
    ```sh
    $ sudo nano /etc/systemd/system/radhelper.service
    ```

2. Add the following content to the service file:
    ```ini
    [Unit]
    Description=Radhelper Embedded Service
    After=network.target

    [Service]
    User=<your-username>
    WorkingDirectory=/path/to/radhelper-embedded
    ExecStart=/path/to/radhelper-embedded/.venv/bin/radcontrol
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

3. Enable and start the service:
    ```sh
    $ sudo systemctl enable radhelper.service
    $ sudo systemctl start radhelper.service
    ```

## Additional Notes

- Ensure all configuration files are correctly set up and placed in the appropriate directories.
- Use the provided YAML files for configuring device connections and server settings.
