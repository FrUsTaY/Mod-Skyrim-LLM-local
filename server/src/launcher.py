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

    # 2. Установка JContainers (Скачиваем последнюю версию с Github)
    jcont_url = "https://github.com/ryobg/JContainers/releases/download/v4.2.9/JContainers.SE.v4.2.9.zip"
    download_and_extract(jcont_url, target_data, "JContainers SE")

    # 3. Установка SKSE
    # Для версии 1.6.1170 нам нужен SKSE64 2.2.6
    skse_url = "https://skse.silverlock.org/beta/skse64_2_02_06.7z"
    print("\n[ИНФО] Для SKSE требуется ручная установка из-за формата .7z, который сложно распаковать встроенными средствами Python.")
    print(f"Пожалуйста, скачайте архив: {skse_url}")
    print("И распакуйте содержимое папки 'skse64_2_02_06' прямо в корень игры:")
    print(game_path)

    input("\nНажмите Enter, когда прочитаете...")

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
        print("3. Проверить статус нейросети (LM Studio)")
        print("4. ЗАПУСТИТЬ СЕРВЕР (Голос и Чат)")
        print("0. Выход")
        print("-" * 50)

        choice = input("Выберите пункт меню: ").strip()

        if choice == '1':
            config = set_skyrim_path(config)
        elif choice == '2':
            install_mods(config)
        elif choice == '3':
            check_lm_studio()
        elif choice == '4':
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
