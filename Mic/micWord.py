#!/usr/bin/env python3
import json
import queue
import signal
import subprocess
import threading
import time
from math import gcd

import numpy as np
from scipy.signal import resample_poly
from vosk import Model, KaldiRecognizer

# ------------------------
# CONFIG
# ------------------------
MODEL_PATH = "vosk-model-small-en-us-0.15"

WAKE_PHRASES = ["hello door", "open sesame"]
GRAMMAR_JSON = json.dumps(WAKE_PHRASES)

VOSK_SR = 16000

# Use dsnoop to avoid "Device or resource busy"
ALSA_DEVICE = "dsnoop:CARD=HIDMediak,DEV=0"
MIC_SR = 48000
CHANNELS = 2

CHUNK_MS = 20
QUEUE_MAX = 100

# Debounce (prevents rapid retriggers)
COOLDOWN_SEC = 1.0

# Confidence gating (tune these)
MIN_WORD_CONF = 0.70     # require every word >= this
MIN_AVG_CONF  = 0.80     # require avg confidence >= this

# Energy gating (tune this; int16 RMS)
MIN_UTT_RMS = 350        # require utterance max RMS >= this

# Debug prints for rejected wake-word candidates
DEBUG_REJECTS = True

# ------------------------
# INIT VOSK
# ------------------------
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, VOSK_SR, GRAMMAR_JSON)

# Enable word-level output (conf, start/end)
rec.SetWords(True)  # adds "result": [{"word":..., "conf":..., "start":..., "end":...}, ...] :contentReference[oaicite:2]{index=2}

audio_q: queue.Queue[bytes] = queue.Queue(maxsize=QUEUE_MAX)
stop_flag = threading.Event()

# ------------------------
# RESAMPLER (mic -> 16k)
# ------------------------
def make_resampler(in_sr: int, out_sr: int):
    if in_sr == out_sr:
        return None
    g = gcd(in_sr, out_sr)
    return (out_sr // g, in_sr // g)  # (up, down)

RESAMPLE_RATIO = make_resampler(MIC_SR, VOSK_SR)

def downmix_to_mono_int16(x: np.ndarray, channels: int) -> np.ndarray:
    if channels == 1:
        return x
    x2 = x.reshape(-1, channels).astype(np.float32)
    return x2.mean(axis=1).astype(np.int16)

def rms_int16(x: np.ndarray) -> float:
    # x is int16 mono
    xf = x.astype(np.float32)
    return float(np.sqrt(np.mean(xf * xf) + 1e-9))

def phrase_conf_stats(vosk_json: dict):
    """
    Returns (min_conf, avg_conf, word_count)
    If words missing, returns (0,0,0).
    """
    words = vosk_json.get("result", [])
    if not words:
        return 0.0, 0.0, 0
    confs = [float(w.get("conf", 0.0)) for w in words]
    return min(confs), sum(confs) / len(confs), len(confs)

# ------------------------
# WORKER: VOSK FEED
# ------------------------
def recognizer_worker():
    cooldown_until = 0.0
    utt_max_rms = 0.0

    while not stop_flag.is_set():
        try:
            raw = audio_q.get(timeout=0.2)
        except queue.Empty:
            continue

        x = np.frombuffer(raw, dtype=np.int16)
        mono_i16 = downmix_to_mono_int16(x, CHANNELS)

        # Track utterance energy (max RMS over chunks until AcceptWaveform True)
        utt_max_rms = max(utt_max_rms, rms_int16(mono_i16))

        # Resample to 16k if needed
        if RESAMPLE_RATIO is not None:
            up, down = RESAMPLE_RATIO
            xf = mono_i16.astype(np.float32) / 32768.0
            yf = resample_poly(xf, up, down)
            pcm = (np.clip(yf, -1.0, 1.0) * 32767.0).astype(np.int16)
        else:
            pcm = mono_i16

        now = time.time()
        if now < cooldown_until:
            continue

        if rec.AcceptWaveform(pcm.tobytes()):
            out = json.loads(rec.Result())
            text = out.get("text", "").strip()

            # Reset utterance RMS tracker for next utterance
            this_utt_rms = utt_max_rms
            utt_max_rms = 0.0

            if not text:
                continue

            min_c, avg_c, n = phrase_conf_stats(out)

            # Hard filter: must match exactly a wake phrase
            if text not in WAKE_PHRASES:
                if DEBUG_REJECTS:
                    print(f"🔸 Reject (not wake phrase): '{text}'  min={min_c:.2f} avg={avg_c:.2f} rms={this_utt_rms:.0f}")
                continue

            # Energy gate: ignore “wake” that happened in near-silence
            if this_utt_rms < MIN_UTT_RMS:
                if DEBUG_REJECTS:
                    print(f"🔸 Reject (low RMS): '{text}'  rms={this_utt_rms:.0f} (<{MIN_UTT_RMS}) min={min_c:.2f} avg={avg_c:.2f}")
                continue

            # Confidence gates
            if min_c < MIN_WORD_CONF or avg_c < MIN_AVG_CONF:
                if DEBUG_REJECTS:
                    print(f"🔸 Reject (low conf): '{text}'  min={min_c:.2f} avg={avg_c:.2f} n={n} rms={this_utt_rms:.0f}")
                continue

            print(f"🟢 Wake word detected: '{text}'  min={min_c:.2f} avg={avg_c:.2f} rms={this_utt_rms:.0f}")
            cooldown_until = time.time() + COOLDOWN_SEC
            rec.Reset()

# ------------------------
# CAPTURE: arecord -> queue
# ------------------------
def capture_loop():
    frames_per_chunk = max(256, int(MIC_SR * (CHUNK_MS / 1000.0)))
    chunk_bytes = frames_per_chunk * 2 * CHANNELS  # int16

    cmd = [
        "arecord",
        "-D", ALSA_DEVICE,
        "-f", "S16_LE",
        "-c", str(CHANNELS),
        "-r", str(MIC_SR),
        "-t", "raw",
    ]

    print("Starting capture:")
    print("  ALSA_DEVICE =", ALSA_DEVICE)
    print("  MIC_SR      =", MIC_SR)
    print("  CHANNELS    =", CHANNELS)
    print("Listening... Ctrl+C to stop.\n")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    assert proc.stdout is not None and proc.stderr is not None

    # Drain stderr to avoid blocking
    def _drain_stderr():
        for line in proc.stderr:
            s = line.decode("utf-8", errors="ignore").rstrip()
            if s:
                print("[arecord]", s)

    threading.Thread(target=_drain_stderr, daemon=True).start()

    try:
        while not stop_flag.is_set():
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
            try:
                audio_q.put_nowait(data)
            except queue.Full:
                pass
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            pass

# ------------------------
# MAIN
# ------------------------
def _handle_stop(sig, frame):
    stop_flag.set()

signal.signal(signal.SIGINT, _handle_stop)
signal.signal(signal.SIGTERM, _handle_stop)

if __name__ == "__main__":
    threading.Thread(target=recognizer_worker, daemon=True).start()
    capture_loop()
    stop_flag.set()
    print("\nStopped.")
