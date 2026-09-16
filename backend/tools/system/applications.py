from __future__ import annotations

import os
import subprocess
from typing import Any

from tools.base import Tool, ToolResult
from tools.system.application_registry import ApplicationRegistry


class OpenApplicationTool(Tool):
    """
    Opens a discovered Windows application.

    Application resolution is handled by ApplicationRegistry.
    This tool is responsible only for validating and launching
    the resolved executable.
    """

    name = "open_application"
    description = "Open an installed Windows application."

    def __init__(
        self,
        registry: ApplicationRegistry,
    ) -> None:
        self.registry = registry

    def execute(
        self,
        application: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Resolve and launch an application.

        Args:
            application:
                Application name or alias supplied by the router.
        """

        query = application.strip()

        if not query:
            return ToolResult(
                success=False,
                message="No application was specified.",
            )

        # -----------------------------------------------------
        # Resolve application
        # -----------------------------------------------------

        app = self.registry.get(query)

        if app is None:
            return ToolResult(
                success=False,
                message=(
                    f"I couldn't find an application "
                    f"called {query}."
                ),
            )

        executable = app.executable

        print(
            f"[Application] Resolved: "
            f"{app.name}"
        )

        print(
            f"[Application] Executable: "
            f"{executable}"
        )

        # -----------------------------------------------------
        # Validate executable
        # -----------------------------------------------------

        if not os.path.isfile(executable):
            return ToolResult(
                success=False,
                message=(
                    f"{app.name} is no longer available "
                    "at its discovered location."
                ),
            )

        if not executable.lower().endswith(".exe"):
            return ToolResult(
                success=False,
                message=(
                    f"{app.name} does not have a valid "
                    "Windows executable."
                ),
            )

        # -----------------------------------------------------
        # Launch application
        # -----------------------------------------------------

        try:
            subprocess.Popen(
                [executable],
                close_fds=True,
            )

        except OSError as exc:
            print(
                f"[Application Error] "
                f"Failed to launch {app.name}: {exc}"
            )

            return ToolResult(
                success=False,
                message=(
                    f"I couldn't open {app.name}."
                ),
                data={
                    "application": app.name,
                    "executable": executable,
                    "error": str(exc),
                },
            )

        print(
            f"[Application] Launched: "
            f"{app.name}"
        )

        return ToolResult(
            success=True,
            message=f"{app.name} is open.",
            data={
                "application": app.name,
                "executable": executable,
            },
        )