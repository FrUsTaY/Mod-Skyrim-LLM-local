import os
import sys
import json
import urllib.request
import zipfile
import shutil
import subprocess

CONFIG_PATH = "config.json"
MOD_SOURCE_DIR = "../skyrim_mod"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"skyrim_path": ""}

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def set_skyrim_path(config):
    clear_console()
    print("=== Настройка пути к игре ===")
    print("Укажите полный путь к папке, где находится файл SkyrimSE.exe")
    print("Пример: D:\\Games\\Skyrim Special Edition")
    print("Или напишите 0, чтобы вернуться назад.")
    print("-" * 30)

    path = input("Ваш путь: ").strip().strip('"')
    if path == "0":
        return config

    if os.path.exists(os.path.join(path, "SkyrimSE.exe")):
        config["skyrim_path"] = path
        save_config(config)
        print("\n[УСПЕХ] Путь сохранен!")
    else:
        print("\n[ОШИБКА] Файл SkyrimSE.exe не найден по этому пути. Проверьте правильность.")

    input("\nНажмите Enter для продолжения...")
    return config

def download_and_extract(url, extract_to, desc):
    print(f"\nСкачивание {desc}...")
    temp_zip = "temp_download.zip"
    try:
        # User-Agent нужен, чтобы GitHub не блокировал запросы
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_zip, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        print(f"Распаковка {desc}...")
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Некоторые архивы содержат корневую папку, нам нужно извлекать содержимое Data
            zip_ref.extractall(extract_to)

        os.remove(temp_zip)
        print(f"[УСПЕХ] {desc} установлен!")
        return True
    except Exception as e:
        print(f"[ОШИБКА] Не удалось скачать/установить {desc}. Ошибка: {e}")
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        return False

def install_mods(config):
    clear_console()
    print("=== Установка модов и зависимостей ===")

    game_path = config.get("skyrim_path", "")
    if not game_path or not os.path.exists(game_path):
        print("[ОШИБКА] Сначала укажите правильный путь к игре (Пункт 1).")
        input("\nНажмите Enter для возврата...")
        return

    print("Внимание: Это установит SKSE, JContainers и скрипты мода прямо в папку с игрой.")
    ans = input("Продолжить? (y/n): ").lower()
    if ans != 'y':
        return

    # 1. Установка скриптов мода (Копирование из нашего репозитория)
    print("\nКопирование файлов нашего мода...")
    target_data = os.path.join(game_path, "Data")
    os.makedirs(target_data, exist_ok=True)

    try:
        # Копируем структуру skyrim_mod в Data
        for root, dirs, files in os.walk(MOD_SOURCE_DIR):
            for file in files:
                src_path = os.path.join(root, file)
                # Вычисляем относительный путь от skyrim_mod
                rel_path = os.path.relpath(src_path, MOD_SOURCE_DIR)
                dest_path = os.path.join(target_data, rel_path)

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
        print("[УСПЕХ] Файлы мода скопированы.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось скопировать скрипты: {e}")

    # 2. Установка JContainers
    jcont_url = "https://github.com/FrUsTaY/public-releases/releases/download/mod-file-to-skyrim/JContainers64-v4.2.13.1.zip"
    # Архив JContainers уже содержит нужные файлы в корне, распаковываем в корень игры
    download_and_extract(jcont_url, game_path, "JContainers SE")

    # 3. Установка SKSE
    # Для версии 1.6.1170 нам нужен SKSE64 2.2.6
    skse_url = "https://github.com/FrUsTaY/public-releases/releases/download/mod-file-to-skyrim/skse64_2_02_06.zip"
    # Архив SKSE содержит файлы в корне, распаковываем в корень игры
    download_and_extract(skse_url, game_path, "SKSE64")

    input("\nНажмите Enter для возврата...")

def check_dependencies(config):
    clear_console()
    print("=== Проверка установленных зависимостей ===")

    game_path = config.get("skyrim_path", "")
    if not game_path or not os.path.exists(game_path):
        print("[ОШИБКА] Сначала укажите правильный путь к игре (Пункт 1).")
        input("\nНажмите Enter для возврата...")
        return

    skse_path = os.path.join(game_path, "skse64_loader.exe")
    jcont_path = os.path.join(game_path, "Data", "SKSE", "Plugins", "JContainers64.dll")

    if os.path.exists(skse_path):
        print("[УСПЕХ] SKSE найден!")
    else:
        print("[ОШИБКА] SKSE не найден! (skse64_loader.exe отсутствует)")

    if os.path.exists(jcont_path):
        print("[УСПЕХ] JContainers найден!")
    else:
        print("[ОШИБКА] JContainers не найден! (JContainers64.dll отсутствует)")

    input("\nНажмите Enter для возврата...")

def check_creation_kit(config):
    clear_console()
    print("=== Проверка установленного Creation Kit ===")

    game_path = config.get("skyrim_path", "")
    if not game_path or not os.path.exists(game_path):
        print("[ОШИБКА] Сначала укажите правильный путь к игре (Пункт 1).")
        input("\nНажмите Enter для возврата...")
        return

    ck_path = os.path.join(game_path, "CreationKit.exe")

    if os.path.exists(ck_path):
        print("[УСПЕХ] Creation Kit найден!")
    else:
        print("[ОШИБКА] Creation Kit не найден в папке с игрой!")
        print("\nЧто нужно сделать:")
        print("1. Откройте Steam и перейдите в библиотеку.")
        print("2. Включите отображение 'Инструментов' (Tools) в фильтре поиска.")
        print("3. Найдите и установите 'Skyrim Special Edition: Creation Kit'.")
        print("4. Убедитесь, что он устанавливается в ту же папку, где находится SkyrimSE.exe.")
        print("\n[!] ДЛЯ ИГРОКОВ С ПИРАТСКОЙ ВЕРСИЕЙ ИГРЫ:")
        print("Steam скачает Creation Kit в свою папку (обычно это C:\\Program Files (x86)\\Steam\\steamapps\\common\\Skyrim Special Edition).")
        print("Вам нужно зайти в эту папку Steam, скопировать оттуда абсолютно все файлы и вставить их в реальную папку с вашей игрой.")

    input("\nНажмите Enter для возврата...")

def check_lm_studio():
    clear_console()
    print("=== Проверка LM Studio ===")
    import urllib.error

    try:
        req = urllib.request.Request("http://127.0.0.1:1234/v1/models")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("[УСПЕХ] Сервер LM Studio запущен и отвечает!")
            if data.get("data"):
                print(f"Загруженная модель: {data['data'][0]['id']}")
            else:
                print("ВНИМАНИЕ: Сервер работает, но модель не загружена. Загрузите Qwen 3 или Gemma 3 в интерфейсе программы.")
    except urllib.error.URLError:
        print("[ОШИБКА] LM Studio не отвечает на порту 1234.")
        print("\nЧто нужно сделать:")
        print("1. Скачайте LM Studio с официального сайта: https://lmstudio.ai/")
        print("2. Запустите программу и скачайте модель (например, Qwen или Gemma).")
        print("3. Перейдите во вкладку 'Local Server' (значок со стрелочками слева).")
        print("4. Выберите скачанную модель сверху и нажмите кнопку 'Start Server'.")

    input("\nНажмите Enter для возврата...")

def start_server(config):
    clear_console()
    print("=== Запуск сервера мода ===")

    if not config.get("skyrim_path"):
        print("[ОШИБКА] Укажите путь к игре (Пункт 1) перед запуском сервера.")
        input("\nНажмите Enter для возврата...")
        return

    print("Запускаем нейросети (Whisper и Silero). Это может занять секунд 30...")
    print("Окно останется открытым. Чтобы остановить мод, просто закройте это окно.")
    print("-" * 50)

    # Запускаем main.py
    try:
        subprocess.run([sys.executable, "src/main.py"])
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем.")
    except Exception as e:
        print(f"\n[ОШИБКА] Сервер упал с ошибкой: {e}")

    input("\nНажмите Enter для возврата в меню...")

def main_menu():
    config = load_config()

    while True:
        clear_console()
        print("===================================================")
        print("      Skyrim Local LLM Voice - Панель управления   ")
        print("===================================================")

        path_status = config.get("skyrim_path", "НЕ УКАЗАН")
        print(f"Путь к Skyrim: {path_status}\n")

        print("1. Указать путь к папке с игрой Skyrim")
        print("2. Установить зависимости мода в игру (SKSE, JContainers)")
        print("3. Проверить установленные зависимости в игре")
        print("4. Проверить установлен ли Creation Kit")
        print("5. Проверить статус нейросети (LM Studio)")
        print("6. ЗАПУСТИТЬ СЕРВЕР (Голос и Чат)")
        print("0. Выход")
        print("-" * 50)

        choice = input("Выберите пункт меню: ").strip()

        if choice == '1':
            config = set_skyrim_path(config)
        elif choice == '2':
            install_mods(config)
        elif choice == '3':
            check_dependencies(config)
        elif choice == '4':
            check_creation_kit(config)
        elif choice == '5':
            check_lm_studio()
        elif choice == '6':
            start_server(config)
        elif choice == '0':
            print("До свидания!")
            sys.exit(0)
        else:
            print("Неверный выбор. Попробуйте еще раз.")
            import time
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
