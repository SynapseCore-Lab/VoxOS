from faster_whisper import WhisperModel
from speech.voice import VoiceCommand
from .base import STTBase


class FasterWhisperEngine(STTBase):
    def __init__(self, model_size="base.en", device="cpu", compute_type="int8"):
        """
        Initializes the CTranslate2 Whisper model.
        compute_type="int8" drops memory usage to ~1GB, perfect for CPU.
        """
        print(
            f"[STT] Loading faster-whisper model ({model_size}) on {device.upper()}..."
        )
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[STT] Model loaded successfully.")

    def transcribe(self, command: VoiceCommand) -> str:
        """Transcribes the audio payload from a VoiceCommand."""
        print("[STT] Transcribing audio payload...")

        # Whisper natively requires float32 arrays bounded between -1.0 and 1.0.
        # Because voice.py captures audio in float32, we pass it directly.
        audio_data = command.audio

        try:
            # beam_size=5 ensures high accuracy for short, punchy desktop commands
            segments, _ = self.model.transcribe(audio_data, beam_size=5, language="en")

            # Stitch the segments together
            text = "".join([segment.text for segment in segments]).strip()

            if text:
                print(f"\n[USER]: {text}")
                return text
            else:
                print("[STT] No speech detected in the audio payload.")
                return ""

        except Exception as e:
            print(f"[STT Error] Transcription failed: {e}")
            return ""
