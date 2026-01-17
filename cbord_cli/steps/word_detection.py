from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from vosk import Model, KaldiRecognizer


@dataclass
class WordDetectionStep:
    name: str = "word_detection"
    wake_phrases: tuple[str, ...] = ("hello door", "open sesame")
    model_path: Path = Path(__file__).resolve().parents[2] / "Mic" / "vosk-model-small-en-us-0.15"
    alsa_device: str = "dsnoop:CARD=HIDMediak,DEV=0"
    sample_rate: int = 16000
    channels: int = 1
    chunk_ms: int = 20

    def run(self) -> bool:
        print("\n[Word Detection]")
        print("Listening for wake phrase...")

        model = Model(str(self.model_path))
        grammar_json = json.dumps(list(self.wake_phrases))
        recognizer = KaldiRecognizer(model, self.sample_rate, grammar_json)

        frames_per_chunk = max(256, int(self.sample_rate * (self.chunk_ms / 1000.0)))
        chunk_bytes = frames_per_chunk * 2 * self.channels

        cmd = [
            "arecord",
            "-D",
            self.alsa_device,
            "-f",
            "S16_LE",
            "-c",
            str(self.channels),
            "-r",
            str(self.sample_rate),
            "-t",
            "raw",
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        if process.stdout is None:
            print("Failed to open audio stream.")
            return False

        try:
            while True:
                data = process.stdout.read(chunk_bytes)
                if not data:
                    time.sleep(0.01)
                    continue

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip().lower()
                    if not text:
                        continue

                    if text in self.wake_phrases:
                        print(f"Wake phrase detected: '{text}'.")
                        return True
        finally:
            process.terminate()
            process.wait(timeout=2)

        return False
