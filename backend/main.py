import asyncio
import os
import threading

from pynput import keyboard

# Core
from core.event_bus import EventBus

# Module 1: Wake Word
from speech.mic_stream import MicrophoneStream
from speech.wake_word import WakeWordDetector

# Module 2: STT
from speech.voice import VoiceEngine
from speech.stt import FasterWhisperEngine

# Module 3: TTS
from speech.tts import WindowsTTSEngine


# Suppress the Hugging Face Windows symlink warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def setup_global_hotkey(event_bus, loop):
    """Listen for F9 to bypass the wake word."""

    def on_press(key):
        if key == keyboard.Key.f9:
            print("\n[Hotkey] F9 Pressed! Waking Vox OS manually...")

            asyncio.run_coroutine_threadsafe(
                event_bus.publish(
                    "wake_word_detected",
                    {"wakeword": "keyboard_trigger"},
                ),
                loop,
            )

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    return listener


async def main():
    print("Initializing Vox OS...")

    bus = EventBus()
    loop = asyncio.get_running_loop()

    # ---------------------------------------------------------
    # Initialize Core Engines
    # ---------------------------------------------------------

    mic = MicrophoneStream()
    wake_word_engine = WakeWordDetector(bus, loop)

    voice_engine = VoiceEngine()
    stt_engine = FasterWhisperEngine()

    # TTS Engine
    tts_engine = WindowsTTSEngine()

    print("[TTS] Windows TTS engine initialized.")

    # Global F9 hotkey
    hotkey_listener = setup_global_hotkey(bus, loop)

    # ---------------------------------------------------------
    # Wake Word -> Voice Capture -> STT
    # ---------------------------------------------------------

    async def handle_wake_word(payload):
        """
        Called when the wake word or F9 hotkey is detected.
        """

        print(
            f"[Wake] Triggered by: "
            f"{payload.get('wakeword', 'unknown')}"
        )

        # Stop the continuous wake-word microphone
        mic.stop()

        # -----------------------------------------------------
        # Blocking audio/STT work runs in a background thread
        # -----------------------------------------------------

        def capture_and_transcribe():
            try:
                # Start STT microphone
                voice_engine.start()

                print("[Voice] Listening for command...")

                # Blocks until VAD detects the end of speech
                command = voice_engine.listen()

                if command:
                    print("[STT] Transcribing...")

                    # Faster-Whisper transcription
                    text = stt_engine.transcribe(command)

                    if text:
                        print(f"[STT] Recognized: {text}")

                        # Send recognized text to EventBus
                        asyncio.run_coroutine_threadsafe(
                            bus.publish(
                                "command_recognized",
                                {"text": text},
                            ),
                            loop,
                        )

            except Exception as e:
                print(
                    f"[System Error] "
                    f"Audio capture/transcription failed: {e}"
                )

            finally:
                # Cleanup STT microphone
                voice_engine.stop()

                # Signal that STT has finished
                asyncio.run_coroutine_threadsafe(
                    bus.publish(
                        "stt_finished",
                        {},
                    ),
                    loop,
                )

        # Run blocking operation outside asyncio event loop
        threading.Thread(
            target=capture_and_transcribe,
            daemon=True,
        ).start()

    bus.subscribe(
        "wake_word_detected",
        handle_wake_word,
    )

    # ---------------------------------------------------------
    # TTS Handler
    # ---------------------------------------------------------

    async def handle_command_recognized(payload):
        """
        Handle text produced by the STT engine.

        Currently this only confirms the recognized command
        through TTS.

        Later:
            STT
             ↓
            Intent Engine
             ↓
            Command Router
             ↓
            Action
             ↓
            Response
             ↓
            TTS
        """

        text = payload.get("text", "").strip()

        if not text:
            return

        print(f"[Command] {text}")

        # Temporary response while Intent Engine is not implemented
        response = f"You said: {text}"

        print(f"[TTS] Speaking: {response}")

        try:
            # pyttsx3 is blocking, so don't block asyncio.
            await asyncio.to_thread(
                tts_engine.speak,
                response,
            )

        except Exception as e:
            print(f"[TTS Error] Failed to speak response: {e}")

    bus.subscribe(
        "command_recognized",
        handle_command_recognized,
    )

    # ---------------------------------------------------------
    # Return to Wake Word Mode
    # ---------------------------------------------------------

    async def reset_listening(payload):
        """
        Resume background wake-word detection after STT
        processing has finished.
        """

        print("[System] Returning to wake-word mode...")

        wake_word_engine.resume_listening()

        mic.start(
            callback=wake_word_engine.process_audio_chunk
        )

    bus.subscribe(
        "stt_finished",
        reset_listening,
    )

    # ---------------------------------------------------------
    # System Boot
    # ---------------------------------------------------------

    print("[System] Starting wake-word listener...")

    mic.start(
        callback=wake_word_engine.process_audio_chunk
    )

    try:
        # Keep asyncio event loop alive
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass

    except KeyboardInterrupt:
        print("\nShutting down Vox OS safely...")

    finally:
        print("[System] Cleaning up...")

        mic.stop()
        voice_engine.stop()
        tts_engine.stop()
        hotkey_listener.stop()

        print("[System] Vox OS stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass