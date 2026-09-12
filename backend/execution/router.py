from __future__ import annotations

import re

from execution.normalizer import CommandNormalizer
from tools.base import ToolResult
from tools.registry import ToolRegistry


class CommandRouter:
    """
    Converts normalized speech into deterministic actions.

    Complex reasoning will be handled by the planner later.
    """

    OPEN_PATTERN = re.compile(
        r"^open\s+(.+?)$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        registry: ToolRegistry,
        normalizer: CommandNormalizer | None = None,
    ) -> None:
        self.registry = registry
        self.normalizer = (
            normalizer
            if normalizer is not None
            else CommandNormalizer()
        )

    def route(self, text: str) -> ToolResult:
        # -----------------------------------------------------
        # Normalize STT output
        # -----------------------------------------------------

        normalized_text = self.normalizer.normalize(
            text
        )

        print(
            f"[Router] Normalized: "
            f"{normalized_text}"
        )

        if not normalized_text:
            return ToolResult(
                success=False,
                message="I didn't hear a command.",
            )

        # -----------------------------------------------------
        # Open application
        # -----------------------------------------------------

        match = self.OPEN_PATTERN.match(
            normalized_text
        )

        if match:
            application = (
                match.group(1)
                .strip()
                .lower()
            )

            tool = self.registry.get(
                "open_application"
            )

            if tool is None:
                return ToolResult(
                    success=False,
                    message=(
                        "The application tool "
                        "is unavailable."
                    ),
                )

            return tool.execute(
                application=application
            )

        # -----------------------------------------------------
        # Unknown command
        # -----------------------------------------------------

        return ToolResult(
            success=False,
            message=(
                f"I don't know how to execute "
                f"'{normalized_text}' yet."
            ),
        )