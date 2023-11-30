#!/bin/bash
# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the arp command and save results in the .txt file
arp > "$SCRIPT_DIR/arp_results.txt"

# Path to the arp_results.txt file
arp_results_file="$SCRIPT_DIR/arp_results.txt"

# Path to the file containing the MAC addresses of interest
mac_addresses_file="$SCRIPT_DIR/known_macAddresses.txt"

# Read the list of MAC addresses of interest
mapfile -t mac_addresses_of_interest < "$mac_addresses_file"

time_synced=0

# Check ARP results for each MAC address of interest
while read -r address hwt hwaddress flags mask iface; do
    # Check if the line contains the expected columns
    if [[ "$address" == "Address" && "$hwaddress" == "HWaddress" ]]; then
        continue
    fi

    # Check if the MAC address is in the list of interest
    if [[ " ${mac_addresses_of_interest[*]} " == *" $hwaddress "* ]];
        then
        	echo "MAC address $hwaddress connected to r-pi with IP address $address"
		#Add the found IP to the ntp.conf file as a server 
		sudo sed -Ei "s/^server .+ iburst$/server ${address} iburst/" /etc/ntpsec/ntp.conf
		# Run the ntp service
		sudo service ntp restart
		echo "Time syncronised with $hwaddress ($address)"
		time_synced=1
		#date 
        	# Remove found MAC address
        	mac_addresses_of_interest=("${mac_addresses_of_interest[@]/$hwaddress/}")
		break
    fi
done < "$arp_results_file"

if [ "$time_synced" -eq 0 ]; then
	#Time sync failed: print all the known MAC addresses; In principal none none of them was corresponds to the MAC addresse(s) connected to the r-pi via its eth0 port 
	for not_found_mac in "${mac_addresses_of_interest[@]}"; do
		if [ -n "$not_found_mac" ]; then
		echo "MAC address $not_found_mac not connected to r-pi"
		fi
	done
	echo "Time synchronisation failed"
fi
