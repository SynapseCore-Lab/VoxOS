from __future__ import annotations

from enum import Enum, auto


class InteractionState(Enum):
    """
    High-level interaction state.

    This is separate from the microphone/audio state.
    """

    IDLE = auto()
    EXECUTING = auto()
    WAITING_FOR_CONFIRMATION = auto()
    SPEAKING = auto()
    SHUTTING_DOWN = auto()