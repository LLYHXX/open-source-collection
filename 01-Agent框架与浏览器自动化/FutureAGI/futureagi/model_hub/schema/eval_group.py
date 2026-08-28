from enum import Enum


class PageType(str, Enum):
    """Valid page types for applying eval groups."""

    EVAL_TASK = "EVAL_TASK"
    PROMPT = "PROMPT"
    DATASET = "DATASET"
    SIMULATE = "SIMULATE"
    EXPERIMENT = "EXPERIMENT"
