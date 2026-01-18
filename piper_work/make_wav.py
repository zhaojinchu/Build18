import os
import wave
from piper.voice import PiperVoice

MODEL = "en_US-joe-medium.onnx"
TEXT = "Hello. This should actually speak out loud."

voice = PiperVoice.load(MODEL)

with wave.open("out.wav", "wb") as wf:
    wf.setnchannels(1)                   # ✅ mono
    wf.setsampwidth(2)                   # ✅ 16-bit PCM
    wf.setframerate(voice.config.sample_rate)  # ✅ usually 22050
    voice.synthesize(TEXT, wf)

print("WAV size:", os.path.getsize("out.wav"))
