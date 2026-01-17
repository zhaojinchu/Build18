from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "config" / "default.json"


@dataclass
class StepConfig:
    name: str
    enabled: bool


@dataclass
class AppConfig:
    retries: int
    steps: list[StepConfig]


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    data = json.loads(path.read_text())
    steps = [StepConfig(**step) for step in data.get("steps", [])]
    return AppConfig(retries=int(data.get("retries", 5)), steps=steps)


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    payload: dict[str, Any] = {
        "retries": config.retries,
        "steps": [
            {"name": step.name, "enabled": step.enabled} for step in config.steps
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
