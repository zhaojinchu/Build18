from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import face_recognition
import pickle
from picamera2 import Picamera2


@dataclass
class FaceRecognitionStep:
    name: str = "face_recognition"
    encodings_path: Path = Path(__file__).resolve().parents[2] / "FaceRecognition" / "encodings.pickle"
    cascade_path: Path = Path(__file__).resolve().parents[2] / "FaceRecognition" / "haarcascade_frontalface_default.xml"
    max_wait_seconds: int = 15

    def run(self) -> bool:
        print("\n[Face Recognition]")
        print("Searching for a known face...")

        data = pickle.loads(self.encodings_path.read_bytes())
        detector = cv2.CascadeClassifier(str(self.cascade_path))

        picam2 = Picamera2()
        picam2.configure(
            picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
        )
        picam2.start()
        time.sleep(1.0)

        start = time.monotonic()
        try:
            while time.monotonic() - start < self.max_wait_seconds:
                frame = picam2.capture_array()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                rects = detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE,
                )

                boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
                if not boxes:
                    continue

                encodings = face_recognition.face_encodings(rgb, boxes)
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"], encoding)
                    if True not in matches:
                        continue

                    matched_idxs = [i for (i, matched) in enumerate(matches) if matched]
                    counts: dict[str, int] = {}
                    for i in matched_idxs:
                        name = data["names"][i]
                        counts[name] = counts.get(name, 0) + 1

                    name = max(counts, key=counts.get)
                    if name:
                        print(f"Face recognized: {name}.")
                        return True
        finally:
            picam2.stop()

        print("Face recognition timed out.")
        return False
