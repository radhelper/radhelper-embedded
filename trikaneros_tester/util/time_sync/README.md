The time synchronisation script runs automaticall at reboot. 
It uses the IP address of the host PC (local server) to permorm the task.
The IP address of the host PC is queried through its MAC address.

known MAC addresses need to be added to the file: known_macAddresses.txt "nano /home/pihub/time_sync/known_macAddresses.txt" 

To run the time synchronisation script manually: "/home/pihub/time_sync/time_sync_script.sh"
Make sure you added the MAC address of the host PC to the file "known_macAddresses.txt"
