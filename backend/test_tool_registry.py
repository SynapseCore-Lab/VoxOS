from tools.registry import ToolRegistry
from tools.system.volume import VolumeControlTool


def main() -> None:
    registry = ToolRegistry()

    volume_tool = VolumeControlTool()

    registry.register(volume_tool)

    print("=" * 70)
    print("TOOL REGISTRY TEST")
    print("=" * 70)

    print("\n[Tools]")
    print(registry.names())

    print("\n[TEST] volume_control")

    tool = registry.get("volume_control")

    if tool is None:
        raise RuntimeError(
            "volume_control tool was not registered."
        )

    result = tool.execute(
        operation="set",
        percentage=50,
    )

    print(result)

    if not result.success:
        raise RuntimeError(
            "Volume control execution failed."
        )

    print("\n[PASS] volume_control registered and executed.")

    print("\n" + "=" * 70)
    print("TOOL REGISTRY TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()