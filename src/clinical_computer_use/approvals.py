"""
Human approval checkpoints.
"""

from __future__ import annotations


def require_user_approval(action_label: str, context_block: str | None = None) -> bool:
    """
    Terminal approval gate for sensitive actions.
    """
    while True:
        if context_block:
            print(context_block)
        choice = input(f"[Approval] Allow action '{action_label}'? [y/n]: ").strip().lower()
        if choice == "y":
            return True
        if choice == "n":
            return False
        print("[Approval] Invalid input. Enter 'y' or 'n'.")
