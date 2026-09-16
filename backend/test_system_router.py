from execution.system_router import SystemCommandRouter
from tools.registry import ToolRegistry
from tools.system.volume import VolumeControlTool


def main() -> None:
    registry = ToolRegistry()

    volume_tool = VolumeControlTool()

    registry.register(volume_tool)

    router = SystemCommandRouter(registry)

    commands = (
        "volume up",
        "increase volume",
        "turn the volume up",
        "volume down",
        "decrease volume",
        "mute",
        "unmute",
        "set volume to 40",
        "set volume to 55 percent",
        "volume 60",
        "open chrome",
    )

    print("=" * 70)
    print("SYSTEM COMMAND ROUTER TEST")
    print("=" * 70)

    for command in commands:
        print(f"\n[COMMAND] {command}")

        result = router.route(command)

        if result is None:
            print("[ROUTER] Not handled")
        else:
            print(f"[ROUTER] {result}")

    print("\n" + "=" * 70)
    print("SYSTEM ROUTER TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()