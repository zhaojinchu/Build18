
import sounddevice as sd
import numpy as np
import math
import time

# ------------------------
# Configuration
# ------------------------
DEVICE_INDEX = None   # Set to mic index if needed
SAMPLE_RATE = 44100
BLOCK_DURATION = 0.1  # seconds
THRESHOLD_DB = -2    # adjust this value

# ------------------------
# Audio callback
# ------------------------
def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)

    # Convert stereo to mono if needed
    audio = indata.mean(axis=1)

    # RMS calculation
    rms = np.sqrt(np.mean(audio**2))

    # Avoid log(0)
    if rms > 0:
        db = 20 * math.log10(rms)
    else:
        db = -np.inf

    print(f"Level: {db:.1f} dB")

    if db >
     THRESHOLD_DB:
        print("🔊 SPIKE DETECTED!")

# ------------------------
# Stream setup
# ------------------------
with sd.InputStream(
    device=DEVICE_INDEX,
    channels=2,
    samplerate=SAMPLE_RATE,
    blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
    callback=audio_callback
):
    print("Listening...")
    while True:
        time.sleep(1)
