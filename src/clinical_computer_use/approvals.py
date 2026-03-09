"""
Human approval checkpoints.
"""

from __future__ import annotations


def require_user_approval(action_label: str) -> bool:
    """
    Terminal approval gate for sensitive actions.
    """
    while True:
        choice = input(f"[Approval] Allow action '{action_label}'? [y/n]: ").strip().lower()
        if choice == "y":
            return True
        if choice == "n":
            return False
        print("[Approval] Invalid input. Enter 'y' or 'n'.")
