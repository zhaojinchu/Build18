import os
import wave
from piper.voice import PiperVoice

model_path = "en_US-joe-medium.onnx"

voice = PiperVoice.load(model_path)

text = "Hello, this is a test."
out_path = "out.wav"

with wave.open(out_path, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(voice.config.sample_rate)
    voice.synthesize(text, wf)

print("WAV bytes:", os.path.getsize(out_path))
