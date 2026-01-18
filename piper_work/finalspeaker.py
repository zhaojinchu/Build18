import os
import json
import subprocess
import tempfile
import random

MODEL = "en_US-joe-medium.onnx"

PHRASES = [
    "Enter the fuck in you little bitch.",
    "Get the fuck out of my room.",
    "I don't like you at all.",
    "You're a gay little boy",
    "You're a little bitch.",
    "Lowkey kiss my ass.",
    "Welcome to the diddy party",
    "Epstein, here I come"
]

# Store state next to this script so it persists across runs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".tts_state.json")

rng = random.SystemRandom()

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"bag": [], "last": None}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"bag": [], "last": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def next_phrase():
    state = load_state()
    bag = state.get("bag", [])
    last = state.get("last", None)

    # Refill + shuffle when empty
    if not bag:
        bag = PHRASES.copy()
        rng.shuffle(bag)

        # Avoid repeating the last phrase across shuffle boundary
        if last and len(bag) > 1 and bag[0] == last:
            bag[0], bag[1] = bag[1], bag[0]

    phrase = bag.pop(0)
    state["bag"] = bag
    state["last"] = phrase
    save_state(state)
    return phrase

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

if __name__ == "__main__":
    phrase = next_phrase()
    print("Speaking:", phrase)
    speak(phrase)
