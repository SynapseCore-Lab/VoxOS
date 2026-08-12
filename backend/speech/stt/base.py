from abc import ABC, abstractmethod
from speech.voice import VoiceCommand

class STTBase(ABC):
    """Abstract Base Class for Speech-to-Text engines."""
    
    @abstractmethod
    def transcribe(self, command: VoiceCommand) -> str:
        """
        Takes a fully captured VoiceCommand and returns the transcribed text.
        """
        pass