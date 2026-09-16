from __future__ import annotations

import os
import winreg
from pathlib import Path

from tools.system.application_model import Application


class WindowsApplicationScanner:
    """
    Discovers launchable Windows applications.

    Discovery source:
        - Windows Registry

    The scanner:
        - Reads installed application metadata.
        - Resolves executable paths.
        - Rejects obvious installers, uninstallers,
          services, DLLs, and non-executable files.

    The scanner does NOT launch applications.
    """

    UNINSTALL_PATHS = (
        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
        r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    )

    REGISTRY_ROOTS = (
        winreg.HKEY_CURRENT_USER,
        winreg.HKEY_LOCAL_MACHINE,
    )

    INVALID_EXECUTABLE_KEYWORDS = (
        "uninstall",
        "unins",
        "installer",
        "install",
        "setup",
        "update",
        "updater",
        "service",
        "helper",
        "crash",
        "repair",
        "bootstrap",
    )

    def scan(self) -> list[Application]:
        """
        Scan Windows and return discovered applications.
        """

        applications: dict[str, Application] = {}

        for root in self.REGISTRY_ROOTS:
            for uninstall_path in self.UNINSTALL_PATHS:
                self._scan_registry_path(
                    root=root,
                    path=uninstall_path,
                    applications=applications,
                )

        return sorted(
            applications.values(),
            key=lambda app: app.name.lower(),
        )

    def _scan_registry_path(
        self,
        root: int,
        path: str,
        applications: dict[str, Application],
    ) -> None:
        """
        Scan one Windows uninstall registry path.
        """

        try:
            with winreg.OpenKey(
                root,
                path,
                0,
                winreg.KEY_READ,
            ) as uninstall_key:

                subkey_count = winreg.QueryInfoKey(
                    uninstall_key
                )[0]

                for index in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(
                            uninstall_key,
                            index,
                        )

                        with winreg.OpenKey(
                            uninstall_key,
                            subkey_name,
                            0,
                            winreg.KEY_READ,
                        ) as app_key:

                            self._read_application(
                                app_key=app_key,
                                applications=applications,
                            )

                    except OSError:
                        continue

        except OSError:
            return

    def _read_application(
        self,
        app_key: winreg.HKEYType,
        applications: dict[str, Application],
    ) -> None:
        """
        Read application metadata from a registry entry.
        """

        display_name = self._read_value(
            app_key,
            "DisplayName",
        )

        if not display_name:
            return

        install_location = self._read_value(
            app_key,
            "InstallLocation",
        )

        display_icon = self._read_value(
            app_key,
            "DisplayIcon",
        )

        executable = self._resolve_executable(
            display_icon=display_icon,
            install_location=install_location,
        )

        if not executable:
            return

        name = display_name.strip()

        if not name:
            return

        if self._is_invalid_application(
            name=name,
            executable=executable,
        ):
            return

        key = name.lower()

        if key in applications:
            return

        aliases = self._generate_aliases(name)

        applications[key] = Application(
            name=name,
            executable=executable,
            aliases=aliases,
        )

    @staticmethod
    def _read_value(
        key: winreg.HKEYType,
        value_name: str,
    ) -> str | None:
        """
        Safely read a string registry value.
        """

        try:
            value, _ = winreg.QueryValueEx(
                key,
                value_name,
            )

            if isinstance(value, str):
                return value.strip()

        except OSError:
            pass

        return None

    @classmethod
    def _is_invalid_application(
        cls,
        name: str,
        executable: str,
    ) -> bool:
        """
        Reject obvious non-launchable application entries.
        """

        executable_name = Path(
            executable
        ).name.lower()

        application_name = name.lower()

        for keyword in cls.INVALID_EXECUTABLE_KEYWORDS:
            if keyword in executable_name:
                return True

        # Registry entries representing runtimes,
        # frameworks, drivers, etc. should not become
        # normal user applications.
        runtime_keywords = (
            "runtime",
            "framework",
            "sdk",
            "driver",
            "redistributable",
            "diagnostics",
        )

        if any(
            keyword in application_name
            for keyword in runtime_keywords
        ):
            return True

        return False

    @staticmethod
    def _resolve_executable(
        display_icon: str | None,
        install_location: str | None,
    ) -> str | None:
        """
        Resolve a valid .exe path.

        Priority:
            1. DisplayIcon
            2. InstallLocation

        Only real .exe files are accepted.
        """

        # =====================================================
        # DisplayIcon
        # =====================================================

        if display_icon:
            icon_path = display_icon.strip()

            # Example:
            #
            # C:\Program Files\App\App.exe,0
            #
            if "," in icon_path:
                icon_path = icon_path.split(
                    ",",
                    1,
                )[0]

            icon_path = icon_path.strip('"')

            path = Path(
                os.path.expandvars(
                    icon_path
                )
            )

            if (
                path.is_file()
                and path.suffix.lower() == ".exe"
            ):
                return str(path)

        # =====================================================
        # InstallLocation
        # =====================================================

        if install_location:
            location = Path(
                os.path.expandvars(
                    install_location.strip('"')
                )
            )

            if location.is_dir():
                executables = sorted(
                    location.glob("*.exe"),
                    key=lambda path: path.name.lower(),
                )

                for executable in executables:
                    if not executable.is_file():
                        continue

                    if executable.suffix.lower() != ".exe":
                        continue

                    filename = executable.name.lower()

                    # Don't select an installer or updater
                    # just because it happens to be the
                    # first .exe in the directory.
                    if any(
                        keyword in filename
                        for keyword in (
                            "uninstall",
                            "unins",
                            "installer",
                            "install",
                            "setup",
                            "update",
                            "updater",
                        )
                    ):
                        continue

                    return str(executable)

        return None

    @staticmethod
    def _generate_aliases(
        name: str,
    ) -> tuple[str, ...]:
        """
        Generate conservative application aliases.
        """

        normalized = name.lower().strip()

        aliases: set[str] = {
            normalized,
        }

        # Remove " application".
        aliases.add(
            normalized.replace(
                " application",
                "",
            ).strip()
        )

        # Remove " browser".
        aliases.add(
            normalized.replace(
                " browser",
                "",
            ).strip()
        )

        # Visual Studio Code.
        if normalized.startswith(
            "microsoft visual studio code"
        ):
            aliases.update(
                {
                    "visual studio code",
                    "vs code",
                    "vscode",
                }
            )

        # Google Chrome.
        if normalized == "google chrome":
            aliases.add("chrome")

        # Microsoft Edge.
        if normalized == "microsoft edge":
            aliases.add("edge")

        aliases.discard("")

        return tuple(
            sorted(aliases)
        )