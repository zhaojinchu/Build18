# CBORD CLI

A simple, SSH-friendly CLI to orchestrate door authentication steps on a
Raspberry Pi 5. The CLI lets you enable/disable steps, reorder them, and
run the pipeline either once or continuously.

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
    word_detection.py     # Vosk wake-word detection
    fingerprint.py        # Adafruit fingerprint reader
    face_recognition.py   # face recognition via Picamera2
    motor_controller.py   # actuator step (placeholder)
  config/
    default.json
```

## Usage

```bash
python3 cbord_cli/cli.py
```

Choose:
- **Run pipeline once** to authenticate a single user.
- **Run pipeline continuously** for 24/7 usage. Press `Ctrl+C` to stop.

## Hardware integration notes

The steps are wired to the existing libraries used in this repo and should
run on the Raspberry Pi 5 with the appropriate hardware attached:

- **Word detection**: Uses Vosk and `arecord` to listen for a wake phrase.
  The default model path is `Mic/vosk-model-small-en-us-0.15`.
- **Fingerprint**: Uses the Adafruit fingerprint library with `/dev/ttyAMA0`
  at `57600` baud.
- **Face recognition**: Uses Picamera2 and OpenCV, reading encodings from
  `FaceRecognition/encodings.pickle`.
- **Motor controller**: Placeholder only; replace with GPIO or motor driver
  logic to actuate the door.

If a step fails, it retries up to the configured count and then exits with
"Access denied".

## Configuration

The config file is stored as JSON in `cbord_cli/config/default.json`. It
controls:

- `retries`: per-step retry count (default: 5)
- `steps`: ordered list of steps with `enabled` flags

