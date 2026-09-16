from __future__ import annotations

import os
import re
from pathlib import Path

from tools.system.application_model import Application
from tools.system.application_scanner import (
    WindowsApplicationScanner,
)
from tools.system.start_menu_scanner import (
    StartMenuApplicationScanner,
)


class ApplicationRegistry:
    """
    Unified application registry for VoxOS.

    Combines applications discovered from:
        - Windows Registry
        - Windows Start Menu

    Applications are deduplicated by executable path.

    Provides fast lookup by:
        - Application name
        - Application alias
    """

    def __init__(self) -> None:
        self._applications: dict[str, Application] = {}
        self._aliases: dict[str, str] = {}
        self._executables: dict[str, str] = {}

    def discover(self) -> int:
        """
        Discover applications from all available sources.

        Returns:
            Number of unique applications registered.
        """

        self.clear()

        scanners = (
            WindowsApplicationScanner(),
            StartMenuApplicationScanner(),
        )

        for scanner in scanners:
            applications = scanner.scan()

            for application in applications:
                self.register(application)

        return len(self._applications)

    def register(
        self,
        application: Application,
    ) -> None:
        """
        Register an application.

        Applications pointing to the same executable are
        treated as the same underlying application.
        """

        name_key = self._normalize(
            application.name
        )

        executable_key = self._normalize_path(
            application.executable
        )

        if not name_key or not executable_key:
            return

        # -----------------------------------------------------
        # Check whether this executable already exists.
        # -----------------------------------------------------

        existing_name_key = self._executables.get(
            executable_key
        )

        if existing_name_key is not None:
            self._register_aliases(
                application,
                existing_name_key,
            )
            return

        # -----------------------------------------------------
        # Register new application.
        # -----------------------------------------------------

        self._applications[name_key] = application

        self._executables[
            executable_key
        ] = name_key

        # -----------------------------------------------------
        # Register canonical name.
        # -----------------------------------------------------

        self._aliases[name_key] = name_key

        # -----------------------------------------------------
        # Register aliases.
        # -----------------------------------------------------

        self._register_aliases(
            application,
            name_key,
        )

    def _register_aliases(
        self,
        application: Application,
        application_key: str,
    ) -> None:
        """
        Register aliases for an existing application.
        """

        # -----------------------------------------------------
        # Register application's actual name.
        # -----------------------------------------------------

        name_key = self._normalize(
            application.name
        )

        if name_key:
            self._aliases.setdefault(
                name_key,
                application_key,
            )

        # -----------------------------------------------------
        # Register explicit aliases.
        # -----------------------------------------------------

        for alias in application.aliases:
            alias_key = self._normalize(
                alias
            )

            if not alias_key:
                continue

            self._aliases.setdefault(
                alias_key,
                application_key,
            )

    def get(
        self,
        query: str,
    ) -> Application | None:
        """
        Find an application by name or alias.
        """

        key = self._normalize(
            query
        )

        if not key:
            return None

        application_key = self._aliases.get(
            key
        )

        if application_key is None:
            return None

        return self._applications.get(
            application_key
        )

    def all(self) -> list[Application]:
        """
        Return all unique registered applications.
        """

        return sorted(
            self._applications.values(),
            key=lambda app: app.name.lower(),
        )

    def names(self) -> list[str]:
        """
        Return all registered application names.
        """

        return [
            application.name
            for application in self.all()
        ]

    def count(self) -> int:
        """
        Return the number of unique applications.
        """

        return len(self._applications)

    def clear(self) -> None:
        """
        Clear all registry data.
        """

        self._applications.clear()
        self._aliases.clear()
        self._executables.clear()

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """
        Normalize text for application lookup.

        Performs:
            1. Lowercasing
            2. Whitespace normalization
            3. Removal of trailing version numbers

        Examples:

            Windhawk v1.7.3
                ->
            windhawk

            Antigravity 2.12.0
                ->
            antigravity

            Google Chrome
                ->
            google chrome
        """

        value = value.lower().strip()

        # -----------------------------------------------------
        # Normalize whitespace.
        # -----------------------------------------------------

        value = " ".join(
            value.split()
        )

        # -----------------------------------------------------
        # Remove common trailing version suffixes.
        #
        # Examples:
        #
        #   "windhawk v1.7.3"
        #       -> "windhawk"
        #
        #   "antigravity 2.12.0"
        #       -> "antigravity"
        #
        #   "app v1.2"
        #       -> "app"
        # -----------------------------------------------------

        value = re.sub(
            r"\s+v?\d+(?:\.\d+){1,4}$",
            "",
            value,
        )

        return value.strip()

    @staticmethod
    def _normalize_path(
        value: str,
    ) -> str:
        """
        Normalize an executable path for comparison.
        """

        path = os.path.normcase(
            os.path.normpath(
                str(Path(value))
            )
        )

        return path