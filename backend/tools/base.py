from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None


class Tool(ABC):
    """
    Base interface for every Jarvis tool.

    Tools perform actions.
    They do not decide what the user meant.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool."""
        raise NotImplementedError