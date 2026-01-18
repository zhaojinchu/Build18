import wave
from piper.voice import PiperVoice

voice = PiperVoice.load("en_US-joe-medium.onnx")

with wave.open("out.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # int16
    wf.setframerate(voice.config.sample_rate)
    voice.synthesize("Hello. If you hear this, Piper works.", wf)

print("Wrote out.wav")
