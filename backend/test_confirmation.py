from tools.registry import ToolRegistry
from tools.system.application_registry import (
    ApplicationRegistry,
)
from tools.system.applications import (
    OpenApplicationTool,
)

from execution.confirmation import (
    ConfirmationManager,
)


def build_manager() -> ConfirmationManager:

    application_registry = ApplicationRegistry()
    application_registry.discover()

    registry = ToolRegistry()

    registry.register(
        OpenApplicationTool(
            application_registry
        )
    )

    return ConfirmationManager(
        registry=registry
    )


def print_result(label: str, result) -> None:

    print("\n" + "-" * 80)
    print(label)
    print("-" * 80)

    print(f"SUCCESS : {result.success}")
    print(f"MESSAGE : {result.message}")
    print(f"DATA    : {result.data}")


def main() -> None:

    manager = build_manager()

    # =========================================================
    # TEST 1
    # Request confirmation
    # =========================================================

    result = manager.request(
        action="open_application",
        arguments={
            "application": "Windhawk v1.7.3"
        },
        prompt="Did you mean Windhawk v1.7.3?",
    )

    print_result(
        "TEST 1 — Request confirmation",
        result,
    )

    assert manager.has_pending

    # =========================================================
    # TEST 2
    # Reject
    # =========================================================

    result = manager.handle_response("no")

    print_result(
        "TEST 2 — Reject confirmation",
        result,
    )

    assert not manager.has_pending

    # =========================================================
    # TEST 3
    # Request again
    # =========================================================

    result = manager.request(
        action="open_application",
        arguments={
            "application": "Windhawk v1.7.3"
        },
        prompt="Did you mean Windhawk v1.7.3?",
    )

    print_result(
        "TEST 3 — Request confirmation again",
        result,
    )

    assert manager.has_pending

    # =========================================================
    # TEST 4
    # Unclear response must NOT execute
    # =========================================================

    result = manager.handle_response(
        "open chrome"
    )

    print_result(
        "TEST 4 — Unclear response",
        result,
    )

    assert not manager.has_pending

    # =========================================================
    # TEST 5
    # Confirm
    # =========================================================

    result = manager.request(
        action="open_application",
        arguments={
            "application": "Windhawk v1.7.3"
        },
        prompt="Did you mean Windhawk v1.7.3?",
    )

    print_result(
        "TEST 5 — Request confirmation",
        result,
    )

    result = manager.handle_response("yes")

    print_result(
        "TEST 6 — Confirm",
        result,
    )

    assert result.success
    assert not manager.has_pending

    print("\n" + "=" * 80)
    print("ALL CONFIRMATION TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()