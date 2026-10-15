"""Poker invite code utilities.
Format: POKER-G{group_id:03d}-{RANDOM4}
Example: POKER-G001-A3K9
"""
import random
import string


def generate_invite_code(group_id: int) -> str:
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"POKER-G{group_id:03d}-{random_part}"


def parse_invite_code(code: str) -> dict | None:
    """Parse an invite code. Returns dict with module/group_id or None if invalid."""
    parts = code.upper().split("-")
    # Expected: ['POKER', 'G001', 'A3K9']
    if len(parts) != 3:
        return None
    module = parts[0]
    group_part = parts[1]
    if not group_part.startswith("G") or not group_part[1:].isdigit():
        return None
    return {
        "module": module,
        "group_id": int(group_part[1:]),
        "random": parts[2],
    }
