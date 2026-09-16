from tools.system.application_registry import ApplicationRegistry
from execution.application_intent import ApplicationIntentResolver


def main() -> None:
    registry = ApplicationRegistry()

    count = registry.discover()
    print(f"Discovered {count} applications.")

    resolver = ApplicationIntentResolver(registry)

    queries = [
        "wind hub",
        "wind hawk",
        "wind hook",
        "wind hock",
    ]

    for query in queries:
        print("\n" + "=" * 90)
        print(f"QUERY: {query}")
        print("=" * 90)

        candidates = resolver.debug_candidates(
            query,
            limit=10,
        )

        if not candidates:
            print("[NO CANDIDATES]")
            continue

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"{index:02d}. "
                f"{str(candidate['application']):<35} "
                f"combined={float(candidate['combined']):.3f} "
                f"sequence={float(candidate['sequence']):.3f} "
                f"compact={float(candidate['compact']):.3f} "
                f"token={float(candidate['token']):.3f} "
                f"ngram={float(candidate['ngram']):.3f} "
                f"boundary={float(candidate['boundary']):.3f} "
                f"phonetic={float(candidate['phonetic']):.3f}"
            )


if __name__ == "__main__":
    main()