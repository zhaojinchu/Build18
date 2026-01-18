import subprocess
import tempfile
import os

MODEL = "en_US-joe-medium.onnx"

def speak(text: str):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_path = tmp.name
    tmp.close()

    try:
        subprocess.run(
            ["piper", "--model", MODEL, "--output_file", wav_path],
            input=text,
            text=True,
            check=True
        )
        subprocess.run(["aplay", "-q", wav_path], check=True)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

print("Type something and press Enter. Type 'q' to quit.")
while True:
    text = input("> ").strip()
    if text.lower() in ["q", "quit", "exit"]:
        break
    if text:
        speak(text)
