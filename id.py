import serial
import adafruit_fingerprint

# Use the port that worked for you!
uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for finger...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    
    return True

counter = 0
while counter < 5:
    if get_fingerprint():
        print(f"MATCH FOUND! ID #{finger.finger_id} with confidence {finger.confidence}")
        exit()
    else:
        print("Finger not found / Match failed.")
        counter += 1
    print("-" * 30)
