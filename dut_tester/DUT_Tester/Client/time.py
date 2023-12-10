from datetime import datetime, timezone

def convert_unix_to_utc(unix_timestamp):
    # Create a datetime object from the Unix timestamp
    utc_datetime = datetime.utcfromtimestamp(unix_timestamp)

    # Add timezone information to the datetime object
    utc_datetime_with_tz = utc_datetime.replace(tzinfo=timezone.utc)

    return utc_datetime_with_tz

# Example usage:
unix_timestamp = 1702138541.5045142  # Replace this with your Unix timestamp
utc_datetime = convert_unix_to_utc(unix_timestamp)

print("Unix Timestamp:", unix_timestamp)
print("UTC Datetime:", utc_datetime)