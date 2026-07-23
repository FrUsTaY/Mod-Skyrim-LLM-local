import sounddevice as sd
import numpy as np
from scipy.io import wavfile

class AudioRecorder:
    def __init__(self, output_path="temp_recording.wav", sample_rate=16000, channels=1):
        self.output_path = output_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.frames = []
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            pass  # Можно добавить логирование при необходимости
        if self.is_recording:
            self.frames.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            return

        self.frames = []
        self.is_recording = True

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback
        )
        self.stream.start()
        print("🎙️ Запись звука начата...", flush=True)

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("🛑 Запись звука завершена.", flush=True)

        if self.frames:
            # Конвертируем список массивов в один numpy массив
            recording = np.concatenate(self.frames, axis=0)

            # Конвертируем в int16 для лучшей совместимости WAV формата
            recording_int16 = np.int16(recording * 32767)

            wavfile.write(self.output_path, self.sample_rate, recording_int16)
        else:
            print("⚠️ Нет записанных аудиоданных.", flush=True)
