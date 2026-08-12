from __future__ import annotations

import queue
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

import numpy as np
import sounddevice as sd


# ============================================================
# Configuration
# ============================================================

SAMPLE_RATE = 16_000
CHANNELS = 1

# Audio is processed in small chunks.
BLOCK_SIZE = 512

# RMS threshold for the basic VAD.
# This is intentionally configurable because microphones
# have different noise levels.
VAD_THRESHOLD = 0.010

# How long silence must continue before we consider the
# utterance finished.
SILENCE_DURATION = 0.8

# Maximum length of one utterance.
MAX_UTTERANCE_DURATION = 15.0


# ============================================================
# Data Models
# ============================================================


@dataclass
class AudioChunk:
    """A single chunk of microphone audio."""

    data: np.ndarray
    timestamp: float


@dataclass
class VoiceCommand:
    """
    Represents a completed voice command.

    STT will populate `text` later.
    """

    audio: np.ndarray
    sample_rate: int
    timestamp: float
    text: Optional[str] = None


class VoiceState(Enum):
    """State of the voice engine."""

    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()


# ============================================================
# Voice Engine
# ============================================================


class VoiceEngine:
    """
    Phase 2 voice engine.

    Responsibilities:
        - Capture microphone audio
        - Detect speech
        - Collect an utterance
        - Return a VoiceCommand

    It intentionally does NOT:
        - Understand commands
        - Launch applications
        - Execute Windows commands
        - Call an LLM

    Those responsibilities belong to later layers.
    """

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        block_size: int = BLOCK_SIZE,
        vad_threshold: float = VAD_THRESHOLD,
        silence_duration: float = SILENCE_DURATION,
        max_utterance_duration: float = MAX_UTTERANCE_DURATION,
    ) -> None:

        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.vad_threshold = vad_threshold
        self.silence_duration = silence_duration
        self.max_utterance_duration = max_utterance_duration

        self.state = VoiceState.IDLE

        self._audio_queue: queue.Queue[AudioChunk] = queue.Queue()

        self._stream: Optional[sd.InputStream] = None

        self._running = False

    # --------------------------------------------------------
    # Audio Callback
    # --------------------------------------------------------

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info,
        status: sd.CallbackFlags,
    ) -> None:
        """
        Called by sounddevice whenever microphone audio
        becomes available.

        IMPORTANT:
        Keep this function extremely lightweight.
        Do not perform STT or AI processing here.
        """

        if status:
            print(f"[Audio] {status}")

        chunk = AudioChunk(
            data=indata.copy(),
            timestamp=time.monotonic(),
        )

        self._audio_queue.put(chunk)

    # --------------------------------------------------------
    # VAD
    # --------------------------------------------------------

    def _calculate_rms(self, audio: np.ndarray) -> float:
        """Calculate RMS volume of an audio chunk."""

        if audio.size == 0:
            return 0.0

        return float(np.sqrt(np.mean(np.square(audio))))

    def _is_speech(self, audio: np.ndarray) -> bool:
        # """
        # Very simple energy-based Voice Activity Detection.

        # This is intentionally a basic implementation for
        # Phase 2. It can later be replaced with WebRTC VAD,
        # Silero VAD, or another dedicated VAD engine.
        # """

        rms = self._calculate_rms(audio)

        return rms >= self.vad_threshold

        """
        Energy-based Voice Activity Detection with live debug logging.
        """
        # rms = self._calculate_rms(audio)

        # DEBUG PRINT: Shows real-time audio volume in the console
        # comment this out once calibrated!
        # if rms > 0.001:  # Filter out complete zero buffers
        #     print(
        #         f"[Mic Debug] Live RMS: {rms:.5f} | Threshold: {self.vad_threshold:.5f}"
        #     )

        # return rms >= self.vad_threshold

    # --------------------------------------------------------
    # Stream Management
    # --------------------------------------------------------

    def start(self) -> None:
        """Start microphone capture."""

        if self._running:
            return

        print("[Voice] Starting microphone...")

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._audio_callback,
        )

        self._stream.start()

        self._running = True
        self.state = VoiceState.IDLE

        print("[Voice] Microphone ready.")

    def stop(self) -> None:
        """Stop microphone capture."""

        if not self._running:
            return

        print("[Voice] Stopping microphone...")

        self._running = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.state = VoiceState.IDLE

        print("[Voice] Microphone stopped.")

    # --------------------------------------------------------
    # Queue
    # --------------------------------------------------------

    def _get_audio_chunk(self, timeout: float = 1.0) -> Optional[AudioChunk]:
        """Get the next microphone chunk."""

        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # --------------------------------------------------------
    # Listen
    # --------------------------------------------------------

    def listen(self) -> Optional[VoiceCommand]:
        """
        Wait for speech, collect the utterance, and return it.

        Current pipeline:

            Microphone
                ↓
            sounddevice
                ↓
            RMS VAD
                ↓
            Utterance
                ↓
            VoiceCommand

        STT will be connected later.
        """

        if not self._running:
            raise RuntimeError("VoiceEngine is not running. Call start() first.")

        print("[Voice] Listening...")

        self.state = VoiceState.LISTENING

        audio_chunks: list[np.ndarray] = []

        speech_started = False
        speech_start_time: Optional[float] = None
        last_speech_time: Optional[float] = None

        while self._running:
            chunk = self._get_audio_chunk()

            if chunk is None:
                continue

            audio = chunk.data

            speaking = self._is_speech(audio)

            # ------------------------------------------------
            # Speech has started
            # ------------------------------------------------

            if speaking and not speech_started:
                speech_started = True
                speech_start_time = chunk.timestamp
                last_speech_time = chunk.timestamp

                audio_chunks.append(audio)

                print("[Voice] Speech detected.")

                continue

            # ------------------------------------------------
            # User is still speaking
            # ------------------------------------------------

            if speech_started:
                audio_chunks.append(audio)

                if speaking:
                    last_speech_time = chunk.timestamp

                # --------------------------------------------
                # Check maximum utterance duration
                # --------------------------------------------

                if speech_start_time is not None:
                    duration = chunk.timestamp - speech_start_time

                    if duration >= self.max_utterance_duration:
                        print("[Voice] Maximum utterance duration reached.")

                        break

                # --------------------------------------------
                # Check silence duration
                # --------------------------------------------

                if last_speech_time is not None:
                    silence_time = chunk.timestamp - last_speech_time

                    if silence_time >= self.silence_duration:
                        print("[Voice] Speech ended.")

                        break

        # ----------------------------------------------------
        # No audio collected
        # ----------------------------------------------------

        if not audio_chunks:
            self.state = VoiceState.IDLE

            return None

        # ----------------------------------------------------
        # Combine chunks
        # ----------------------------------------------------

        utterance = np.concatenate(audio_chunks, axis=0).flatten()
        self.state = VoiceState.PROCESSING

        print(f"[Voice] Captured {len(utterance) / self.sample_rate:.2f}s of audio.")

        command = VoiceCommand(
            audio=utterance,
            sample_rate=self.sample_rate,
            timestamp=time.time(),
        )

        self.state = VoiceState.IDLE

        return command

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    def run(self) -> None:
        """
        Run the voice engine continuously.

        This is only a development/test loop.
        Phase 3 will consume VoiceCommand objects.
        """

        self.start()

        try:
            while self._running:
                command = self.listen()

                if command is None:
                    continue

                duration = len(command.audio) / self.sample_rate

                print(f"[Voice] Command captured ({duration:.2f}s)")

                # --------------------------------------------
                # STT will be connected here later.
                # --------------------------------------------

                print("[Voice] Ready for Speech-to-Text.")

        except KeyboardInterrupt:
            print("\n[Voice] Interrupted by user.")

        finally:
            self.stop()


# ============================================================
# Development Entry Point
# ============================================================


def main() -> None:
    """Development entry point."""

    engine = VoiceEngine()

    engine.run()


if __name__ == "__main__":
    main()
