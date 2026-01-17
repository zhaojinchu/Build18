from __future__ import annotations

import time
from dataclasses import dataclass

import adafruit_fingerprint
import serial


@dataclass
class FingerprintStep:
    name: str = "fingerprint"
    device: str = "/dev/ttyAMA0"
    baudrate: int = 57600
    timeout: float = 1.0
    max_wait_seconds: int = 15

    def run(self) -> bool:
        print("\n[Fingerprint]")
        print("Waiting for fingerprint match...")

        uart = serial.Serial(self.device, baudrate=self.baudrate, timeout=self.timeout)
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

        start = time.monotonic()
        while time.monotonic() - start < self.max_wait_seconds:
            if finger.get_image() != adafruit_fingerprint.OK:
                time.sleep(0.05)
                continue

            if finger.image_2_tz(1) != adafruit_fingerprint.OK:
                return False

            if finger.finger_search() != adafruit_fingerprint.OK:
                return False

            print(f"Fingerprint match confirmed. ID #{finger.finger_id} confidence {finger.confidence}.")
            return True

        print("Fingerprint match timed out.")
        return False
