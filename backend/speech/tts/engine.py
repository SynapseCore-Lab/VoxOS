import threading

import pyttsx3

from .base import TTSEngine


class WindowsTTSEngine(TTSEngine):
    """Windows SAPI-based text-to-speech implementation."""

    def __init__(
        self,
        rate: int = 175,
        volume: float = 1.0,
    ) -> None:
        self.rate = rate
        self.volume = volume

        self._engine = pyttsx3.init()
        self._lock = threading.Lock()

        self._configure()

    def _configure(self) -> None:
        self._engine.setProperty("rate", self.rate)
        self._engine.setProperty("volume", self.volume)

    def speak(self, text: str) -> None:
        """Speak text synchronously."""
        if not text or not text.strip():
            return

        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()

    def stop(self) -> None:
        """Stop active speech."""
        with self._lock:
            self._engine.stop()