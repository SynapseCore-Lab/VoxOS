from __future__ import annotations

from typing import Any

from tools.base import Tool, ToolResult
from tools.system.audio import WindowsAudioController


class VolumeControlTool(Tool):
    name = "volume_control"
    description = (
        "Control Windows master volume: increase, decrease, "
        "set percentage, mute, unmute, or get current volume."
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
            # -------------------------
            # GET CURRENT VOLUME
            # -------------------------

            if operation == "get":
                volume = self.controller.get_volume()
                muted = self.controller.is_muted()

                if muted:
                    message = (
                        f"Volume is at {volume}%, "
                        "and the system is muted."
                    )
                else:
                    message = f"Volume is at {volume}%."

                return ToolResult(
                    True,
                    message,
                    {
                        "operation": operation,
                        "volume": volume,
                        "muted": muted,
                    },
                )

            # -------------------------
            # VOLUME UP
            # -------------------------

            if operation == "up":
                volume = self.controller.volume_up(step)

                return ToolResult(
                    True,
                    f"Volume increased to {volume}%.",
                    {
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            # -------------------------
            # VOLUME DOWN
            # -------------------------

            if operation == "down":
                volume = self.controller.volume_down(step)

                return ToolResult(
                    True,
                    f"Volume decreased to {volume}%.",
                    {
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            # -------------------------
            # SET VOLUME
            # -------------------------

            if operation == "set":
                if percentage is None:
                    return ToolResult(
                        False,
                        "No volume percentage was provided.",
                    )

                volume = self.controller.set_volume(percentage)

                return ToolResult(
                    True,
                    f"Volume set to {volume}%.",
                    {
                        "operation": operation,
                        "volume": volume,
                        "muted": self.controller.is_muted(),
                    },
                )

            # -------------------------
            # MUTE
            # -------------------------

            if operation == "mute":
                self.controller.mute()

                return ToolResult(
                    True,
                    "Volume muted.",
                    {
                        "operation": operation,
                        "volume": self.controller.get_volume(),
                        "muted": True,
                    },
                )

            # -------------------------
            # UNMUTE
            # -------------------------

            if operation == "unmute":
                self.controller.unmute()

                return ToolResult(
                    True,
                    "Volume unmuted.",
                    {
                        "operation": operation,
                        "volume": self.controller.get_volume(),
                        "muted": False,
                    },
                )

            # -------------------------
            # UNKNOWN OPERATION
            # -------------------------

            return ToolResult(
                False,
                f"Unknown volume operation: {operation}.",
            )

        except ValueError as exc:
            return ToolResult(False, str(exc))

        except Exception as exc:
            return ToolResult(
                False,
                "I couldn't control the Windows volume.",
                {"error": str(exc)},
            )