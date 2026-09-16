from __future__ import annotations

import re

from execution.application_intent import (
    ApplicationIntentResolver,
    MatchConfidence,
)
from execution.normalizer import CommandNormalizer
from tools.base import ToolResult
from tools.registry import ToolRegistry


class CommandRouter:
    """
    Routes normalized user commands to registered tools.

    Application commands use ApplicationIntentResolver so that
    speech-recognition variations can be handled safely.

    Execution policy:

        EXACT / HIGH
            Execute immediately.

        MEDIUM
            Do not execute.
            Return a confirmation request.

        LOW / NONE
            Do not execute.
    """

    OPEN_PATTERN = re.compile(
        r"^(?:open|launch|start|run)\s+(.+?)$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        registry: ToolRegistry,
        normalizer: CommandNormalizer | None = None,
        application_resolver: ApplicationIntentResolver | None = None,
    ) -> None:
        self.registry = registry

        self.normalizer = (
            normalizer
            if normalizer is not None
            else CommandNormalizer()
        )

        self.application_resolver = (
            application_resolver
            if application_resolver is not None
            else ApplicationIntentResolver(
                self._get_application_registry()
            )
        )

    # =========================================================
    # PUBLIC ROUTING
    # =========================================================

    def route(
        self,
        text: str,
    ) -> ToolResult:

        normalized_text = self.normalizer.normalize(text)

        print(
            f"[Router] Normalized: {normalized_text}"
        )

        if not normalized_text:
            return ToolResult(
                False,
                "I didn't hear a command.",
            )

        # -----------------------------------------------------
        # Application command
        # -----------------------------------------------------

        match = self.OPEN_PATTERN.match(
            normalized_text
        )

        if match:
            return self._route_application(
                match.group(1).strip()
            )

        # -----------------------------------------------------
        # Unknown command
        # -----------------------------------------------------

        return ToolResult(
            False,
            f"I don't know how to execute "
            f"'{normalized_text}' yet.",
        )

    # =========================================================
    # APPLICATION ROUTING
    # =========================================================

    def _route_application(
        self,
        application_query: str,
    ) -> ToolResult:

        print(
            f"[Router] Application query: "
            f"{application_query}"
        )

        result = self.application_resolver.resolve(
            application_query
        )

        if result is None:
            return ToolResult(
                False,
                f"I couldn't confidently identify "
                f"the application '{application_query}'.",
                data={
                    "type": "application",
                    "query": application_query,
                    "confidence": "none",
                },
            )

        print(
            f"[Router] Candidate: "
            f"{result.application.name}"
        )

        print(
            f"[Router] Score: "
            f"{result.score:.3f}"
        )

        print(
            f"[Router] Confidence: "
            f"{result.confidence.value}"
        )

        # -----------------------------------------------------
        # EXACT / HIGH
        # -----------------------------------------------------

        if result.confidence in {
            MatchConfidence.EXACT,
            MatchConfidence.HIGH,
        }:

            return self._execute_application(
                result.application.name
            )

        # -----------------------------------------------------
        # MEDIUM
        # -----------------------------------------------------

        if result.confidence == MatchConfidence.MEDIUM:

            application_name = (
                result.application.name
            )

            return ToolResult(
                False,
                f"Did you mean {application_name}?",
                data={
                    "type": "confirmation_required",
                    "action": "open_application",
                    "query": application_query,
                    "application": application_name,
                    "executable": (
                        result.application.executable
                    ),
                    "score": result.score,
                    "confidence": (
                        result.confidence.value
                    ),
                },
            )

        # -----------------------------------------------------
        # LOW
        # -----------------------------------------------------

        return ToolResult(
            False,
            f"I couldn't confidently identify "
            f"the application '{application_query}'.",
            data={
                "type": "application",
                "query": application_query,
                "confidence": (
                    result.confidence.value
                ),
            },
        )

    # =========================================================
    # APPLICATION EXECUTION
    # =========================================================

    def _execute_application(
        self,
        application_name: str,
    ) -> ToolResult:

        tool = self.registry.get(
            "open_application"
        )

        if tool is None:
            return ToolResult(
                False,
                "The application tool is unavailable.",
            )

        return tool.execute(
            application=application_name
        )

    # =========================================================
    # REGISTRY ACCESS
    # =========================================================

    def _get_application_registry(self):

        tool = self.registry.get(
            "open_application"
        )

        if tool is None:
            raise RuntimeError(
                "The open_application tool must be "
                "registered before creating CommandRouter."
            )

        application_registry = getattr(
            tool,
            "registry",
            None,
        )

        if application_registry is None:
            raise RuntimeError(
                "The open_application tool does not "
                "expose its ApplicationRegistry."
            )

        return application_registry