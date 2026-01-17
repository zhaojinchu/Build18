from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Step(Protocol):
    name: str

    def run(self) -> bool:
        ...


@dataclass
class StepResult:
    name: str
    success: bool
    message: str
