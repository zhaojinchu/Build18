import wave
import sounddevice as sd
from piper.voice import PiperVoice

# Load the model
model_path = "en_US-lessac-medium.onnx"
voice = PiperVoice.load(model_path)

text = "The Raspberry Pi 5 is powerful enough for neural speech."

# Stream to audio device
with sd.OutputStream(samplerate=voice.config.sample_rate, channels=1, dtype='int16') as stream:
    for audio_bytes in voice.synthesize_stream_raw(text):
        stream.write(audio_bytes)