import os
import time
import json
import pygame
from recorder import AudioRecorder
from stt import SpeechToText
from llm_client import LLMClient
from tts import TextToSpeech

# Настройка путей (предполагается, что сервер запускается параллельно с игрой,
# и пути настроены на папку игры. Для разработки используем локальные заглушки).

# Для production нужно будет просить пользователя указать путь к папке Skyrim в config.json
MOD_INTERFACE_DIR = os.path.join("..", "skyrim_mod", "Interface", "llm_bridge")
MOD_SOUND_DIR = os.path.join("..", "skyrim_mod", "Sound", "Voice", "llm_mod")

os.makedirs(MOD_INTERFACE_DIR, exist_ok=True)
os.makedirs(MOD_SOUND_DIR, exist_ok=True)

FLAG_START = os.path.join(MOD_INTERFACE_DIR, "recording_start.flag")
FLAG_STOP = os.path.join(MOD_INTERFACE_DIR, "recording_stop.flag")
REQUEST_JSON = os.path.join(MOD_INTERFACE_DIR, "request.json")
RESPONSE_JSON = os.path.join(MOD_INTERFACE_DIR, "response.json")
TEMP_AUDIO = "temp_recording.wav"

def main():
    print("Инициализация компонентов сервера...")
    recorder = AudioRecorder(output_path=TEMP_AUDIO)
    stt = SpeechToText(download_root="../models")
    llm = LLMClient()
    tts = TextToSpeech(download_root="../models")

    # Инициализация аудиоплеера на стороне Python (в качестве обходного пути
    # для отсутствия сложного C++ SKSE плагина в игре)
    pygame.mixer.init(frequency=48000, size=-16, channels=1)

    print("Сервер запущен и ожидает сигналов от Skyrim...", flush=True)

    # Очистка старых флагов
    for file in [FLAG_START, FLAG_STOP, RESPONSE_JSON]:
        if os.path.exists(file):
            os.remove(file)

    while True:
        # 1. Ожидание начала записи
        if os.path.exists(FLAG_START) and not recorder.is_recording:
            os.remove(FLAG_START)

            # Удаляем старый ответ сразу при начале записи, чтобы игра не прочитала его
            if os.path.exists(RESPONSE_JSON):
                os.remove(RESPONSE_JSON)

            recorder.start_recording()

        # 2. Ожидание конца записи
        if os.path.exists(FLAG_STOP) and recorder.is_recording:
            os.remove(FLAG_STOP)
            recorder.stop_recording()

            # Начинаем обработку
            process_interaction(stt, llm, tts)

        time.sleep(0.1) # Polling interval

def process_interaction(stt, llm, tts):
    print("--- Начало обработки взаимодействия ---", flush=True)

    # Чтение контекста из игры
    context_data = {}
    if os.path.exists(REQUEST_JSON):
        try:
            with open(REQUEST_JSON, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
        except Exception as e:
            print(f"Ошибка чтения request.json: {e}", flush=True)

    npc_name = context_data.get("npc_name", "Неизвестный NPC")

    # STT
    user_text = stt.transcribe(TEMP_AUDIO)
    if not user_text:
        print("Речь не распознана. Возвращаем пустой ответ в игру.", flush=True)
        # Нужно вернуть что-то в response.json, чтобы Papyrus не завис
        with open(RESPONSE_JSON, 'w', encoding='utf-8') as f:
            json.dump({"text": "*Не расслышал*", "audio_file": ""}, f, ensure_ascii=False, indent=4)
        return

    # LLM
    llm_response = llm.generate_response(user_text, context_data)

    # TTS
    # Возвращаем динамическое имя файла, так как движок Skyrim агрессивно кэширует .wav файлы
    # Для полного проигрывания потребуется плагин PapyrusUtil/FuzRoDoh или аналогичный.
    audio_filename = f"response_{int(time.time())}.wav"
    audio_path = os.path.join(MOD_SOUND_DIR, audio_filename)

    success = tts.synthesize(llm_response, npc_name, audio_path)

    # Возврат результата в игру
    if success:
        # Проигрываем аудио прямо из Python, чтобы гарантировать, что игрок услышит голос,
        # даже если у него не установлены SKSE плагины типа Fuz Ro D'oh
        print("Проигрывание ответа...", flush=True)
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Ошибка при проигрывании аудио: {e}")

        response_data = {
            "text": llm_response,
            "audio_file": audio_filename
        }
        with open(RESPONSE_JSON, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
        print("Данные успешно отправлены в Skyrim (субтитры).", flush=True)

        # Ожидаем окончания проигрывания перед завершением цикла, чтобы
        # не начинать новую запись поверх говорящего NPC (если игрок зажмет кнопку)
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        # Удаляем request.json, чтобы не прочитать старые данные в следующий раз
        if os.path.exists(REQUEST_JSON):
            os.remove(REQUEST_JSON)
    else:
        print("Ошибка генерации аудио. Отправляем текст без звука.", flush=True)
        # Отправляем только текст, чтобы Papyrus не завис
        with open(RESPONSE_JSON, 'w', encoding='utf-8') as f:
            json.dump({"text": llm_response, "audio_file": ""}, f, ensure_ascii=False, indent=4)

    print("--- Обработка завершена ---", flush=True)

if __name__ == "__main__":
    main()
