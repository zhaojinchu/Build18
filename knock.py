# knock_test.py
# Tests LM393 knock sensor on Raspberry Pi (3.3 V).
# Wiring: LM393 OUT1 -> GPIO17 (BCM), common GND. Uses Pi's internal pull-up.

import time
import RPi.GPIO as GPIO

PIN = 17                 # BCM pin for OUT1
REFRACTORY_MS = 150      # ignore repeats within this time (debounce)
GROUP_WINDOW_MS = 1000   # window to count knocks as a cluster

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN)

while True:
    print(GPIO.input(PIN))
    time.sleep(0.1)

GPIO.cleanup()

#last_ms = 0
#group_start_ms = 0
#group_count = 0

# def now_ms():
#     return int(time.monotonic() * 1000)
# 
# def on_falling(channel):
#     global last_ms, group_start_ms, group_count
# 
#     t = now_ms()
#     if t - last_ms < REFRACTORY_MS:
#         return
# 
#     # Knock grouping
#     if t - group_start_ms > GROUP_WINDOW_MS:
#         group_start_ms = t
#         group_count = 0
#     group_count += 1
# 
#     print(f"KNOCK  t={t}ms  Δ={t - last_ms}ms  group={group_count}")
# 
#     last_ms = t
# 
# # LM393 idles HIGH, goes LOW on knock
# GPIO.add_event_detect(PIN, GPIO.FALLING, callback=on_falling)
# 
# print("Listening for knocks on GPIO17…  (Ctrl+C to exit)")
# print("Tip: start the trimmer mid-way; adjust until light knocks give one event.")
# 
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     pass
# finally:
#     GPIO.cleanup()
# 
