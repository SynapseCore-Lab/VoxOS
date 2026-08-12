import asyncio
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

import os

# Suppress the Hugging Face Windows symlink warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def setup_global_hotkey(event_bus, loop):
    """Listens for the F9 key to bypass the wake word."""

    def on_press(key):
        if key == keyboard.Key.f9:
            print("\n[Hotkey] F9 Pressed! Waking Vox OS manually...")
            asyncio.run_coroutine_threadsafe(
                event_bus.publish(
                    "wake_word_detected", {"wakeword": "keyboard_trigger"}
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

    hotkey_listener = setup_global_hotkey(bus, loop)

    # ---------------------------------------------------------
    # Orchestration: Wake Word -> Voice Capture -> STT
    # ---------------------------------------------------------
    async def handle_wake_word(payload):
        # 1. Stop the continuous background wake word microphone
        mic.stop()

        # 2. Run the blocking voice capture in a dedicated background thread
        def capture_and_transcribe():
            try:
                # Start STT mic stream
                voice_engine.start()

                # Blocks until the user finishes their sentence (VAD silence cutoff)
                command = voice_engine.listen()

                if command:
                    # Execute Faster-Whisper Transcription
                    text = stt_engine.transcribe(command)

                    if text:
                        # Send text to the (Future) Intent Router
                        asyncio.run_coroutine_threadsafe(
                            bus.publish("command_recognized", {"text": text}), loop
                        )
            except Exception as e:
                print(f"[System Error] Audio capture/transcription failed: {e}")
            finally:
                # Cleanup STT mic
                voice_engine.stop()

                # 3. Signal the system to return to Wake Word mode
                asyncio.run_coroutine_threadsafe(bus.publish("stt_finished", {}), loop)

        # Dispatch the thread so asyncio continues routing other events
        threading.Thread(target=capture_and_transcribe, daemon=True).start()

    # Bind the handoff logic to the event bus
    bus.subscribe("wake_word_detected", handle_wake_word)

    # ---------------------------------------------------------
    # Orchestration: Return to Idle
    # ---------------------------------------------------------
    async def reset_listening(payload):
        """Called when STT is done to resume background wake word detection."""
        wake_word_engine.resume_listening()
        mic.start(callback=wake_word_engine.process_audio_chunk)

    bus.subscribe("stt_finished", reset_listening)

    # ---------------------------------------------------------
    # System Boot
    # ---------------------------------------------------------
    # Start the system with the Wake Word engine in control of the hardware
    mic.start(callback=wake_word_engine.process_audio_chunk)

    try:
        # Keep the main async loop alive infinitely
        while True:
            await asyncio.sleep(1)

    except asyncio.exceptions.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\nShutting down Vox OS safely...")
    finally:
        mic.stop()
        voice_engine.stop()
        hotkey_listener.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
