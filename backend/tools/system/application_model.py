from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Application:
    """
    Represents an application discovered on Windows.
    """

    name: str
    executable: str
    aliases: tuple[str, ...] = field(
        default_factory=tuple
    )

    def matches(self, query: str) -> bool:
        """
        Check whether a user query matches this application.
        """

        query = query.strip().lower()

        if not query:
            return False

        if query == self.name.lower():
            return True

        return query in {
            alias.lower()
            for alias in self.aliases
        }