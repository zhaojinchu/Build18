#!/usr/bin/env python3
import argparse
import sys
import wave
from pathlib import Path

from piper.voice import PiperVoice


def read_text(cli_text: str) -> str:
    if cli_text:
        return cli_text
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print("Paste text, then press Ctrl-D (Linux/macOS) or Ctrl-Z then Enter (Windows):")
    return sys.stdin.read().strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Text-to-speech using the local Piper voice model."
    )
    parser.add_argument(
        "-t",
        "--text",
        help="Text to speak. If omitted, reads from stdin.",
        default="",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output WAV file path.",
        default="piper_tts.wav",
    )
    args = parser.parse_args()

    text = read_text(args.text)
    if not text:
        print("No text provided.", file=sys.stderr)
        return 1

    model_path = Path(__file__).resolve().parent / "piper_work" / "en_US-joe-medium.onnx"
    if not model_path.exists():
        print(f"Model not found at {model_path}", file=sys.stderr)
        return 1

    voice = PiperVoice.load(str(model_path))
    output_path = Path(args.output).expanduser()

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16
        wf.setframerate(voice.config.sample_rate)
        voice.synthesize(text, wf)

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
