import requests
import json
import subprocess
import os
import tempfile
import shutil
import time

def fetch_url_content(url):
    try:
        print(f"Загрузка доменов по ссылке:\n{url}")
        response = requests.get(url)
        response.raise_for_status()
        print(f"Загрузка успешно завершена!\n")
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"Загрузка не удалась!")
        while True:
            answer = input(f"Продолжить обновление без доменов из этой ссылки?\nНапишите + чтобы продолжить или - чтобы остановить обновление и нажмите Enter: ")
            if answer == '+':
                print("Продолжаем без этой ссылки.\n")
                return None
            elif answer == '-':
                print("Прерываем обновление.")
                return False  # Возвращаем False для прерывания
            else:
                print("Некорректный ввод. Пожалуйста, введите + или -")

def extract_unique_domains(text_lines):
    unique_domains = set()
    for line in text_lines:
        cleaned_line = ''.join(char for char in line if char.isprintable())
        domains = [domain.strip() for domain in line.split() if domain.strip() and domain != '#']
        unique_domains.update(domains)
    return unique_domains

def process_geoblock_file(filename, urls, temp_filenames, is_custom=False):
    print(f"Запуск работы с {filename}...\n")
    domains_for_delete = {'google.com', 'googleapis.com', 'github.com', 'twimg.com', 'twitter.com', 'x.com', 'tweetdeck.com', 'tweetdeck.com', 't.co'}

    if is_custom:  # Для custom-geoblock.lst обрабатываем только первую ссылку
        main_url = urls[0]  # Берем только первую ссылку для custom
        other_urls = []     # И не добавляем другие
    else:
        main_url = urls[0]  # Первая ссылка - для geoblock
        other_urls = urls[1:]  # Остальные ссылки

    # 1. Загрузка из основной ссылки (main_url)
    main_url_lines = fetch_url_content(main_url)
    if main_url_lines is False:  # Если пользователь прервал выполнение
        return False
    if main_url_lines is None:
        print(f"Не удалось загрузить основной список доменов из {main_url}, продолжение невозможно")
        return False

    # Разделение контента на блоки
    content = "\n".join(main_url_lines)
    blocks = content.split('\n\n')

    processed_blocks = []
    initial_domains = set() # Initialize the variable

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('#')]
        if lines:
            # Extract unique domains and update initial_domains
            unique_domains_in_block = extract_unique_domains(lines) - domains_for_delete
            initial_domains.update(unique_domains_in_block)
            processed_blocks.append(list(unique_domains_in_block))  # Append list of unique domains
        else:
            processed_blocks.append([]) # Keep the empty block

    # 2. Обработка дополнительных ссылок (только для geoblock)
    if not is_custom:
        for index, url in enumerate(other_urls, start=2):  # Отсчет с 2, т.к. первая ссылка уже обработана
            url_lines = fetch_url_content(url)
            if url_lines is False:  # Если пользователь прервал выполнение
                return False
            if url_lines is None:
                continue

            cleaned_lines = [line.strip() for line in url_lines if line.strip() and not line.strip().startswith('#')]
            new_domains = extract_unique_domains(cleaned_lines) - domains_for_delete

            # Add new domains into the last block
            if processed_blocks:
                last_block = processed_blocks[-1]
                for domain in new_domains:
                    if domain not in initial_domains:
                        last_block.append(domain)
                        initial_domains.add(domain)
            else:
                processed_blocks.append(list(new_domains))  # Create the first block when there's none

    # 3. Формирование итогового списка с сохранением блоков
    result = []
    for block in processed_blocks:
        sorted_block = sorted(block)  # Сортировка доменов в каждом блоке
        result.extend(sorted_block)
        if processed_blocks.index(block) < len(processed_blocks) - 1:
            result.append('')  # Добавляем пустую строку между блоками

    final_domains = set(result) - {''}

    # Запись во временный geoblock.lst или custom-geoblock.lst
    temp_lst_filename = temp_filenames['geoblock_lst'] if filename == 'geoblock.lst' else temp_filenames['custom_geoblock_lst']
    with open(temp_lst_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    # Запись во временный geoblock.json или custom-geoblock.json
    temp_json_filename = temp_filenames['geoblock_json'] if filename == 'geoblock.lst' else temp_filenames['custom_geoblock_json']
    json_data = {
        "version": 1,
        "rules": [
            {
                "domain_suffix": sorted(final_domains)
            }
        ]
    }
    with open(temp_json_filename, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    # Запись во временный geoblock.txt или custom-geoblock.txt
    temp_txt_filename = temp_filenames['geoblock_txt'] if filename == 'geoblock.lst' else temp_filenames['custom_geoblock_txt']
    with open(temp_txt_filename, "w", encoding="utf-8") as txt_file:
        txt_file.write("\n".join(sorted(final_domains)))

    print(f"Было в {filename}: {len(initial_domains)} доменов.")
    print(f"Стало в {filename}: {len(final_domains)} доменов.\n")

    return True  # Возвращаем True в случае успеха

def run_srs_cmd(geoblock_json_path, srs_path):  # Изменен параметр для srs.
    """
    Создает временный srs.cmd, запускает его и удаляет.
    """
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmd') as temp_file:
            temp_cmd_path = temp_file.name
            # Construct the command
            command = f'@echo off\n' \
                      f'sing-box rule-set compile "{geoblock_json_path}" -o "{srs_path}"\n'

            temp_file.write(command)
        # Убеждаемся что файл закрыт до того как его запускать

        # Запускаем команду с помощью subprocess
        process = subprocess.Popen([temp_cmd_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)  # Pass the command as a list
        stdout, stderr = process.communicate()

        if stdout:
            print("Standard Output:")
            print(stdout.decode())

        if stderr:
            print("Standard Error:")
            print(stderr.decode())

        if process.returncode == 0:
            return True
        else:
            print(f"Создание файла .srs завершилось с кодом ошибки: {process.returncode}")
            return False

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False  # Ошибка - прерываем обновление
    finally:
        # Удаляем временный файл .cmd
        try:
            os.remove(temp_cmd_path)
        except OSError as e:
            print(f"Ошибка при удалении временного файла {temp_cmd_path}: {e}")

def create_temp_filenames():  # Убрали original_filename, т.к. обрабатываем 2 разных файла
    """Создает имена временных файлов для каждого."""
    return {
        'geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="geoblock_temp_"),
        'geoblock_json': tempfile.mktemp(suffix=".json", prefix="geoblock_temp_"),
        'geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="geoblock_temp_"),
        'geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="geoblock_temp_"),
        'custom_geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="custom_geoblock_temp_"),
        'custom_geoblock_json': tempfile.mktemp(suffix=".json", prefix="custom_geoblock_temp_"),
        'custom_geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="custom_geoblock_temp_"),
        'custom_geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="custom_geoblock_temp_")
    }

def cleanup_temp_files(temp_filenames):
    """Удаляет все временные файлы."""
    print("\nУдаление временных файлов...")
    for temp_file in temp_filenames.values():
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            print(f"Временный файл {temp_file} не найден.")
        except OSError as e:
            print(f"Ошибка при удалении временного файла {temp_file}: {e}")
    print("Удаление временных файлов завершено.")

def replace_original_with_temp(temp_filenames):  # Теперь один словарь
    """Заменяет оригинальные файлы временными."""
    print("Замена оригинальных файлов обновленными временными файлами...")
    try:
        shutil.copy2(temp_filenames['geoblock_lst'], 'geoblock.lst')
        shutil.copy2(temp_filenames['geoblock_json'], 'geoblock.json')
        shutil.copy2(temp_filenames['geoblock_txt'], 'geoblock.txt')
        shutil.copy2(temp_filenames['geoblock_srs'], 'geoblock.srs')

        shutil.copy2(temp_filenames['custom_geoblock_lst'], 'custom-geoblock.lst')
        shutil.copy2(temp_filenames['custom_geoblock_json'], 'custom-geoblock.json')
        shutil.copy2(temp_filenames['custom_geoblock_txt'], 'custom-geoblock.txt')
        shutil.copy2(temp_filenames['custom_geoblock_srs'], 'custom-geoblock.srs') # custom-geoblock.srs
        print("Замена завершена.")
        return True
    except Exception as e:
        print(f"Ошибка при замене файлов: {e}")
        return False

def countdown_and_exit(duration=3):
    """Выводит обратный отсчет и закрывает окно."""
    print("Закрытие окна через:")
    for i in range(duration, 0, -1):
        print(f"{i}...")
        time.sleep(1)  # Пауза в 1 секунду
    print("Закрытие.")
    os._exit(0)  # Принудительное завершение процесса (более надежно в данном случае)


# Использование ссылок
geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/geoblock.lst',
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt',
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst'
]
custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]

# 1. Создаем временные файлы
temp_filenames = create_temp_filenames()

try:
    # 2. Обрабатываем geoblock.lst
    geoblock_success = process_geoblock_file('geoblock.lst', geoblock_urls, temp_filenames)
    if geoblock_success is False: # Проверка, что пользователь не прервал процесс
        print("Обновление geoblock.lst прервано.")
        countdown_and_exit()

    # 3. Обрабатываем custom-geoblock.lst
    custom_geoblock_success = process_geoblock_file('custom-geoblock.lst', custom_geoblock_urls, temp_filenames, is_custom=True) # is_custom=True
    if custom_geoblock_success is False: # Проверка, что пользователь не прервал процесс
        print("Обновление custom-geoblock.lst прервано.")
        countdown_and_exit()

    # 4. Запускаем srs.cmd для каждого файла:
    srs_geoblock_success = run_srs_cmd(temp_filenames['geoblock_json'], temp_filenames['geoblock_srs'])
    srs_custom_success = run_srs_cmd(temp_filenames['custom_geoblock_json'], temp_filenames['custom_geoblock_srs'])

    if srs_geoblock_success and srs_custom_success:
        # 5. Заменяем оригинальные файлы временными
        if replace_original_with_temp(temp_filenames): # Теперь один словарь
            print("\nОбновление завершено успешно!")
        else:
            print("Произошла ошибка при замене файлов. Обновление не завершено.")
            countdown_and_exit()
    else:
        print("Произошла ошибка во время выполнения srs.cmd для одного или обоих файлов. Обновление не завершено.")
        countdown_and_exit()


except Exception as e:  # Общий обработчик ошибок, чтобы скрипт не падал
    print(f"Произошла неожиданная ошибка: {e}")
    countdown_and_exit()

finally:  # Обязательно удаляем временные файлы, чтобы не засорять систему
    cleanup_temp_files(temp_filenames)
    countdown_and_exit()