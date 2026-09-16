from __future__ import annotations

import re

from tools.base import ToolResult
from tools.registry import ToolRegistry


class SystemCommandRouter:
    """
    Deterministic router for simple Windows system commands.

    Commands handled here should NOT require an LLM.
    """

    VOLUME_UP_PATTERNS = (
        re.compile(r"^(?:volume|sound)\s+up$"),
        re.compile(r"^increase\s+(?:the\s+)?(?:volume|sound)$"),
        re.compile(r"^turn\s+(?:the\s+)?(?:volume|sound)\s+up$"),
        re.compile(r"^raise\s+(?:the\s+)?(?:volume|sound)$"),
    )

    VOLUME_DOWN_PATTERNS = (
        re.compile(r"^(?:volume|sound)\s+down$"),
        re.compile(r"^decrease\s+(?:the\s+)?(?:volume|sound)$"),
        re.compile(r"^turn\s+(?:the\s+)?(?:volume|sound)\s+down$"),
        re.compile(r"^lower\s+(?:the\s+)?(?:volume|sound)$"),
    )

    MUTE_PATTERNS = (
        re.compile(r"^mute$"),
        re.compile(r"^mute\s+(?:the\s+)?(?:volume|sound)$"),
        re.compile(r"^turn\s+(?:the\s+)?(?:volume|sound)\s+off$"),
    )

    UNMUTE_PATTERNS = (
        re.compile(r"^unmute$"),
        re.compile(r"^unmute\s+(?:the\s+)?(?:volume|sound)$"),
        re.compile(r"^turn\s+(?:the\s+)?(?:volume|sound)\s+on$"),
    )

    SET_VOLUME_PATTERNS = (
        re.compile(
            r"^(?:set\s+)?(?:the\s+)?(?:volume|sound)"
            r"\s+(?:to\s+)?(\d{1,3})\s*(?:percent|%)?$"
        ),
    )

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def route(self, text: str) -> ToolResult | None:
        """
        Route a deterministic system command.

        Returns:
            ToolResult if this router recognizes the command.
            None if another router should handle it.
        """

        command = text.strip().lower()

        if not command:
            return None

        result = self._route_volume_up(command)

        if result is not None:
            return result

        result = self._route_volume_down(command)

        if result is not None:
            return result

        result = self._route_mute(command)

        if result is not None:
            return result

        result = self._route_unmute(command)

        if result is not None:
            return result

        result = self._route_set_volume(command)

        if result is not None:
            return result

        return None

    def _get_volume_tool(self):
        return self.registry.get("volume_control")

    def _route_volume_up(self, command: str) -> ToolResult | None:
        if not any(
            pattern.fullmatch(command)
            for pattern in self.VOLUME_UP_PATTERNS
        ):
            return None

        tool = self._get_volume_tool()

        if tool is None:
            return ToolResult(
                success=False,
                message="Volume control is not available.",
            )

        return tool.execute(
            operation="up",
        )

    def _route_volume_down(self, command: str) -> ToolResult | None:
        if not any(
            pattern.fullmatch(command)
            for pattern in self.VOLUME_DOWN_PATTERNS
        ):
            return None

        tool = self._get_volume_tool()

        if tool is None:
            return ToolResult(
                success=False,
                message="Volume control is not available.",
            )

        return tool.execute(
            operation="down",
        )

    def _route_mute(self, command: str) -> ToolResult | None:
        if not any(
            pattern.fullmatch(command)
            for pattern in self.MUTE_PATTERNS
        ):
            return None

        tool = self._get_volume_tool()

        if tool is None:
            return ToolResult(
                success=False,
                message="Volume control is not available.",
            )

        return tool.execute(
            operation="mute",
        )

    def _route_unmute(self, command: str) -> ToolResult | None:
        if not any(
            pattern.fullmatch(command)
            for pattern in self.UNMUTE_PATTERNS
        ):
            return None

        tool = self._get_volume_tool()

        if tool is None:
            return ToolResult(
                success=False,
                message="Volume control is not available.",
            )

        return tool.execute(
            operation="unmute",
        )

    def _route_set_volume(self, command: str) -> ToolResult | None:
        match = None

        for pattern in self.SET_VOLUME_PATTERNS:
            match = pattern.fullmatch(command)

            if match:
                break

        if match is None:
            return None

        percentage = int(match.group(1))

        tool = self._get_volume_tool()

        if tool is None:
            return ToolResult(
                success=False,
                message="Volume control is not available.",
            )

        return tool.execute(
            operation="set",
            percentage=percentage,
        )