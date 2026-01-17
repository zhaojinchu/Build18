from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WordDetectionStep:
    name: str = "word_detection"
    wake_phrases: tuple[str, ...] = ("hello door", "open sesame")

    def run(self) -> bool:
        print("\n[Word Detection]")
        print("Say the wake phrase (placeholder via text input).")
        text = input("Enter phrase: ").strip().lower()
        if text in self.wake_phrases:
            print("Wake phrase detected.")
            return True
        print("Wake phrase not recognized.")
        return False
