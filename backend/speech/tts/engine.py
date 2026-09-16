from __future__ import annotations

import queue
import threading
from dataclasses import dataclass

import pyttsx3

from .base import TTSEngine


@dataclass
class _SpeechRequest:
    text: str
    completed: threading.Event
    error: Exception | None = None


class WindowsTTSEngine(TTSEngine):
    """
    Windows SAPI TTS implementation.

    The pyttsx3 engine is created and used exclusively inside a
    dedicated worker thread. This avoids COM/SAPI thread-affinity
    problems when speak() is called from asyncio worker threads.
    """

    def __init__(
        self,
        rate: int = 175,
        volume: float = 1.0,
    ) -> None:
        self.rate = rate
        self.volume = volume

        self._queue: queue.Queue[_SpeechRequest | None] = queue.Queue()
        self._shutdown = threading.Event()
        self._ready = threading.Event()

        self._startup_error: Exception | None = None
        self._engine: pyttsx3.Engine | None = None

        self._worker = threading.Thread(
            target=self._worker_loop,
            name="Jarvis-TTS",
            daemon=True,
        )

        self._worker.start()

        # Wait until pyttsx3/SAPI has been initialized.
        self._ready.wait()

        if self._startup_error is not None:
            raise RuntimeError(
                "Failed to initialize Windows TTS."
            ) from self._startup_error

    def _worker_loop(self) -> None:
        """
        Own the pyttsx3 engine completely inside this thread.
        """

        try:
            engine = pyttsx3.init()

            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            self._engine = engine

        except Exception as exc:
            self._startup_error = exc
            self._ready.set()
            return

        self._ready.set()

        while not self._shutdown.is_set():
            request = self._queue.get()

            if request is None:
                break

            try:
                self._engine.say(request.text)
                self._engine.runAndWait()

            except Exception as exc:
                request.error = exc

            finally:
                request.completed.set()

        # Cleanup happens on the SAME thread that owns the engine.
        try:
            if self._engine is not None:
                self._engine.stop()
        except Exception:
            pass

        self._engine = None

    def speak(self, text: str) -> None:
        """
        Queue speech and wait until it has completed.

        This method can safely be called from any thread.
        """

        if not text or not text.strip():
            return

        if self._shutdown.is_set():
            raise RuntimeError("Windows TTS engine has been shut down.")

        request = _SpeechRequest(
            text=text.strip(),
            completed=threading.Event(),
        )

        self._queue.put(request)

        # Wait for the dedicated TTS worker.
        request.completed.wait()

        if request.error is not None:
            raise RuntimeError(
                "Windows TTS failed while speaking."
            ) from request.error

    def stop(self) -> None:
        """
        Stop the TTS worker and release the SAPI engine.
        """

        if self._shutdown.is_set():
            return

        self._shutdown.set()

        # Wake the worker if it is waiting for work.
        self._queue.put(None)

        if (
            self._worker.is_alive()
            and threading.current_thread() is not self._worker
        ):
            self._worker.join(timeout=3.0)