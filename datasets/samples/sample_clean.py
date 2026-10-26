"""Sample clean Python code with correct type annotations and no type errors."""

from typing import List, Optional

def compute_average(scores: List[float]) -> Optional[float]:
    """Calculate the arithmetic mean of a list of floats."""
    if not scores:
        return None
    return sum(scores) / len(scores)


def format_greeting(name: str, count: int) -> str:
    """Format a personalized greeting message."""
    return f"Hello, {name}! You have {count} pending tasks."
