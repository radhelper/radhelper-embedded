#!/bin/bash

# Default values
DEFAULT_USERNAME="trikarenos"
DEFAULT_PASSWORD="trikarenos"
DEFAULT_TIMESPAN="10"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--username)
            _USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            _PASSWORD="$2"
            shift 2
            ;;
        -t|--timespan)
            _TIMESPAN="$2"
            shift 2
            ;;
        -i|--ip)
            SERVER_IP="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if the server IP is provided
if [ -z "$SERVER_IP" ]; then
    echo "Error: Server IP is required. Please provide the server IP using the -i or --ip option."
    exit 1
fi

# Set default values if not provided
USERNAME=${_USERNAME:-$DEFAULT_USERNAME}
PASSWORD=${_PASSWORD:-$DEFAULT_PASSWORD}
TIMESPAN=${_TIMESPAN:-$DEFAULT_TIMESPAN}

# Remote and local file paths
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REMOTE_LOG_FILE="/tmp/journal_logs_${TIMESPAN}hrs_$TIMESTAMP.txt"
COMPRESSED_FILE="/tmp/journal_logs_${TIMESPAN}hrs_$TIMESTAMP.tar.gz"
LOCAL_LOG_FILE="journal_logs_${TIMESPAN}hrs_$TIMESTAMP.txt"

# Connect to the server via SSH and export journal logs
sshpass -p "$PASSWORD" ssh $USERNAME@$SERVER_IP "journalctl --since '$TIMESPAN hours ago' > $REMOTE_LOG_FILE"

# Compress the exported log file on the remote server
sshpass -p "$PASSWORD" ssh $USERNAME@$SERVER_IP "tar -czvf $COMPRESSED_FILE $REMOTE_LOG_FILE"

# Download the compressed log file
sshpass -p "$PASSWORD" scp $USERNAME@$SERVER_IP:$COMPRESSED_FILE .

# Clean up - remove temporary files on the remote server
sshpass -p "$PASSWORD" ssh $USERNAME@$SERVER_IP "rm $REMOTE_LOG_FILE $COMPRESSED_FILE"

echo "Logs exported, compressed, and downloaded successfully."
