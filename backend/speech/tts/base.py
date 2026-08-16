from abc import ABC, abstractmethod


class TTSEngine(ABC):
    """Abstract interface for text-to-speech engines."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Convert text to speech."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stop active speech."""
        raise NotImplementedError