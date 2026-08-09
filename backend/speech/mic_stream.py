import sounddevice as sd
import numpy as np
import threading
import queue

class MicrophoneStream:
    def __init__(self, chunk_size=1280, rate=16000, device_index=None):
        self.chunk_size = chunk_size
        self.rate = rate
        self.device_index = device_index
        self.stream = None
        self.is_listening = False
        
        self.audio_queue = queue.Queue()
        self.worker_thread = None
        self.current_callback = None

    def list_devices(self):
        """Helper to print available microphones"""
        print("\n--- Available Audio Devices ---")
        print(sd.query_devices())
        print("-------------------------------\n")

    def set_callback(self, callback):
        self.current_callback = callback

    def start(self, callback):
        self.is_listening = True
        self.current_callback = callback

        self.worker_thread = threading.Thread(
            target=self._process_queue_in_background, 
            daemon=True
        )
        self.worker_thread.start()

        def audio_callback(indata, frames, time, status):
            if status: print(f"[Mic Warning] {status}")
            if self.is_listening:
                self.audio_queue.put(indata.flatten())

        self.stream = sd.InputStream(
            device=self.device_index, # Allows custom mic selection
            samplerate=self.rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk_size,
            callback=audio_callback
        )
        self.stream.start()
        print("[Mic] Microphone stream started...")

    def _process_queue_in_background(self):
        while self.is_listening:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                if self.current_callback:
                    self.current_callback(audio_data)
            except queue.Empty:
                continue

    def stop(self):
        self.is_listening = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)