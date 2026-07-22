import torch
import torchaudio
import os
import hashlib

class TextToSpeech:
    def __init__(self, download_root="../models"):
        print("Загрузка модели Silero TTS...", flush=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Загрузка русской модели Silero TTS
        # Используем локальный кэш, если возможно
        torch.hub.set_dir(download_root)
        self.model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker='v3_1_ru'
        )
        self.model.to(self.device)
        print(f"Silero TTS загружена на устройство: {self.device}", flush=True)

        # Доступные русские голоса в модели v3_1_ru
        self.available_speakers = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']
        self.sample_rate = 48000

    def _get_speaker_for_npc(self, npc_name):
        """
        Назначает псевдослучайный, но постоянный голос на основе имени NPC.
        Хэшируем имя NPC и берем остаток от деления на количество доступных голосов.
        """
        if not npc_name:
            return self.available_speakers[0]

        hash_val = int(hashlib.md5(npc_name.encode('utf-8')).hexdigest(), 16)
        speaker_idx = hash_val % len(self.available_speakers)
        return self.available_speakers[speaker_idx]

    def synthesize(self, text, npc_name, output_path="response.wav"):
        """
        Генерирует аудио из текста и сохраняет в .wav файл.
        """
        if not text:
            print("Нет текста для генерации речи.", flush=True)
            return False

        speaker = self._get_speaker_for_npc(npc_name)
        print(f"Генерация речи для '{npc_name}' (Голос: {speaker})...", flush=True)

        try:
            # Silero ожидает текст с ударениями для идеального звучания,
            # но справляется и с обычным текстом, хотя иногда может ошибаться в ударениях.
            # Также модель имеет ограничение на длину строки, для длинных текстов нужна разбивка.
            # Так как мы просим LLM отвечать коротко (max_tokens=150), обычно это не проблема.
            audio = self.model.apply_tts(
                text=text,
                speaker=speaker,
                sample_rate=self.sample_rate
            )

            # Сохранение файла
            torchaudio.save(output_path, audio.unsqueeze(0).cpu(), self.sample_rate)
            print(f"Аудио успешно сохранено в {output_path}", flush=True)
            return True
        except Exception as e:
            print(f"Ошибка генерации TTS: {e}", flush=True)
            return False

if __name__ == "__main__":
    # Test script
    # tts = TextToSpeech()
    # tts.synthesize("Приветствую тебя, путник! Что привело тебя в Вайтран?", "Балгруф Старший", "test_tts.wav")
    pass
