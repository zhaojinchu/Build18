import time
import serial
import adafruit_fingerprint

# Use the port that worked!
uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def get_next_free_id():
    """Checks the sensor's memory for the first available empty slot"""
    # R503 usually has 127 slots (some have 300)
    for slot in range(1, 128):
        # We try to load a model; if it fails, the slot is empty
        if finger.load_model(slot) != adafruit_fingerprint.OK:
            return slot
    return None

def enroll_finger(location):
    """Enrolls a fingerprint at the given location index"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print(f"Enrolling into ID #{location}. Place finger...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
                time.sleep(0.1)
            else:
                return False

        print("Templating...", end="", flush=True)
        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            print("Error templating")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(2)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    if finger.create_model() == adafruit_fingerprint.OK:
        print("Created")
    else:
        return False

    print(f"Storing model at ID #{location}...", end="", flush=True)
    if finger.store_model(location) == adafruit_fingerprint.OK:
        print("Stored!")
        return True
    else:
        return False

# --- MAIN LOGIC ---
# 1. Automatically find the next available slot
next_slot = get_next_free_id()

if next_slot is not None:
    print(f"Next available memory slot found: {next_slot}")
    # 2. Run enrollment using that slot
    if enroll_finger(next_slot):
        print(f"Success! Fingerprint is saved in slot {next_slot}")
    else:
        print("Enrollment failed.")
else:
    print("The sensor memory is completely full!")