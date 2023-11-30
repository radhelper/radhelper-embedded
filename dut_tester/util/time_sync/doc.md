1. accessing the r-pi:
    ssh <pi_name>@<pi_IP>: ssh pihub@192.168.0.111
    pawrd: depend4blel4b

2. Changing/Setting static IP:
    2.1 Open the network configuration files: sudo nano /etc/dhcpcd.conf  
    2.2 Look for lines similar to these;  ->  modify them according to the new configuration.
        "interface eth0
        static ip_address=192.168.1.100/24 (new static IP)
        static routers=192.168.1.1 (the gateway)
        static domain_name_servers=192.168.1.1 (DNS)"
    2.3 Restart the dhcpcd service: sudo service dhcpcd restart
    2.4 Verify the new IP address: ip addr show eth0; 

3. Connecting to WiFi while using LAN to communicate to the host PC/ for package management
    3.1 check if the WiFi is active; If not, activate it: "rfkill unblock wifi"
    3.2 Open the wpa_supplicant configuration file for editing: sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
        -> complete these:
        network={
        ssid="your_SSID"
        psk="your_password"
        }

    3.3 Restart the networking service to apply the changes: sudo systemctl restart networking
    3.4 (optional) reboot: sudo reboot

    3.5 now there are both eth0 and wlan0 IPs as possible gateway to the net. but eth0 has priority but it is also used for comm with the PC. Check the current routing table and see the different gateway's with: route -n
        -> Hence, give wlan0 a higher priority:
        sudo ip route add default via <wlan0_gateway> dev wlan0 metric 100
        sudo ip route delete default via <eth0_gateway> dev eth0

        -> To give the priority back to wlan0: 
        sudo ip route add default via <eth0_gateway> dev eth0 metric 100
        sudo ip route delete default via <wlan0_gateway> dev wlan0
    * To deactivate the WiFi: "rfkill block wifi"

4. Time sync the r-pi with host PC (local server)
    4.1 Install NTP client: sudo apt-get install ntp
    4.2 Configure NTP: sudo nano /etc/ntp.conf:
            -> comment all thess lines so that it doesn't atempt to sync with NTP servers (needs internet)  
            #pool 0.debian.pool.ntp.org iburst
            #pool 1.debian.pool.ntp.org iburst
            #pool 2.debian.pool.ntp.org iburst
            #pool 3.debian.pool.ntp.org iburst

    4.3 Add the PC IP as local server, by modifying/adding this line: "server host_IP iburst"
    4.4 run the NTP service: "sudo service ntp restart"

5. 4.3 and 4.4 are done automatically by the script "time_sync_script.sh": see "readme file"
    5.1 To make time_sync_script.sh run at reboot:
            -> sudo crontab -e
            -> add this line: @reboot path_to_time_sync_script/time_sync_script.sh



