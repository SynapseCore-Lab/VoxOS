from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Any

from tools.base import ToolResult
from tools.registry import ToolRegistry


class ConfirmationDecision(str, Enum):
    """
    Possible responses to a confirmation request.
    """

    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class PendingConfirmation:
    """
    Represents an action that is waiting for user confirmation.
    """

    action: str
    arguments: dict[str, Any]
    prompt: str
    created_at: float


class ConfirmationManager:
    """
    Manages actions that require explicit user confirmation.

    Security rules:

    - Only one confirmation can be pending at a time.
    - Pending confirmations expire automatically.
    - Only an explicit YES executes the action.
    - NO cancels the action.
    - An unclear response cancels the action.
    - The pending action is consumed before execution.
    - The manager never executes an action that was not explicitly
      stored as pending.
    """

    DEFAULT_TIMEOUT_SECONDS = 15.0

    YES_PHRASES = {
        "yes",
        "yeah",
        "yep",
        "yup",
        "correct",
        "right",
        "sure",
        "okay",
        "ok",
        "do it",
        "go ahead",
        "confirm",
    }

    NO_PHRASES = {
        "no",
        "nope",
        "nah",
        "cancel",
        "stop",
        "don't",
        "do not",
        "never mind",
        "nevermind",
    }

    def __init__(
        self,
        registry: ToolRegistry,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds

        self._pending: PendingConfirmation | None = None

    # =========================================================
    # STATE
    # =========================================================

    @property
    def has_pending(self) -> bool:
        """
        Return True when an action is waiting for confirmation.
        """

        return self._pending is not None

    @property
    def pending(self) -> PendingConfirmation | None:
        """
        Return the current pending confirmation.

        This should normally only be used for inspection/debugging.
        """

        return self._pending

    # =========================================================
    # CREATE CONFIRMATION
    # =========================================================

    def request(
        self,
        action: str,
        arguments: dict[str, Any],
        prompt: str,
    ) -> ToolResult:
        """
        Store an action that requires confirmation.

        Any previous pending confirmation is replaced.
        """

        if not action.strip():
            return ToolResult(
                success=False,
                message="The confirmation action is invalid.",
                data={
                    "type": "confirmation_error",
                    "reason": "empty_action",
                },
            )

        self._pending = PendingConfirmation(
            action=action.strip(),
            arguments=dict(arguments),
            prompt=prompt.strip(),
            created_at=monotonic(),
        )

        return ToolResult(
            success=False,
            message=prompt,
            data={
                "type": "confirmation_required",
                "action": action,
                "arguments": dict(arguments),
            },
        )

    # =========================================================
    # HANDLE RESPONSE
    # =========================================================

    def handle_response(
        self,
        text: str,
    ) -> ToolResult:
        """
        Handle the user's response to the pending confirmation.
        """

        # -----------------------------------------------------
        # No pending confirmation
        # -----------------------------------------------------

        if self._pending is None:
            return ToolResult(
                success=False,
                message="There is nothing waiting for confirmation.",
                data={
                    "type": "no_pending_confirmation",
                },
            )

        # -----------------------------------------------------
        # Check expiration before interpreting the response.
        # -----------------------------------------------------

        if self._is_expired():
            self.clear()

            return ToolResult(
                success=False,
                message="That confirmation has expired.",
                data={
                    "type": "confirmation_expired",
                },
            )

        # -----------------------------------------------------
        # Classify response.
        # -----------------------------------------------------

        decision = self._classify_response(text)

        # -----------------------------------------------------
        # YES
        # -----------------------------------------------------

        if decision == ConfirmationDecision.YES:
            return self._approve()

        # -----------------------------------------------------
        # NO
        # -----------------------------------------------------

        if decision == ConfirmationDecision.NO:
            self.clear()

            return ToolResult(
                success=False,
                message="Okay, cancelled.",
                data={
                    "type": "confirmation_rejected",
                },
            )

        # -----------------------------------------------------
        # UNKNOWN
        # -----------------------------------------------------

        self.clear()

        return ToolResult(
            success=False,
            message=(
                "I didn't get a clear confirmation, "
                "so I cancelled it."
            ),
            data={
                "type": "confirmation_unclear",
            },
        )

    # =========================================================
    # APPROVAL
    # =========================================================

    def _approve(self) -> ToolResult:
        """
        Execute the explicitly confirmed action.
        """

        pending = self._pending

        if pending is None:
            return ToolResult(
                success=False,
                message="There is nothing waiting for confirmation.",
                data={
                    "type": "no_pending_confirmation",
                },
            )

        # -----------------------------------------------------
        # Consume the pending action BEFORE execution.
        #
        # This is intentional.
        #
        # If another event arrives while the tool is executing,
        # the same action cannot accidentally execute twice.
        # -----------------------------------------------------

        self.clear()

        # -----------------------------------------------------
        # Resolve the tool.
        # -----------------------------------------------------

        tool = self.registry.get(
            pending.action
        )

        if tool is None:
            return ToolResult(
                success=False,
                message="The confirmed action is unavailable.",
                data={
                    "type": "confirmation_execution_error",
                    "action": pending.action,
                },
            )

        # -----------------------------------------------------
        # Execute.
        # -----------------------------------------------------

        try:
            result = tool.execute(
                **pending.arguments
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                message="The confirmed action failed.",
                data={
                    "type": "confirmation_execution_error",
                    "action": pending.action,
                    "error": str(exc),
                },
            )

        return result

    # =========================================================
    # RESPONSE CLASSIFICATION
    # =========================================================

    @classmethod
    def _classify_response(
        cls,
        text: str,
    ) -> ConfirmationDecision:
        """
        Convert a short spoken response into a confirmation
        decision.

        Only exact phrases from the allow-lists are accepted.
        """

        normalized = " ".join(
            text.lower().strip().split()
        )

        if not normalized:
            return ConfirmationDecision.UNKNOWN

        if normalized in cls.YES_PHRASES:
            return ConfirmationDecision.YES

        if normalized in cls.NO_PHRASES:
            return ConfirmationDecision.NO

        return ConfirmationDecision.UNKNOWN

    # =========================================================
    # EXPIRATION
    # =========================================================

    def _is_expired(self) -> bool:
        """
        Return True if the pending confirmation has timed out.
        """

        if self._pending is None:
            return False

        age = (
            monotonic()
            - self._pending.created_at
        )

        return age > self.timeout_seconds

    # =========================================================
    # PENDING ACTION
    # =========================================================

    def pending_action(
        self,
    ) -> tuple[str, dict[str, Any]] | None:
        """
        Return the pending action and a copy of its arguments.

        Returns None when no confirmation is pending.
        """

        if self._pending is None:
            return None

        return (
            self._pending.action,
            dict(self._pending.arguments),
        )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self) -> None:
        """
        Clear the current pending confirmation.
        """

        self._pending = None