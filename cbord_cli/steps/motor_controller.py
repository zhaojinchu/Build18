from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
import time

from cbord_cli import tts

ACTUATOR_LINK = "bts7960_test_enonly.py"


def _load_pwm_output_device():
    spec = importlib.util.find_spec("gpiozero")
    if spec is None:
        return None
    gpiozero = importlib.import_module("gpiozero")
    return getattr(gpiozero, "PWMOutputDevice", None)


PWMOutputDevice = _load_pwm_output_device()


@dataclass
class MotorControllerSettings:
    rpwm_pin: int = 18
    lpwm_pin: int = 19
    speed: float = 0.95
    extend_seconds: float = 9
    hold_seconds: float = 10
    retract_seconds: float = 9
    ramp_step: int = 5
    ramp_delay: float = 0.05
    pwm_frequency: int = 500

    @classmethod
    def from_env(cls) -> "MotorControllerSettings":
        def _get_float(name: str, default: float) -> float:
            raw = os.getenv(name)
            return float(raw) if raw is not None else default

        def _get_int(name: str, default: int) -> int:
            raw = os.getenv(name)
            return int(raw) if raw is not None else default

        return cls(
            rpwm_pin=_get_int("MOTOR_RPWM_PIN", cls.rpwm_pin),
            lpwm_pin=_get_int("MOTOR_LPWM_PIN", cls.lpwm_pin),
            speed=_get_float("MOTOR_SPEED", cls.speed),
            extend_seconds=_get_float("MOTOR_EXTEND_SECONDS", cls.extend_seconds),
            hold_seconds=_get_float("MOTOR_HOLD_SECONDS", cls.hold_seconds),
            retract_seconds=_get_float("MOTOR_RETRACT_SECONDS", cls.retract_seconds),
            ramp_step=_get_int("MOTOR_RAMP_STEP", cls.ramp_step),
            ramp_delay=_get_float("MOTOR_RAMP_DELAY", cls.ramp_delay),
            pwm_frequency=_get_int("MOTOR_PWM_FREQUENCY", cls.pwm_frequency),
        )


def _ramp_up(pwm_pin, target_intensity: int, ramp_step: int, ramp_delay: float) -> None:
    step = max(1, ramp_step)
    for intensity in range(0, target_intensity + 1, step):
        pwm_pin.value = intensity / 100
        time.sleep(ramp_delay)


def _ramp_down(pwm_pin, start_intensity: int, ramp_step: int, ramp_delay: float) -> None:
    step = max(1, ramp_step)
    for intensity in range(start_intensity, -1, -step):
        pwm_pin.value = intensity / 100
        time.sleep(ramp_delay)


@dataclass
class MotorControllerStep:
    name: str = "motor_controller"

    def run(self) -> bool:
        print("\n[Motor Controller]")
        print("Actuator control link:", ACTUATOR_LINK)

        if PWMOutputDevice is None:
            print("GPIO motor driver not available; skipping hardware actuation.")
            return True

        settings = MotorControllerSettings.from_env()
        target_intensity = int(settings.speed * 100)
        print(
            "Motor sequence: "
            f"extend {settings.extend_seconds}s, "
            f"hold {settings.hold_seconds}s, "
            f"retract {settings.retract_seconds}s."
        )
        print(f"Configured speed: {target_intensity}%.")

        rpwm = PWMOutputDevice(settings.rpwm_pin, frequency=settings.pwm_frequency)
        lpwm = PWMOutputDevice(settings.lpwm_pin, frequency=settings.pwm_frequency)
        try:
            print("Extending actuator.")
            _ramp_up(rpwm, target_intensity, settings.ramp_step, settings.ramp_delay)
            time.sleep(settings.extend_seconds)
            _ramp_down(rpwm, target_intensity, settings.ramp_step, settings.ramp_delay)
            rpwm.off()
            tts.speak_success()

            print("Holding position.")
            time.sleep(settings.hold_seconds)

            print("Retracting actuator.")
            _ramp_up(lpwm, target_intensity, settings.ramp_step, settings.ramp_delay)
            time.sleep(settings.retract_seconds)
            _ramp_down(lpwm, target_intensity, settings.ramp_step, settings.ramp_delay)
            lpwm.off()
        finally:
            rpwm.off()
            lpwm.off()
        return True
