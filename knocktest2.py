from gpiozero import Button
from time import sleep

knock = Button(17, pull_up=True)  # LM393 OUT1 -> GPIO17, GND -> GND

while True:
    print(int(knock.value))  # 1 = idle, 0 = knock (active-low)
    sleep(0.1)
