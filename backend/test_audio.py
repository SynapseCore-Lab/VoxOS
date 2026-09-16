from tools.system.audio import WindowsAudioController


def main() -> None:
    audio = WindowsAudioController()

    print("=" * 70)
    print("WINDOWS AUDIO TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Current state
    # ---------------------------------------------------------

    volume = audio.get_volume()
    muted = audio.is_muted()

    print(f"[Audio] Current volume: {volume}%")
    print(f"[Audio] Currently muted: {muted}")

    # ---------------------------------------------------------
    # Volume up
    # ---------------------------------------------------------

    print("\n[TEST] Volume up")

    new_volume = audio.volume_up()

    print(
        f"[Audio] Volume after increase: "
        f"{new_volume}%"
    )

    # ---------------------------------------------------------
    # Volume down
    # ---------------------------------------------------------

    print("\n[TEST] Volume down")

    new_volume = audio.volume_down()

    print(
        f"[Audio] Volume after decrease: "
        f"{new_volume}%"
    )

    # ---------------------------------------------------------
    # Set volume
    # ---------------------------------------------------------

    print("\n[TEST] Set volume to 50%")

    new_volume = audio.set_volume(50)

    print(
        f"[Audio] Volume after set: "
        f"{new_volume}%"
    )

    # ---------------------------------------------------------
    # Mute
    # ---------------------------------------------------------

    print("\n[TEST] Mute")

    audio.mute()

    print(
        f"[Audio] Muted: "
        f"{audio.is_muted()}"
    )

    # ---------------------------------------------------------
    # Unmute
    # ---------------------------------------------------------

    print("\n[TEST] Unmute")

    audio.unmute()

    print(
        f"[Audio] Muted: "
        f"{audio.is_muted()}"
    )

    print("\n" + "=" * 70)
    print("AUDIO TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()