from tools.system.volume import VolumeControlTool


def main() -> None:
    tool = VolumeControlTool()

    print("=" * 70)
    print("VOLUME CONTROL TOOL TEST")
    print("=" * 70)

    print("\n[TEST] Current state")

    result = tool.controller.get_volume()
    muted = tool.controller.is_muted()

    print(f"[Audio] Volume: {result}%")
    print(f"[Audio] Muted: {muted}")

    print("\n[TEST] volume_up")

    result = tool.execute(
        operation="up",
    )

    print(result)

    print("\n[TEST] volume_down")

    result = tool.execute(
        operation="down",
    )

    print(result)

    print("\n[TEST] set volume")

    result = tool.execute(
        operation="set",
        percentage=50,
    )

    print(result)

    print("\n[TEST] mute")

    result = tool.execute(
        operation="mute",
    )

    print(result)

    print("\n[TEST] unmute")

    result = tool.execute(
        operation="unmute",
    )

    print(result)

    print("\n[TEST] invalid percentage")

    result = tool.execute(
        operation="set",
        percentage=150,
    )

    print(result)

    print("\n" + "=" * 70)
    print("VOLUME CONTROL TOOL TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()