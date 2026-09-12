from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from tools.base import Tool, ToolResult


class OpenApplicationTool(Tool):
    """
    Opens a supported Windows application.

    Responsibilities:
        - Resolve application aliases
        - Find the application executable
        - Launch the application
        - Return a structured ToolResult
    """

    name = "open_application"
    description = "Open a Windows application."

    # ---------------------------------------------------------
    # Supported Applications
    # ---------------------------------------------------------

    APPLICATIONS = {
        "chrome": [
            "chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "notepad": [
            "notepad.exe",
        ],
        "calculator": [
            "calc.exe",
        ],
    }

    # ---------------------------------------------------------
    # Speech / User Aliases
    # ---------------------------------------------------------

    ALIASES = {
        # Chrome
        "google chrome": "chrome",
        "chrome browser": "chrome",

        # Notepad
        "note pad": "notepad",
        "note pattern": "notepad",
        "notepad": "notepad",

        # Calculator
        "calc": "calculator",
        "windows calculator": "calculator",
    }

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    def execute(
        self,
        application: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Open the requested application.
        """

        # -----------------------------------------------------
        # Normalize application name
        # -----------------------------------------------------

        application = application.strip().lower()

        if not application:
            return ToolResult(
                success=False,
                message="No application was specified.",
            )

        # -----------------------------------------------------
        # Resolve aliases
        # -----------------------------------------------------

        application = self.ALIASES.get(
            application,
            application,
        )

        print(
            f"[Application] Resolved application: "
            f"{application}"
        )

        # -----------------------------------------------------
        # Find application configuration
        # -----------------------------------------------------

        candidates = self.APPLICATIONS.get(
            application
        )

        if candidates is None:
            return ToolResult(
                success=False,
                message=(
                    f"I don't know how to open "
                    f"{application} yet."
                ),
            )

        # -----------------------------------------------------
        # Try each executable candidate
        # -----------------------------------------------------

        for candidate in candidates:

            try:
                # -------------------------------------------------
                # Absolute executable path
                # -------------------------------------------------

                if os.path.isabs(candidate):

                    if not os.path.exists(candidate):
                        continue

                    subprocess.Popen(
                        [candidate],
                        close_fds=True,
                    )

                    print(
                        f"[Application] "
                        f"Launched: {application}"
                    )

                    return ToolResult(
                        success=True,
                        message=(
                            f"{application} is open."
                        ),
                        data={
                            "application": application,
                            "executable": candidate,
                        },
                    )

                # -------------------------------------------------
                # Search executable in PATH
                # -------------------------------------------------

                executable = shutil.which(
                    candidate
                )

                if executable:

                    subprocess.Popen(
                        [executable],
                        close_fds=True,
                    )

                    print(
                        f"[Application] "
                        f"Launched: {application}"
                    )

                    return ToolResult(
                        success=True,
                        message=(
                            f"{application} is open."
                        ),
                        data={
                            "application": application,
                            "executable": executable,
                        },
                    )

            except OSError as exc:

                print(
                    f"[Application Error] "
                    f"{application}: {exc}"
                )

                return ToolResult(
                    success=False,
                    message=(
                        f"Failed to open "
                        f"{application}: {exc}"
                    ),
                )

        # ---------------------------------------------------------
        # Application not found
        # ---------------------------------------------------------

        return ToolResult(
            success=False,
            message=(
                f"{application} was not found "
                "on this computer."
            ),
        )