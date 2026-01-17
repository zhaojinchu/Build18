from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from cbord_cli.config import AppConfig, load_config, save_config
from cbord_cli.runner import run_continuous, run_pipeline

MENU = """
CBORD CLI
---------
1) View pipeline
2) Toggle step
3) Reorder steps
4) Set retries
5) Run pipeline once
6) Run pipeline continuously
7) Save & exit
8) Exit without saving
"""


def _print_pipeline(config: AppConfig) -> None:
    print("\nCurrent pipeline:")
    for idx, step in enumerate(config.steps, start=1):
        status = "enabled" if step.enabled else "disabled"
        print(f"  {idx}. {step.name} ({status})")
    print(f"Retries per step: {config.retries}")


def _toggle_step(config: AppConfig) -> None:
    _print_pipeline(config)
    selection = input("Select step number to toggle: ").strip()
    if not selection.isdigit():
        print("Invalid selection.")
        return
    index = int(selection) - 1
    if index < 0 or index >= len(config.steps):
        print("Invalid step number.")
        return
    config.steps[index].enabled = not config.steps[index].enabled
    state = "enabled" if config.steps[index].enabled else "disabled"
    print(f"{config.steps[index].name} is now {state}.")


def _reorder_steps(config: AppConfig) -> None:
    _print_pipeline(config)
    order = input("Enter new order (comma-separated numbers, e.g. 1,3,2,4): ").strip()
    if not order:
        print("No changes made.")
        return
    parts = [p.strip() for p in order.split(",") if p.strip()]
    if not all(p.isdigit() for p in parts):
        print("Invalid order input.")
        return
    indices = [int(p) - 1 for p in parts]
    if sorted(indices) != list(range(len(config.steps))):
        print("Order must include each step exactly once.")
        return
    config.steps = [config.steps[i] for i in indices]
    print("Step order updated.")


def _set_retries(config: AppConfig) -> None:
    value = input("Enter retries per step (>=1): ").strip()
    if not value.isdigit():
        print("Invalid number.")
        return
    retries = int(value)
    if retries < 1:
        print("Retries must be >= 1.")
        return
    config.retries = retries
    print(f"Retries set to {config.retries}.")


def main() -> None:
    config = load_config()

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            _print_pipeline(config)
        elif choice == "2":
            _toggle_step(config)
        elif choice == "3":
            _reorder_steps(config)
        elif choice == "4":
            _set_retries(config)
        elif choice == "5":
            _print_pipeline(config)
            run_pipeline(config)
        elif choice == "6":
            _print_pipeline(config)
            run_continuous(config)
        elif choice == "7":
            save_config(config)
            print("Configuration saved. Goodbye.")
            break
        elif choice == "8":
            print("Exiting without saving.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
