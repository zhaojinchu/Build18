from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FingerprintStep:
    name: str = "fingerprint"

    def run(self) -> bool:
        print("\n[Fingerprint]")
        print("Placeholder for fingerprint match.")
        response = input("Type 'match' to simulate fingerprint success: ").strip().lower()
        if response == "match":
            print("Fingerprint match confirmed.")
            return True
        print("Fingerprint match failed.")
        return False
