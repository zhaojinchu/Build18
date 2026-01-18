from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[1] / "piper_work" / "en_US-joe-medium.onnx"
STATE_FILE = Path(__file__).resolve().parent / ".tts_state.json"

FAILURE_PHRASES = [
    "You hella stupid.",
    "Get outta my room.",
    "Access denied. Try harder.",
    "Nice try. Door stays closed.",
    "Nope. You are not getting in.",
]

SUCCESS_PHRASES = [
    "Access granted. Door unlocked.",
    "Welcome back. Opening the door.",
    "You got it. Unlocking now.",
    "All checks passed. Door is opening.",
]

_rng = random.SystemRandom()


def _tts_enabled() -> bool:
    return os.getenv("CBORD_TTS_ENABLED", "1") not in {"0", "false", "no"}


def _load_state() -> dict[str, object]:
    if not STATE_FILE.exists():
        return {"failure_bag": [], "success_bag": [], "last": None}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return {"failure_bag": [], "success_bag": [], "last": None}


def _save_state(state: dict[str, object]) -> None:
    STATE_FILE.write_text(json.dumps(state))


def _next_phrase(phrases: list[str], bag_key: str) -> str:
    state = _load_state()
    bag = list(state.get(bag_key, []))
    last = state.get("last")

    if not bag:
        bag = phrases.copy()
        _rng.shuffle(bag)
        if last and len(bag) > 1 and bag[0] == last:
            bag[0], bag[1] = bag[1], bag[0]

    phrase = bag.pop(0)
    state[bag_key] = bag
    state["last"] = phrase
    _save_state(state)
    return phrase


def speak(text: str) -> None:
    if not _tts_enabled():
        return
    if shutil.which("piper") is None or shutil.which("aplay") is None:
        print("TTS unavailable; skipping speech output.")
        return
    if not MODEL_PATH.exists():
        print(f"TTS model not found at {MODEL_PATH}; skipping speech output.")
        return

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_path = tmp.name
    tmp.close()

    try:
        subprocess.run(
            ["piper", "--model", str(MODEL_PATH), "--output_file", wav_path],
            input=text,
            text=True,
            check=True,
        )
        subprocess.run(["aplay", "-q", wav_path], check=True)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def speak_failure() -> None:
    phrase = _next_phrase(FAILURE_PHRASES, "failure_bag")
    speak(phrase)


def speak_success() -> None:
    phrase = _next_phrase(SUCCESS_PHRASES, "success_bag")
    speak(phrase)
