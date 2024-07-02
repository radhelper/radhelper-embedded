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


## Getting Stated

1. Clone this repository:
    ```sh
    $> git clone git@gitlab.utwente.nl:dcs-group/radiation-setups/radhelper-embedded.git
    $> cd radhelper-embedded
    ```

2. Create a new virtual environment in the `venv` folder and install DUT Tester as editable package.
    ```sh
    $> python3.9 -m venv .venv
    $> source .venv/bin/activate
    $> python -m pip install --upgrade pip
    $> pip install -e .
    ```

In case you run into issues with python versions on Ubuntu you cab easily switch between multiple versions of Python with [PyEnv](https://github.com/pyenv/pyenv).

```sh
$> pyenv versions
$> pyenv global <version>
$> python -m venv .venv
```

## On the Client (Raspberry Pi)
The Raspberry Pi automatically enters the `/opt/DUT_Tester` directory and activates the virtual python environmnt.

1. Configure the IP address on the SD-card by modififying the lines:
   ```bash
        # Example static IP configuration:
        interface eth0
        static ip_address=192.168.0.32
   ```
   in `/etc/dhcpcd.conf` on the boot partition of the SD card.
   
2. Boot the Raspberry Pi, connect via SSH.
    ```
    Username: trikarenos
    Password: trikarenos
    ```
3. Connect to the Pi, make sure to add your SSH key to `~/.ssh/authorized_keys`
    ```sh
    # On your Local Machine (will create a file called ~/.ssh/id_ed25519.pub)
    $> ssh-keygen -t ed25519

    # On the Raspberry Pi
    $> nano ~/.ssh/authorized_keys
    ```
4. Modify the IP address of the server
    ```sh
    # Modify the ExecStart=/opt/DUT_Tester/.venv/bin/python -m DUT_Tester client <ip_address> ../trikaneros_radiation_app
    $> sudo nano /etc/systemd/system/trikarenos_tester.service
    $> sudo systemctl daemon-reload
    $> sudo systemctl restart trikarenos_tester.service
    ```

You can also start a local version of the client (no system service) by running
```sh
$> source .venv/bin/activate
$> python -m DUT_Tester client -h
```

## On the Server
1. Make sure that your ethernet interface is statically configured to the same address you specified above in point 5.
2. Start server
    ```sh
    $> source .venv/bin/activate
    $> python -m DUT_Tester server -h
    $> python -m DUT_Tester server <Raspberry Pi IP>
    ```

**Make sure to specify the correct ip address and id for the power switch.**
```sh
--switch_id SWITCH_ID              # ID of the power switch (default: 6)
--switch_ip SWITCH_IP              # ID of the power switch (default: 192.168.0.100)
--switch_password SWITCH_PASSWORD  # Password of the power switch (default: 1234)
--switch_username SWITCH_USERNAME  # Username of the power switch (default: snmp)
```

# Misc
## Example commands
```s
# At University of Twente
## Standard Setup
python -m DUT_Tester server --switch_username "frits" --switch_password "Whiskers!" --switch_id 6 192.168.0.200 --fallback-power-switch

## Disable automatic power cycling of the Raspberry Pi
python -m DUT_Tester server 192.168.0.200 --no-power-cycle
```

## Installing the script as a systemd service

```sh
$> sudo nano /etc/systemd/system/trikarenos_tester.service
$> sudo systemctl daemon-reload
$> sudo systemctl enable trikarenos_tester.service
$> sudo systemctl restart trikarenos_tester.service
```

File `/etc/systemd/system/trikarenos_tester.service`
```
[Unit]
Description=Automated testing utility for fault tolerance monitoring in radiation environments
After=syslog.target network.target

[Service]
User=trikarenos
Group=users
WorkingDirectory=/opt/DUT_Tester
ExecStart=/opt/DUT_Tester/.venv/bin/python -m DUT_Tester client 192.168.0.2 ../trikaneros_radiation_app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

