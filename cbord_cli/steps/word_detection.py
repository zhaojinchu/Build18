from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from math import gcd
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly
from vosk import Model, KaldiRecognizer


@dataclass
class WordDetectionStep:
    name: str = "word_detection"
    wake_phrases: tuple[str, ...] = ("hello door", "open sesame")
    model_path: Path = Path(__file__).resolve().parents[2] / "Mic" / "vosk-model-small-en-us-0.15"
    alsa_device: str = "dsnoop:CARD=HIDMediak,DEV=0"
    mic_sample_rate: int = 48000
    vosk_sample_rate: int = 16000
    channels: int = 2
    chunk_ms: int = 20
    queue_max: int = 100
    cooldown_sec: float = 1.0
    min_word_conf: float = 0.70
    min_avg_conf: float = 0.80
    min_utt_rms: float = 350.0
    debug_rejects: bool = True

    def run(self) -> bool:
        print("\n[Word Detection]")
        print("Listening for wake phrase...")

        model = Model(str(self.model_path))
        grammar_json = json.dumps(list(self.wake_phrases))
        recognizer = KaldiRecognizer(model, self.vosk_sample_rate, grammar_json)
        recognizer.SetWords(True)

        audio_q: queue.Queue[bytes] = queue.Queue(maxsize=self.queue_max)
        stop_flag = threading.Event()
        success_flag = threading.Event()

        resample_ratio = self._make_resampler(self.mic_sample_rate, self.vosk_sample_rate)

        def recognizer_worker() -> None:
            cooldown_until = 0.0
            utt_max_rms = 0.0

            while not stop_flag.is_set():
                try:
                    raw = audio_q.get(timeout=0.2)
                except queue.Empty:
                    continue

                x = np.frombuffer(raw, dtype=np.int16)
                mono_i16 = self._downmix_to_mono_int16(x, self.channels)
                utt_max_rms = max(utt_max_rms, self._rms_int16(mono_i16))

                if resample_ratio is not None:
                    up, down = resample_ratio
                    xf = mono_i16.astype(np.float32) / 32768.0
                    yf = resample_poly(xf, up, down)
                    pcm = (np.clip(yf, -1.0, 1.0) * 32767.0).astype(np.int16)
                else:
                    pcm = mono_i16

                now = time.time()
                if now < cooldown_until:
                    continue

                if recognizer.AcceptWaveform(pcm.tobytes()):
                    out = json.loads(recognizer.Result())
                    text = out.get("text", "").strip()

                    this_utt_rms = utt_max_rms
                    utt_max_rms = 0.0

                    if not text:
                        continue

                    min_c, avg_c, n = self._phrase_conf_stats(out)

                    if text not in self.wake_phrases:
                        if self.debug_rejects:
                            print(
                                f"🔸 Reject (not wake phrase): '{text}'  min={min_c:.2f} "
                                f"avg={avg_c:.2f} rms={this_utt_rms:.0f}"
                            )
                        continue

                    if this_utt_rms < self.min_utt_rms:
                        if self.debug_rejects:
                            print(
                                f"🔸 Reject (low RMS): '{text}'  rms={this_utt_rms:.0f} "
                                f"(<{self.min_utt_rms}) min={min_c:.2f} avg={avg_c:.2f}"
                            )
                        continue

                    if min_c < self.min_word_conf or avg_c < self.min_avg_conf:
                        if self.debug_rejects:
                            print(
                                f"🔸 Reject (low conf): '{text}'  min={min_c:.2f} avg={avg_c:.2f} "
                                f"n={n} rms={this_utt_rms:.0f}"
                            )
                        continue

                    print(
                        f"🟢 Wake word detected: '{text}'  min={min_c:.2f} "
                        f"avg={avg_c:.2f} rms={this_utt_rms:.0f}"
                    )
                    cooldown_until = time.time() + self.cooldown_sec
                    recognizer.Reset()
                    success_flag.set()
                    stop_flag.set()

        worker = threading.Thread(target=recognizer_worker, daemon=True)
        worker.start()

        return self._capture_loop(audio_q, stop_flag, success_flag)

    def _capture_loop(
        self,
        audio_q: queue.Queue[bytes],
        stop_flag: threading.Event,
        success_flag: threading.Event,
    ) -> bool:
        frames_per_chunk = max(256, int(self.mic_sample_rate * (self.chunk_ms / 1000.0)))
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
            str(self.mic_sample_rate),
            "-t",
            "raw",
        ]

        print("Starting capture:")
        print("  ALSA_DEVICE =", self.alsa_device)
        print("  MIC_SR      =", self.mic_sample_rate)
        print("  CHANNELS    =", self.channels)
        print("Listening... Ctrl+C to stop.\n")

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        if proc.stdout is None or proc.stderr is None:
            print("Failed to open audio stream.")
            stop_flag.set()
            return False

        def drain_stderr() -> None:
            for line in proc.stderr:
                s = line.decode("utf-8", errors="ignore").rstrip()
                if s:
                    print("[arecord]", s)

        threading.Thread(target=drain_stderr, daemon=True).start()

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

        return success_flag.is_set()

    @staticmethod
    def _make_resampler(in_sr: int, out_sr: int):
        if in_sr == out_sr:
            return None
        g = gcd(in_sr, out_sr)
        return (out_sr // g, in_sr // g)

    @staticmethod
    def _downmix_to_mono_int16(x: np.ndarray, channels: int) -> np.ndarray:
        if channels == 1:
            return x
        x2 = x.reshape(-1, channels).astype(np.float32)
        return x2.mean(axis=1).astype(np.int16)

    @staticmethod
    def _rms_int16(x: np.ndarray) -> float:
        xf = x.astype(np.float32)
        return float(np.sqrt(np.mean(xf * xf) + 1e-9))

    @staticmethod
    def _phrase_conf_stats(vosk_json: dict):
        words = vosk_json.get("result", [])
        if not words:
            return 0.0, 0.0, 0
        confs = [float(w.get("conf", 0.0)) for w in words]
        return min(confs), sum(confs) / len(confs), len(confs)
