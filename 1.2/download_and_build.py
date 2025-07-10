import requests
import os
import shutil
import zipfile
import csv
import json
import subprocess
import sys
import argparse

# Конфигурация
API_URL_2 = "http://95.31.15.222:8091/v2/projects/2/export"
API_KEY_2 = "tgpak_gjpti33vnbrdazjyojxwm3bwoaztk3ddnnqwen3fgfztq"
API_URL_4 = "http://95.31.15.222:8091/v2/projects/4/export"
API_KEY_4 = "tgpak_grpwyy3kg5wgomtonuzgmodqnjxgo3rtnr2ds2lbnm3a"
EXPORT_FOLDER = "translations"  # Папка для сохранения
TEMP_ZIP = "translations.zip"  # Временный ZIP-файл
MOUNT_FOLDER = "HMS_00-WindowsNoEditor_Rus"
FINAL_FOLDER = "HMS_00-WindowsNoEditor_Rus/HMS_00/Content/Etc/Localization"  # Папка для финальных файлов
UNREALPAK_FOLDER = "UnrealPakTool"  # Папка с UnrealPak.exe
FILELIST_NAME = "filelist.txt"  # Имя файла для списка

# Нужные папки и их соответствующие имена
TARGET_FOLDERS = {
    "event_dialogue": "event_dialogue_ru.csv",
    "ui": "ui_ru.csv",
}

# Убедимся, что папка для финальных файлов существует
os.makedirs(FINAL_FOLDER, exist_ok=True)

def stop_with_error(message):
    """
    Останавливает выполнение программы с сообщением об ошибке и ждет нажатия клавиши.
    """
    print(f"\n❌ ОШИБКА: {message}")
    print("\nПроцесс остановлен. Нажмите любую клавишу для закрытия...")
    try:
        input()
    except KeyboardInterrupt:
        pass
    sys.exit(1)


def pause_with_success(message):
    """
    Показывает сообщение об успехе и ждет нажатия клавиши.
    """
    print(f"\n✅ {message}")
    print("\nНажмите любую клавишу для закрытия...")
    try:
        input()
    except KeyboardInterrupt:
        pass


def get_pak_output_path():
    # Путь к папке
    target_folder = "C:/Program Files (x86)/Steam/steamapps/common/The Matchless KungFu/HMS_00/Content/Paks/"
    default_output = "../HMS_00-WindowsNoEditor_Rus.pak"  # Путь по умолчанию, если папка отсутствует

    if os.path.exists(target_folder) and os.path.isdir(target_folder):
        # Если папка существует, использовать её
        pak_output = os.path.join(target_folder, "HMS_00-WindowsNoEditor_Rus.pak")
        print(f"Папка найдена. Используем путь: {pak_output}")
    else:
        # Если папка отсутствует, использовать путь по умолчанию
        pak_output = default_output
        print(f"Папка не найдена. Используем путь по умолчанию: {pak_output}")
    
    return pak_output


def find_unrealpak():
    """
    Находит путь к UnrealPak.exe в папке UnrealPakTool.
    """
    tool_path = os.path.join(os.getcwd(), UNREALPAK_FOLDER, "UnrealPak.exe")
    if os.path.exists(tool_path):
        print(f"Найден UnrealPak.exe: {tool_path}")
        return tool_path
    else:
        raise FileNotFoundError(f"UnrealPak.exe не найден в папке '{UNREALPAK_FOLDER}'.")


def download_zip():
    """
    Скачивает ZIP-архив с переводами через новый API URL (Tolgee).
    """
    url = f"{API_URL_4}?ak={API_KEY_4}"
    print(url)

    try:
        response = requests.get(url, stream=True)
        print(f"Статус-код ответа: {response.status_code}")

        if response.status_code == 200:
            # Сохраняем ZIP-файл
            with open(TEMP_ZIP, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"ZIP-архив успешно сохранён в '{TEMP_ZIP}'.")
            return True
        else:
            stop_with_error(f"Ошибка при загрузке ZIP-архива. Ответ сервера:, {response.text}")
    except Exception as e:
        stop_with_error(f"Произошла ошибка при загрузке ZIP-архива: {e}")



def extract_zip():
    """
    Распаковывает ZIP-архив в папку EXPORT_FOLDER.
    """
    try:
        with zipfile.ZipFile(TEMP_ZIP, "r") as zip_ref:
            zip_ref.extractall(EXPORT_FOLDER)
        print(f"Архив распакован в папку '{EXPORT_FOLDER}'.")
        if os.path.exists(TEMP_ZIP):
            os.remove(TEMP_ZIP)
            print(f"Временный файл '{TEMP_ZIP}' удалён.")
        return True
    except Exception as e:
        stop_with_error(f"Ошибка при распаковке архива: {e}")


def convert_json_to_csv(json_path, csv_path):
    """
    Конвертирует JSON в CSV.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            # Добавляем заголовки
            writer.writerow(["key", "translation"])
            for key, value in data.items():
                writer.writerow([key, value])

        print(f"Файл '{json_path}' успешно преобразован в '{csv_path}'.")
        return True
    except Exception as e:
        stop_with_error(f"Ошибка при преобразовании файла '{json_path}': {e}")

def process_csv_file(csv_path):
    """
    Проверяет CSV-файл, удаляет ненужные строки и добавляет недостающие строки.
    """

    # Строки, которые должны быть в начале файла
    header_lines = [
        ["# 文本key", "文本value"],
        ["string", "string"],
        ["id", "text"]
    ]

    try:
        # Читаем существующий файл
        with open(csv_path, "r", encoding="utf-8") as csv_file:
            rows = list(csv.reader(csv_file))

        # Удаляем строки с ключами 'key', 'id', 'string' и дублирующиеся заголовки
        filtered_rows = []
        for row in rows:
            if len(row) == 0:
                continue
            if row in header_lines or row[0] in ["key", "id", "string"]:
                continue
            # Заменяем \n на \\n в каждой строке
            filtered_rows.append([col.replace("\n", "\\n") for col in row])

        # Добавляем заголовки в начало
        filtered_rows = header_lines + filtered_rows

        # Записываем обратно
        with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
            writer.writerows(filtered_rows)

        print(f"Файл '{csv_path}' обработан и обновлён.")
    except Exception as e:
        stop_with_error(f"Ошибка при обработке файла '{csv_path}': {e}")

def process_files():
    """
    Отбирает и переименовывает нужные файлы, копирует дополнительные.
    """
    files_processed = False
    
    for folder, new_name in TARGET_FOLDERS.items():
        folder_path = os.path.join(EXPORT_FOLDER, folder)
        if os.path.exists(folder_path):
            print(f"Обработка папки: {folder_path}")
            for file in os.listdir(folder_path):
                print(f"Найден файл: {file}")
                if file.endswith("ru.json"):  # Только файлы для ru
                    json_path = os.path.join(folder_path, file)
                    csv_path = os.path.join(FINAL_FOLDER, new_name)

                    # Конвертация JSON в CSV
                    if convert_json_to_csv(json_path, csv_path):
                        print(f"Файл '{json_path}' преобразован и сохранён как '{csv_path}'.")
                        # Обработка CSV
                        process_csv_file(csv_path)
                        files_processed = True
                    else:
                        stop_with_error(f"Ошибка при обработке файла '{json_path}'.")
        else:
            print(f"Папка '{folder_path}' не найдена.")
    
    if not files_processed:
        stop_with_error("Не найдено ни одного файла для обработки. Проверьте папку 'translations'.")


def build_pak(unrealpak_path):
    """
    Упаковывает файлы в .pak с помощью UnrealPak и выводит содержимое filelist.txt.
    """
    try:
        filelist_path = os.path.join(os.getcwd(), FILELIST_NAME)  # Генерируем файл в корневой папке
        hms_folder = os.path.join(os.getcwd(), MOUNT_FOLDER).replace("\\", "/")

        # Создаём файл со списком для UnrealPak
        with open(filelist_path, "w") as filelist:
            filelist.write(f'"{hms_folder}/*.*" "..\\..\\..\\*.*"\n')

        # Выводим содержимое filelist.txt в консоль
        print("\n=== Содержимое filelist.txt ===")
        with open(filelist_path, "r") as filelist:
            content = filelist.read()
            print(content)
        print("=== Конец содержимого filelist.txt ===\n")

        out_path = get_pak_output_path()

        # Запускаем UnrealPak
        command = [unrealpak_path, out_path, f"-Create={filelist_path}", "-compress"]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        print(f"Файлы успешно упакованы в '{out_path}'.")
        
        # Удаляем временный файл
        if os.path.exists(filelist_path):
            os.remove(filelist_path)
            print(f"Временный файл '{FILELIST_NAME}' удалён.")
            
    except subprocess.CalledProcessError as e:
        stop_with_error(f"Ошибка при упаковке .pak файла: {e}\nВывод: {e.stdout}\nОшибки: {e.stderr}")
    except Exception as e:
        stop_with_error(f"Ошибка при упаковке .pak файла: {e}")


# Основная функция
if __name__ == "__main__":
    print("\n=== Загрузка и обработка переводов ===")
    if download_zip():
        if extract_zip():
            try:
                print("Начинаю обработку файлов...")
                process_files()
                
                print("\nНачинаю создание .pak файла...")
                unrealpak_path = find_unrealpak()
                build_pak(unrealpak_path)
                
                #pause_with_success("Все операции выполнены успешно!")
                
            except Exception as e:
                stop_with_error(f"Неожиданная ошибка: {e}")