from tools.registry import ToolRegistry
from tools.system.application_registry import (
    ApplicationRegistry,
)
from tools.system.applications import (
    OpenApplicationTool,
)

from execution.application_intent import (
    ApplicationIntentResolver,
)
from execution.normalizer import (
    CommandNormalizer,
)
from execution.router import CommandRouter


def main() -> None:

    print("=" * 80)
    print("JARVIS ROUTER TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # Application registry
    # ---------------------------------------------------------

    application_registry = ApplicationRegistry()

    count = application_registry.discover()

    print(
        f"[Test] Discovered {count} applications."
    )

    # ---------------------------------------------------------
    # Tool registry
    # ---------------------------------------------------------

    tool_registry = ToolRegistry()

    tool_registry.register(
        OpenApplicationTool(
            application_registry
        )
    )

    # ---------------------------------------------------------
    # Resolver
    # ---------------------------------------------------------

    resolver = ApplicationIntentResolver(
        application_registry
    )

    # ---------------------------------------------------------
    # Router
    # ---------------------------------------------------------

    router = CommandRouter(
        registry=tool_registry,
        normalizer=CommandNormalizer(),
        application_resolver=resolver,
    )

    # ---------------------------------------------------------
    # Commands
    # ---------------------------------------------------------

    commands = [
        "open chrome",
        "launch google chrome",
        "open wind hawk",
        "open wind hub",
        "open wind hook",
        "open something completely random",
    ]

    # ---------------------------------------------------------
    # Test
    # ---------------------------------------------------------

    for command in commands:

        print("\n" + "=" * 80)
        print(f"COMMAND: {command}")
        print("=" * 80)

        result = router.route(command)

        print(
            f"SUCCESS : {result.success}"
        )

        print(
            f"MESSAGE : {result.message}"
        )

        print(
            f"DATA    : {result.data}"
        )


if __name__ == "__main__":
    main()