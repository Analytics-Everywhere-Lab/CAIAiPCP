from typing import List

from state import Argument


def calculate_decision_confidence(arguments: List[Argument]) -> float:
    """Calculate overall confidence based on argument validity scores"""
    if not arguments:
        return 0.5

    support_scores = [
        arg.validity_score for arg in arguments if arg.argument_type == "support"
    ]
    attack_scores = [
        arg.validity_score for arg in arguments if arg.argument_type == "attack"
    ]

    avg_support = sum(support_scores) / len(support_scores) if support_scores else 0.5
    avg_attack = sum(attack_scores) / len(attack_scores) if attack_scores else 0.5

    # Higher support and lower attack scores increase confidence
    confidence = (avg_support + (1 - avg_attack)) / 2
    return round(confidence, 2)


def clip_text(text: str, max_chars: int) -> str:
    """Collapse whitespace and truncate to max_chars, marking the cut with '...'."""
    text = " ".join((text or "").split())
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."
