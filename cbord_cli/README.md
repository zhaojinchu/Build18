# CBORD CLI

A simple, SSH-friendly CLI to orchestrate door authentication steps on a
Raspberry Pi 5. The CLI lets you enable/disable steps, reorder them, and
run the pipeline with a fixed retry policy.

## Goals

- Word detection first
- If word detection passes, proceed to fingerprint and face recognition
- Fail fast after **5 retries** per step (configurable)
- On success, activate the motor controller (placeholder)

## Project layout

```
cbord_cli/
  cli.py                  # interactive menu
  runner.py               # pipeline runner
  config.py               # config load/save helpers
  steps/
    base.py               # step interface
    word_detection.py     # word detection step (placeholder)
    fingerprint.py        # fingerprint step (placeholder)
    face_recognition.py   # face recognition step (placeholder)
    motor_controller.py   # actuator step (placeholder)
  config/
    default.json
```

## Usage

```bash
python3 cbord_cli/cli.py
```

## Notes on hardware integration

The steps are implemented as **placeholders** so the CLI can run over SSH
without hardware attached. Replace each step's `run()` body with the real
device integration:

- **Word detection**: integrate `Mic/micWord.py` (Vosk) into a function that
  returns `True` only when a wake phrase is detected.
- **Fingerprint**: integrate `id.py` or the Adafruit fingerprint library
  to return `True` on match.
- **Face recognition**: integrate `FaceRecognition/face_rec.py` or refactor
  to return `True` when a known face is found.
- **Motor controller**: replace the placeholder call with GPIO or motor
  controller logic.

## Configuration

The config file is stored as JSON in `cbord_cli/config/default.json`. It
controls:

- `retries`: per-step retry count (default: 5)
- `steps`: ordered list of steps with `enabled` flags

