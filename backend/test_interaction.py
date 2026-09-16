from execution.interaction import InteractionState


def main() -> None:

    print("=" * 80)
    print("INTERACTION STATE TEST")
    print("=" * 80)

    states = [
        InteractionState.IDLE,
        InteractionState.EXECUTING,
        InteractionState.WAITING_FOR_CONFIRMATION,
        InteractionState.SPEAKING,
        InteractionState.SHUTTING_DOWN,
    ]

    for state in states:
        print(f"[State] {state.name}")

    assert InteractionState.IDLE.name == "IDLE"
    assert (
        InteractionState.WAITING_FOR_CONFIRMATION.name
        == "WAITING_FOR_CONFIRMATION"
    )

    print("\nALL INTERACTION STATE TESTS PASSED")


if __name__ == "__main__":
    main()