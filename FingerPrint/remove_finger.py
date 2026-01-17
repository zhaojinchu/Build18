import serial
import adafruit_fingerprint
import sys

# Use the port that worked!
id_to_delete = int(sys.argv[1])
uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def delete_fingerprint(location):
    """Delete a fingerprint model from the sensor's flash memory"""
    print(f"Attempting to delete ID #{location}...", end="")
    
    if finger.delete_model(location) == adafruit_fingerprint.OK:
        print("DELETED successfully.")
    else:
        print("FAILED. The ID might already be empty.")

# Specify the ID you want to remove
delete_fingerprint(id_to_delete)