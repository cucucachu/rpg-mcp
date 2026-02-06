"""Dice rolling utilities with standard notation support."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass


@dataclass
class DiceResult:
    """Result of a dice roll."""
    notation: str
    rolls: list[int]
    modifier: int
    total: int
    dropped: list[int] | None = None
    details: str = ""


def roll_dice(notation: str) -> DiceResult:
    """
    Roll dice using standard notation.
    
    Supported formats:
    - "d20" or "1d20" - roll one d20
    - "2d6" - roll two d6
    - "2d6+3" - roll two d6 and add 3
    - "4d6-1" - roll four d6 and subtract 1
    - "4d6kh3" or "4d6k3" - roll 4d6, keep highest 3
    - "4d6kl3" - roll 4d6, keep lowest 3
    - "2d20kh1" or "2d20adv" - advantage (roll 2, keep highest)
    - "2d20kl1" or "2d20dis" - disadvantage (roll 2, keep lowest)
    
    Returns:
        DiceResult with rolls, modifier, total, and details
    """
    notation = notation.lower().strip()
    original_notation = notation
    
    # Handle advantage/disadvantage shortcuts
    if "adv" in notation:
        notation = notation.replace("adv", "kh1")
        if not notation.startswith("2"):
            notation = "2" + notation.lstrip("1")
    elif "dis" in notation:
        notation = notation.replace("dis", "kl1")
        if not notation.startswith("2"):
            notation = "2" + notation.lstrip("1")
    
    # Parse the notation
    # Pattern: (count)d(sides)(keep modifier)?(+/- modifier)?
    pattern = r'^(\d*)d(\d+)(k[hl]?\d+)?([+-]\d+)?$'
    match = re.match(pattern, notation)
    
    if not match:
        raise ValueError(f"Invalid dice notation: {original_notation}")
    
    count_str, sides_str, keep_str, mod_str = match.groups()
    
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(mod_str) if mod_str else 0
    
    # Roll the dice
    rolls = [random.randint(1, sides) for _ in range(count)]
    original_rolls = rolls.copy()
    dropped = None
    
    # Handle keep highest/lowest
    if keep_str:
        keep_match = re.match(r'k([hl]?)(\d+)', keep_str)
        if keep_match:
            keep_type = keep_match.group(1) or 'h'  # default to highest
            keep_count = int(keep_match.group(2))
            
            sorted_rolls = sorted(rolls, reverse=(keep_type == 'h'))
            kept = sorted_rolls[:keep_count]
            dropped = sorted_rolls[keep_count:]
            rolls = kept
    
    total = sum(rolls) + modifier
    
    # Build details string
    if dropped:
        details = f"Rolled {original_rolls}, kept {rolls}"
        if modifier:
            details += f", {'+' if modifier > 0 else ''}{modifier}"
    else:
        details = f"Rolled {rolls}"
        if modifier:
            details += f" {'+' if modifier > 0 else ''}{modifier}"
    details += f" = {total}"
    
    return DiceResult(
        notation=original_notation,
        rolls=rolls,
        modifier=modifier,
        total=total,
        dropped=dropped,
        details=details
    )


def roll_multiple(notation: str, times: int) -> list[DiceResult]:
    """Roll the same dice multiple times."""
    return [roll_dice(notation) for _ in range(times)]


def random_choice(options: list[str], weights: list[int] | None = None) -> tuple[int, str]:
    """
    Pick a random item from a list.
    
    Args:
        options: List of options to choose from
        weights: Optional weights for each option (higher = more likely)
    
    Returns:
        Tuple of (index, chosen_option)
    """
    if weights:
        if len(weights) != len(options):
            raise ValueError("Weights must match options length")
        chosen = random.choices(options, weights=weights, k=1)[0]
    else:
        chosen = random.choice(options)
    
    return options.index(chosen), chosen


def coin_flip() -> str:
    """Flip a coin."""
    return random.choice(["heads", "tails"])


def percentile() -> int:
    """Roll a percentile (1-100)."""
    return random.randint(1, 100)
