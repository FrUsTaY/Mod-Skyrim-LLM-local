from faster_whisper import WhisperModel
import os

class SpeechToText:
    def __init__(self, model_size="base", download_root="../models", device="auto", compute_type="default"):
        print(f"Загрузка STT модели {model_size}...", flush=True)
        # Убедимся, что директория для моделей существует
        os.makedirs(download_root, exist_ok=True)

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=download_root
            )
            print("STT модель успешно загружена.", flush=True)
        except Exception as e:
            print(f"Ошибка загрузки STT модели: {e}", flush=True)
            self.model = None

    def transcribe(self, audio_path):
        if not self.model:
            print("STT модель не инициализирована.")
            return ""

        if not os.path.exists(audio_path):
            print(f"Файл {audio_path} не найден для распознавания.")
            return ""

        print("Распознавание речи...", flush=True)
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5, language="ru")

            text = ""
            for segment in segments:
                text += segment.text + " "

            result = text.strip()
            print(f"Распознанный текст: {result}", flush=True)
            return result
        except Exception as e:
            print(f"Ошибка при распознавании речи: {e}", flush=True)
            return ""
