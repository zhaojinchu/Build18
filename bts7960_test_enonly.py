from gpiozero import PWMOutputDevice
from time import sleep
import sys

# ==========================================
# CONFIGURATION
# ==========================================
RPWM_PIN = 19       # GPIO 19 (Physical Pin 35)
LPWM_PIN = 18       # GPIO 18 (Physical Pin 12)

SPEED = 0.95        # 95% Power (Your tested stable maximum)
DURATION = 7        # Seconds for full travel
RAMP_TIME = 0.05    # Delay between speed steps (seconds)
# ==========================================

# Initialize Hardware
# Frequency at 500Hz helps reduce electrical "ringing" noise
rpwm = PWMOutputDevice(RPWM_PIN, frequency=500) 
lpwm = PWMOutputDevice(LPWM_PIN, frequency=500)

def move_actuator(pwm_pin, direction_label):
    """
    Handles the movement sequence with ramping to protect the Pi 5.
    """
    target_int = int(SPEED * 100)
    print(f"\n[ACTION] {direction_label} at {target_int}% speed...")

    try:
        # 1. Ramp Up (Soft Start)
        for i in range(0, target_int + 1, 5):
            pwm_pin.value = i / 100
            sleep(RAMP_TIME)
        
        # 2. Sustained Movement
        print(f"Holding for {DURATION}s...")
        sleep(DURATION)
        
        # 3. Ramp Down (Soft Stop)
        for i in range(target_int, -1, -5):
            pwm_pin.value = i / 100
            sleep(RAMP_TIME)
            
    except Exception as e:
        print(f"\n[ERROR] Movement interrupted: {e}")
    finally:
        pwm_pin.off()
        print("[IDLE] Movement finished. Cooling down rail...")
        sleep(1.0) # Buffer to let Back-EMF settle before next command

def main():
    print("========================================")
    print("   LINEAR ACTUATOR CONTROL SYSTEM")
    print("========================================")
    print(f" Configured Speed: {int(SPEED*100)}%")
    print(f" Configured Time:  {DURATION}s")
    print("----------------------------------------")
    print(" Commands:")
    print("  [e] + Enter : EXTEND")
    print("  [r] + Enter : RETRACT")
    print("  [q] + Enter : EXIT")
    print("----------------------------------------")

    try:
        while True:
            # strip() removes accidental spaces, lower() handles 'E' or 'e'
            user_input = input("Command > ").lower().strip()

            if user_input == 'e':
                move_actuator(rpwm, "EXTENDING")
            elif user_input == 'r':
                move_actuator(lpwm, "RETRACTING")
            elif user_input == 'q':
                print("\nShutting down system safely...")
                break
            elif user_input == "":
                continue
            else:
                print(f" Invalid command '{user_input}'. Use 'e', 'r', or 'q'.")

    except KeyboardInterrupt:
        print("\n\n[HALT] Manual override detected.")
    finally:
        # Ensure all pins are low before closing
        rpwm.off()
        lpwm.off()
        print("GPIO cleaned up. System offline.\n")

if __name__ == "__main__":
    main()
