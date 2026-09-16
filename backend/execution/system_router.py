from __future__ import annotations

import re

from tools.base import ToolResult
from tools.registry import ToolRegistry


class SystemCommandRouter:
    """
    Deterministic router for simple Windows system commands.

    This router intentionally does not use an LLM.
    """

    _SET_VOLUME_PATTERNS = (
        re.compile(r"^(?:set|change)\s+(?:the\s+)?volume\s+(?:to\s+)?(\d{1,3})$"),
        re.compile(r"^(?:set|change)\s+(?:the\s+)?volume\s+to\s+(\d{1,3})\s+percent$"),
        re.compile(r"^(?:increase|decrease|raise|lower)\s+(?:the\s+)?volume\s+to\s+(\d{1,3})$"),
        re.compile(r"^(?:increase|decrease|raise|lower)\s+(?:the\s+)?volume\s+to\s+(\d{1,3})\s+percent$"),
        re.compile(r"^volume\s+(\d{1,3})$"),
        re.compile(r"^volume\s+(\d{1,3})\s+percent$"),
    )

    _GET_VOLUME_PATTERNS = (
    re.compile(
        r"^(?:what|whats|what's)\s+(?:is\s+)?(?:the\s+)?volume$"
    ),
    re.compile(
        r"^(?:what|whats|what's)\s+(?:is\s+)?(?:the\s+)?volume\s+(?:at|now)$"
    ),
    re.compile(
        r"^(?:check|tell me)\s+(?:the\s+)?volume$"
    ),
    re.compile(
        r"^(?:current|my)\s+volume$"
    ),
    re.compile(
        r"^volume$"
    ),
)

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def route(self, text: str) -> ToolResult | None:
        """
        Route a normalized command.

        Returns:
            ToolResult when this router recognizes the command.
            None when another router should handle it.
        """

        command = text.strip().lower()

        if not command:
            return None

        # -------------------------
        # MUTE
        # -------------------------

        if command in {
            "mute",
            "mute volume",
            "mute the volume",
        }:
            return self._execute("mute")

        # -------------------------
        # UNMUTE
        # -------------------------

        if command in {
            "unmute",
            "unmute volume",
            "unmute the volume",
        }:
            return self._execute("unmute")

        # -------------------------
        # GET VOLUME
        # -------------------------

        if self._matches_any(command, self._GET_VOLUME_PATTERNS):
            return self._execute("get")

        # -------------------------
        # SET VOLUME
        # -------------------------

        for pattern in self._SET_VOLUME_PATTERNS:
            match = pattern.fullmatch(command)

            if match:
                percentage = int(match.group(1))

                if not 0 <= percentage <= 100:
                    return ToolResult(
                        False,
                        "Volume must be between 0 and 100 percent.",
                    )

                return self._execute(
                    "set",
                    percentage=percentage,
                )

        # -------------------------
        # VOLUME UP
        # -------------------------

        if command in {
            "volume up",
            "increase volume",
            "increase the volume",
            "turn up volume",
            "turn the volume up",
            "raise volume",
            "raise the volume",
        }:
            return self._execute("up")

        # -------------------------
        # VOLUME DOWN
        # -------------------------

        if command in {
            "volume down",
            "decrease volume",
            "decrease the volume",
            "turn down volume",
            "turn the volume down",
            "lower volume",
            "lower the volume",
        }:
            return self._execute("down")

        return None

    def _execute(
        self,
        operation: str,
        *,
        percentage: int | None = None,
    ) -> ToolResult:
        tool = self.registry.get("volume_control")

        if tool is None:
            return ToolResult(
                False,
                "The volume control tool is not available.",
            )

        arguments = {
            "operation": operation,
        }

        if percentage is not None:
            arguments["percentage"] = percentage

        try:
            return tool.execute(**arguments)

        except Exception as exc:
            return ToolResult(
                False,
                "I couldn't execute the volume command.",
                {"error": str(exc)},
            )

    @staticmethod
    def _matches_any(
        command: str,
        patterns: tuple[re.Pattern[str], ...],
    ) -> bool:
        return any(pattern.fullmatch(command) for pattern in patterns)