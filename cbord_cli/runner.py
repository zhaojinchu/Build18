from __future__ import annotations

import time
from typing import Dict, List

from cbord_cli.config import AppConfig
from cbord_cli.steps.face_recognition import FaceRecognitionStep
from cbord_cli.steps.fingerprint import FingerprintStep
from cbord_cli.steps.motor_controller import MotorControllerStep
from cbord_cli.steps.word_detection import WordDetectionStep
from cbord_cli import tts


def build_steps() -> Dict[str, object]:
    return {
        "word_detection": WordDetectionStep(),
        "fingerprint": FingerprintStep(),
        "face_recognition": FaceRecognitionStep(),
        "motor_controller": MotorControllerStep(),
    }


def run_pipeline(config: AppConfig) -> List[str]:
    steps = build_steps()
    errors: List[str] = []

    print("\nStarting authentication pipeline...")
    for step_config in config.steps:
        if not step_config.enabled:
            print(f"- Skipping {step_config.name} (disabled)")
            continue

        step = steps.get(step_config.name)
        if step is None:
            errors.append(f"Unknown step '{step_config.name}'")
            print(errors[-1])
            return errors

        print(f"- Running {step_config.name}")
        success = False
        for attempt in range(1, config.retries + 1):
            print(f"  Attempt {attempt}/{config.retries}")
            if step.run():
                success = True
                break
            if attempt < config.retries:
                print("  Retrying...")

        if not success:
            print("Authentication failed. Access denied.")
            tts.speak_failure()
            errors.append(f"Step '{step_config.name}' failed after {config.retries} retries.")
            return errors

    print("Authentication succeeded. Access granted.")
    tts.speak_success()
    return errors


def run_continuous(config: AppConfig, delay_seconds: float = 1.0) -> None:
    print("\nRunning in continuous mode. Press Ctrl+C to stop.")
    try:
        while True:
            run_pipeline(config)
            time.sleep(delay_seconds)
    except KeyboardInterrupt:
        print("\nContinuous mode stopped.")
