from __future__ import annotations

import os
from pathlib import Path

from tools.system.application_model import Application


class StartMenuApplicationScanner:
    """
    Discovers Windows applications from Start Menu shortcuts.

    Sources:
        - Current user's Start Menu
        - All users' Start Menu

    The scanner resolves .lnk shortcuts to their target
    executable paths.

    It does not launch applications.
    """

    START_MENU_PATHS = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs",

        Path(os.environ.get("PROGRAMDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs",
    )

    def scan(self) -> list[Application]:
        """
        Scan Start Menu directories and return applications.
        """

        applications: dict[str, Application] = {}

        for start_menu_path in self.START_MENU_PATHS:
            self._scan_directory(
                start_menu_path,
                applications,
            )

        return sorted(
            applications.values(),
            key=lambda app: app.name.lower(),
        )

    def _scan_directory(
        self,
        directory: Path,
        applications: dict[str, Application],
    ) -> None:
        """
        Recursively scan a Start Menu directory.
        """

        if not directory.exists():
            return

        if not directory.is_dir():
            return

        try:
            entries = directory.rglob("*")
        except OSError:
            return

        for entry in entries:
            if not entry.is_file():
                continue

            if entry.suffix.lower() != ".lnk":
                continue

            application = self._read_shortcut(
                entry
            )

            if application is None:
                continue

            key = application.name.lower()

            if key in applications:
                continue

            applications[key] = application

    @staticmethod
    def _read_shortcut(
        shortcut: Path,
    ) -> Application | None:
        """
        Resolve a Windows .lnk shortcut.

        Uses Windows Script Host through PowerShell.
        """

        try:
            import subprocess

            escaped_path = str(
                shortcut
            ).replace(
                "'",
                "''",
            )

            command = (
                "$shell = New-Object -ComObject "
                "WScript.Shell; "
                f"$shortcut = $shell.CreateShortcut('{escaped_path}'); "
                "$shortcut.TargetPath; "
                "$shortcut.Arguments"
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return None

        if result.returncode != 0:
            return None

        lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        if not lines:
            return None

        target = Path(
            os.path.expandvars(
                lines[0].strip('"')
            )
        )

        if not target.is_file():
            return None

        if target.suffix.lower() != ".exe":
            return None

        name = shortcut.stem.strip()

        if not name:
            return None

        aliases = StartMenuApplicationScanner._generate_aliases(
            name
        )

        return Application(
            name=name,
            executable=str(target),
            aliases=aliases,
        )

    @staticmethod
    def _generate_aliases(
        name: str,
    ) -> tuple[str, ...]:
        """
        Generate conservative aliases.
        """

        normalized = name.lower().strip()

        aliases: set[str] = {
            normalized,
        }

        # Google Chrome
        if normalized == "google chrome":
            aliases.add("chrome")

        # Microsoft Edge
        if normalized == "microsoft edge":
            aliases.add("edge")

        # Visual Studio Code
        if (
            "visual studio code"
            in normalized
        ):
            aliases.update(
                {
                    "visual studio code",
                    "vs code",
                    "vscode",
                }
            )

        # VLC
        if normalized == "vlc media player":
            aliases.add("vlc")

        aliases.discard("")

        return tuple(
            sorted(aliases)
        )