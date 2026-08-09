import asyncio
import winsound
from pynput import keyboard
from core.event_bus import EventBus
from speech.mic_stream import MicrophoneStream
from speech.wake_word import WakeWordDetector

# If you have Module 2 ready, you would import it here:
# from speech.stt import SpeechToTextEngine

def setup_global_hotkey(event_bus, loop):
    """Listens for the F9 key to manually wake Jarvis."""
    
    def on_press(key):
        if key == keyboard.Key.f9:
            print("\n[Hotkey] F9 Pressed! Waking Jarvis up manually...")
            # Fire the exact same event the voice engine fires
            # Play a quick 1000Hz chime for 150ms asynchronously to avoid blocking the main thread
                            
            winsound.Beep(1000, 150)  # Frequency: 1000Hz, Duration: 150ms
            asyncio.run_coroutine_threadsafe(
                event_bus.publish("wake_word_detected", {"wakeword": "keyboard_trigger"}),
                loop
            )

    # Start the pynput listener in a background thread
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    print("[System] Global Hotkey Active: Press 'F9' to manually wake Jarvis.")
    return listener

async def main():
    bus = EventBus()
    loop = asyncio.get_running_loop()
    
    mic = MicrophoneStream()
    wake_word_engine = WakeWordDetector(bus, loop)
    
    # Initialize the manual hotkey
    hotkey_listener = setup_global_hotkey(bus, loop)
    
    # ---------------------------------------------------------
    # STT Module 2 Placeholder (For when you integrate it later)
    # ---------------------------------------------------------
    # stt_engine = SpeechToTextEngine(bus, loop, mic)
    # async def reset_listening(payload):
    #     wake_word_engine.resume_listening()
    #     mic.set_callback(wake_word_engine.process_audio_chunk)
    # bus.subscribe("stt_finished", reset_listening)
    
    # Start the microphone stream routed to the wake word engine
    mic.start(callback=wake_word_engine.process_audio_chunk)

    try:
        # Keep the system running
        while True:
            await asyncio.sleep(1)
    except asyncio.exceptions.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\nShutting down Jarvis...")
    finally:
        mic.stop()
        hotkey_listener.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass