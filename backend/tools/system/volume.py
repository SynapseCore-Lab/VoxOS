from __future__ import annotations

from typing import Any

from tools.base import Tool, ToolResult
from tools.system.audio import WindowsAudioController


class VolumeControlTool(Tool):
    """
    High-level volume control tool.

    Supported operations:
    - up
    - down
    - set
    - mute
    - unmute
    """

    name = "volume_control"

    description = (
        "Control Windows master volume: increase, decrease, "
        "set percentage, mute, or unmute."
    )

    def __init__(
        self,
        controller: WindowsAudioController | None = None,
    ) -> None:
        self.controller = controller or WindowsAudioController()

    def execute(
        self,
        operation: str,
        percentage: int | None = None,
        step: int | None = None,
        **kwargs: Any,
    ) -> ToolResult:

        operation = operation.strip().lower()

        try:
            if operation == "up":
                volume = self.controller.volume_up(step)

                return ToolResult(
                    success=True,
                    message=f"Volume increased to {volume}%.",
                    data={
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            if operation == "down":
                volume = self.controller.volume_down(step)

                return ToolResult(
                    success=True,
                    message=f"Volume decreased to {volume}%.",
                    data={
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            if operation == "set":
                if percentage is None:
                    return ToolResult(
                        success=False,
                        message="No volume percentage was provided.",
                    )

                volume = self.controller.set_volume(percentage)

                return ToolResult(
                    success=True,
                    message=f"Volume set to {volume}%.",
                    data={
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            if operation == "mute":
                self.controller.mute()

                return ToolResult(
                    success=True,
                    message="Volume muted.",
                    data={
                        "operation": operation,
                        "volume": self.controller.get_volume(),
                        "muted": True,
                    },
                )

            if operation == "unmute":
                self.controller.unmute()

                return ToolResult(
                    success=True,
                    message="Volume unmuted.",
                    data={
                        "operation": operation,
                        "volume": self.controller.get_volume(),
                        "muted": False,
                    },
                )

            return ToolResult(
                success=False,
                message=f"Unknown volume operation: {operation}.",
            )

        except ValueError as exc:
            return ToolResult(
                success=False,
                message=str(exc),
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                message="I couldn't control the Windows volume.",
                data={
                    "error": str(exc),
                },
            )