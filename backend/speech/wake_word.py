import openwakeword
import winsound
from openwakeword.model import Model
from openwakeword import get_pretrained_model_paths
import numpy as np
import os
import asyncio
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

class WakeWordDetector:
    def __init__(self, event_bus, loop):
        self.event_bus = event_bus
        self.loop = loop
        
        # LOWERED SENSITIVITY THRESHOLD (Tune this based on the debug output)
        self.threshold = 0.35  
        
        all_model_paths = get_pretrained_model_paths()
        jarvis_path = next((path for path in all_model_paths if "hey_jarvis" in path.lower()), None)
        
        if jarvis_path and jarvis_path.endswith('.tflite'):
            onnx_path = jarvis_path.replace('.tflite', '.onnx')
            if os.path.exists(onnx_path):
                jarvis_path = onnx_path
        
        self.model = Model(wakeword_model_paths=[jarvis_path]) 
        self.is_active = True
        
        print(f"[WakeWord] Listening for 'Hey Jarvis' (Threshold: {self.threshold})")

    def process_audio_chunk(self, audio_data: np.ndarray):
        if not self.is_active:
            return

        prediction = self.model.predict(audio_data)
        
        for wakeword, score in prediction.items():
            # DEBUG: Uncomment the line below if you want to see exactly what the model scores the room noise
            # if score > 0.1: print(f"  [Debug] Jarvis Score: {score:.2f}") 
            
            if score >= self.threshold:  
                print(f"\n[WakeWord] >>> HEY JARVIS DETECTED! (Score: {score:.2f}) <<<")
                self.is_active = False 

                # Play a quick 1000Hz chime for 150ms asynchronously to avoid blocking the main thread
                
                winsound.Beep(1000, 150)  # Frequency: 1000Hz, Duration: 150ms
                
                asyncio.run_coroutine_threadsafe(
                    self.event_bus.publish("wake_word_detected", {"wakeword": "voice_trigger"}),
                    self.loop
                )

    def resume_listening(self):
        # Reset the internal state of the model so it doesn't instantly re-trigger
        self.model.reset()
        self.is_active = True
        print("\n[WakeWord] Resumed listening for 'Hey Jarvis'...")