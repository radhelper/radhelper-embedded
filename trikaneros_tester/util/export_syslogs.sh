#!/bin/bash

# Default values
DEFAULT_TIMESPAN="10"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--timespan)
            _TIMESPAN="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_LOCATION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set default values if not provided
TIMESPAN=${_TIMESPAN:-$DEFAULT_TIMESPAN}

# Check if the output location is provided
if [ -z "$OUTPUT_LOCATION" ]; then
    echo "Error: Output location is required. Please provide the output location using the -o or --output option."
    exit 1
fi

# Add a timestamp to the filenames
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOCAL_LOG_FILE="$OUTPUT_LOCATION/journal_logs_${TIMESPAN}min_$TIMESTAMP.txt"
COMPRESSED_FILE="$OUTPUT_LOCATION/journal_logs_${TIMESPAN}min_$TIMESTAMP.tar.gz"

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_LOCATION"

# Export journal logs from the last specified hours
journalctl --since "$TIMESPAN minute ago" > $LOCAL_LOG_FILE

# Compress the exported log file
tar -czvf $COMPRESSED_FILE $LOCAL_LOG_FILE

# Remove the uncompressed log file
rm $LOCAL_LOG_FILE

echo "Logs from the last $TIMESPAN hours exported and compressed successfully. Timestamp: $TIMESTAMP"
