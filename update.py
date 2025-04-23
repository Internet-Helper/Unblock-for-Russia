import requests
import json
import subprocess
import os
import tempfile
import shutil
import time
import sys

# Устанавливаем текущую рабочую директорию как папку со скриптом
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Добавление комментария - # Работает только через американские IP
ADD_USA_COMMENT = '+' # + для включения, - для выключения

# Использование ссылок для geoblock_urls
geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/geoblock.lst',
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt',
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst'
]

# Использование ссылки для custom_geoblock_urls
custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]

# Использование ссылки для custom_geoblock_urls (может быть не определена)
try:
    custom_geoblock_urls
except NameError:
    custom_geoblock_urls = None

# Домены для исключения
domains_for_delete = {'google.com', 'googleapis.com', 'github.com', 'twimg.com', 'twitter.com', 'x.com', 'tweetdeck.com', 't.co'}

# Константы
GEOBLOCK_LST = 'geoblock.lst'
CUSTOM_GEOBLOCK_LST = 'custom-geoblock.lst'
SING_BOX_PATH = 'sing-box.exe'

def fetch_url_content(url, is_main=False):
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
                return False
            else:
                print("Некорректный ввод. Пожалуйста, введите + или -")

def extract_unique_domains(text_lines):
    unique_domains = set()
    for line in text_lines:
        cleaned_line = ''.join(char for char in line if char.isprintable())
        domains = [domain.strip() for domain in line.split() if domain.strip() and not domain.startswith('#')]
        unique_domains.update(domains)
    return unique_domains

def process_geoblock_file(filename, urls, temp_filenames, custom_urls=None, is_custom=False):
    print(f"Запуск работы с {filename}...\n")

    if is_custom:
        main_url = urls[0]
        other_urls = []
    else:
        main_url = urls[0]
        other_urls = urls[1:]

    main_url_lines = fetch_url_content(main_url, is_main=True)
    if main_url_lines is False:
        return False
    if main_url_lines is None and not is_custom:
        print(f"Не удалось загрузить основной список доменов из {main_url}, продолжение невозможно")
        return False
    elif main_url_lines is None and is_custom:
        print(f"Пропускаем обработку {filename} из-за неудачной загрузки.")
        return True

    content = "\n".join(main_url_lines)
    blocks = content.split('\n\n')

    processed_blocks = []
    initial_domains = set()

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('#')]
        if lines:
            unique_domains_in_block = extract_unique_domains(lines) - domains_for_delete
            initial_domains.update(unique_domains_in_block)
            processed_blocks.append(list(unique_domains_in_block))
        else:
            processed_blocks.append([])

    custom_blocks_to_replace = []  # Для хранения всех подгрупп из custom, кроме последней
    custom_domains_by_block = []

    if not is_custom and custom_urls:
        custom_lines = fetch_url_content(custom_urls[0])
        if custom_lines is False:
            return False
        if custom_lines is not None:
            custom_content = "\n".join(custom_lines)
            custom_blocks = custom_content.split('\n\n')
            for i, block in enumerate(custom_blocks):
                lines = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('#')]
                if lines:
                    unique_domains = extract_unique_domains(lines) - domains_for_delete
                    custom_domains_by_block.append(unique_domains)
                    if i < len(custom_blocks) - 1:  # Сохраняем все, кроме последней подгруппы
                        custom_blocks_to_replace.append(unique_domains)
                else:
                    custom_domains_by_block.append(set())
                    if i < len(custom_blocks) - 1:
                        custom_blocks_to_replace.append(set())

    if not is_custom:
        for url in other_urls:
            url_lines = fetch_url_content(url)
            if url_lines is False:
                return False
            if url_lines is None:
                continue

            cleaned_lines = [line.strip() for line in url_lines if line.strip() and not line.strip().startswith('#')]
            new_domains = extract_unique_domains(cleaned_lines) - domains_for_delete

            if processed_blocks:
                last_block = processed_blocks[-1]
                for domain in new_domains:
                    if domain not in initial_domains:
                        last_block.append(domain)
                        initial_domains.add(domain)
            else:
                processed_blocks.append(list(new_domains))

    # Формирование результата для .lst файла
    result = []
    final_domains = set()

    # Замена всех подгрупп до последней из custom для geoblock.lst
    if not is_custom and custom_blocks_to_replace:
        for custom_block in custom_blocks_to_replace:
            result.extend(sorted(list(custom_block)))
            final_domains.update(custom_block)
            result.append('')  # Добавляем пустую строку после каждой подгруппы
        # Сохраняем только последнюю подгруппу из processed_blocks
        if processed_blocks:
            processed_blocks = [processed_blocks[-1]]  # Оставляем только последнюю подгруппу
        else:
            processed_blocks = []

    # Объединение последней подгруппы из custom с последней подгруппой geoblock
    if not is_custom and custom_urls and len(custom_domains_by_block) > 0:
        last_custom_block = custom_domains_by_block[-1]
        if processed_blocks:
            last_block = processed_blocks[-1]
            for domain in last_custom_block:
                if domain not in initial_domains:
                    last_block.append(domain)
                    initial_domains.add(domain)
        else:
            processed_blocks.append(list(last_custom_block))

    # Добавление блоков в результат
    for block in processed_blocks:
        sorted_block = sorted(block)
        result.extend(sorted_block)
        final_domains.update(sorted_block)
        if processed_blocks.index(block) < len(processed_blocks) - 1:
            result.append('')

    # Добавление комментария в .lst файлы, если включено
    temp_lst_filename = temp_filenames['geoblock_lst'] if filename == GEOBLOCK_LST else temp_filenames['custom_geoblock_lst']
    with open(temp_lst_filename, 'w', encoding='utf-8') as f:
        if ADD_USA_COMMENT == '+':
            f.write('#Работает только через американские IP\n')
        f.write('\n'.join(result))

    temp_json_filename = temp_filenames['geoblock_json'] if filename == GEOBLOCK_LST else temp_filenames['custom_geoblock_json']
    json_data = {
        "version": 1,
        "rules": [{"domain_suffix": sorted(list(final_domains))}]
    }
    with open(temp_json_filename, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    temp_txt_filename = temp_filenames['geoblock_txt'] if filename == GEOBLOCK_LST else temp_filenames['custom_geoblock_txt']
    with open(temp_txt_filename, 'w', encoding='utf-8') as txt_file:
        txt_file.write("\n".join(sorted(list(final_domains))))

    # Создание файлов для AGH
    temp_agh_filename = temp_filenames['geoblock_agh'] if filename == GEOBLOCK_LST else temp_filenames['custom_geoblock_agh']
    with open(temp_agh_filename, 'w', encoding='utf-8') as agh_file:
        domains_list = sorted(list(final_domains))
        domains_str = "/" + "/".join(domains_list) + "/"
        agh_file.write(f"[{domains_str}]")

    # Создание файлов для 3X-UI
    temp_3xui_filename = temp_filenames['geoblock_3xui'] if filename == GEOBLOCK_LST else temp_filenames['custom_geoblock_3xui']
    with open(temp_3xui_filename, 'w', encoding='utf-8') as ui_file:
        ui_file.write(",".join(sorted(list(final_domains))))

    print(f"Было в {filename}: {len(initial_domains)} доменов.")
    print(f"Стало в {filename}: {len(final_domains)} доменов.\n")
    return True

def run_srs_cmd(geoblock_json_path, srs_path):
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmd') as temp_file:
            temp_cmd_path = temp_file.name
            command = f'@echo off\nsing-box rule-set compile "{geoblock_json_path}" -o "{srs_path}"\n'
            temp_file.write(command)

        process = subprocess.Popen([temp_cmd_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if stdout:
            print("Standard Output:", stdout.decode('utf-8'))
        if stderr:
            print("Standard Error:", stderr.decode('utf-8'))
        if process.returncode != 0:
            print(f"Ошибка sing-box: код {process.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False
    finally:
        try:
            os.remove(temp_cmd_path)
        except OSError as e:
            print(f"Ошибка удаления {temp_cmd_path}: {e}")

def create_temp_filenames(has_custom):
    filenames = {
        'geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="geoblock_temp_"),
        'geoblock_json': tempfile.mktemp(suffix=".json", prefix="geoblock_temp_"),
        'geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="geoblock_temp_"),
        'geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="geoblock_temp_"),
        'geoblock_agh': tempfile.mktemp(suffix=".txt", prefix="geoblock-for-AGH_temp_"),
        'geoblock_3xui': tempfile.mktemp(suffix=".txt", prefix="custom-geoblock-for-3X-UI_temp_")
    }
    if has_custom:
        filenames.update({
            'custom_geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="custom_geoblock_temp_"),
            'custom_geoblock_json': tempfile.mktemp(suffix=".json", prefix="custom_geoblock_temp_"),
            'custom_geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="custom_geoblock_temp_"),
            'custom_geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="custom_geoblock_temp_"),
            'custom_geoblock_agh': tempfile.mktemp(suffix=".txt", prefix="custom_geoblock-for-AGH_temp_"),
            'custom_geoblock_3xui': tempfile.mktemp(suffix=".txt", prefix="custom-geoblock-for-3X-UI_temp_")
        })
    return filenames

def cleanup_temp_files(temp_filenames, create_srs, has_custom):
    print("\nУдаление временных файлов...")
    for temp_file in temp_filenames.values():
        if not create_srs and temp_file.endswith(".srs"):
            continue
        if not has_custom and ("custom_geoblock" in temp_file or "custom-geoblock-for-3X-UI" in temp_file):
            continue
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            if create_srs and temp_file.endswith(".srs"):
                print(f"Временный файл {temp_file} не найден.")
        except OSError as e:
            print(f"Ошибка при удалении временного файла {temp_file}: {e}")
    print("Удаление временных файлов завершено.")

def replace_original_with_temp(temp_filenames, create_srs, has_custom):
    print("Замена оригинальных файлов обновленными временными файлами...")
    try:
        shutil.copy2(temp_filenames['geoblock_lst'], GEOBLOCK_LST)
        shutil.copy2(temp_filenames['geoblock_json'], 'geoblock.json')
        shutil.copy2(temp_filenames['geoblock_txt'], 'geoblock.txt')
        shutil.copy2(temp_filenames['geoblock_agh'], 'geoblock-for-AGH.txt')
        shutil.copy2(temp_filenames['geoblock_3xui'], 'geoblock-for-3X-UI.txt')
        if create_srs:
            shutil.copy2(temp_filenames['geoblock_srs'], 'geoblock.srs')
        if has_custom:
            shutil.copy2(temp_filenames['custom_geoblock_lst'], CUSTOM_GEOBLOCK_LST)
            shutil.copy2(temp_filenames['custom_geoblock_json'], 'custom-geoblock.json')
            shutil.copy2(temp_filenames['custom_geoblock_txt'], 'custom-geoblock.txt')
            shutil.copy2(temp_filenames['custom_geoblock_agh'], 'custom-geoblock-for-AGH.txt')
            shutil.copy2(temp_filenames['custom_geoblock_3xui'], 'custom-geoblock-for-3X-UI.txt')
            if create_srs:
                shutil.copy2(temp_filenames['custom_geoblock_srs'], 'custom-geoblock.srs')
        print("Замена завершена.")
        return True
    except Exception as e:
        print(f"Ошибка при замене файлов: {e}")
        return False

def countdown_and_exit(duration=3):
    print("Закрытие окна через:")
    for i in range(duration, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("Закрытие.")
    sys.exit(0)

def update_files(geoblock_urls, custom_geoblock_urls, temp_filenames, create_srs, has_custom):
    geoblock_success = process_geoblock_file(GEOBLOCK_LST, geoblock_urls, temp_filenames, custom_urls=custom_geoblock_urls)
    if not geoblock_success:
        return False

    custom_success = True
    if has_custom and custom_geoblock_urls:
        custom_success = process_geoblock_file(CUSTOM_GEOBLOCK_LST, custom_geoblock_urls, temp_filenames, is_custom=True)
    if not custom_success:
        return False

    if create_srs:
        srs_geoblock = run_srs_cmd(temp_filenames['geoblock_json'], temp_filenames['geoblock_srs'])
        srs_custom = run_srs_cmd(temp_filenames['custom_geoblock_json'], temp_filenames['custom_geoblock_srs']) if has_custom and custom_geoblock_urls else True
        if not (srs_geoblock and srs_custom):
            return False

    return replace_original_with_temp(temp_filenames, create_srs, has_custom)

# Определяем has_custom
has_custom = custom_geoblock_urls is not None

# Основной код
temp_filenames = create_temp_filenames(has_custom)
try:
    create_srs = os.path.exists(SING_BOX_PATH)
    print("Sing-box найден.\n" if create_srs else "Sing-box не найден.\nПродолжаю обновление других файлов...\n")

    if update_files(geoblock_urls, custom_geoblock_urls, temp_filenames, create_srs, has_custom):
        print("\nОбновление завершено успешно!")
    else:
        print("Обновление прервано или завершилось с ошибкой.")
        countdown_and_exit()

except Exception as e:
    print(f"Произошла неожиданная ошибка: {e}")
    countdown_and_exit()

finally:
    cleanup_temp_files(temp_filenames, create_srs, has_custom)
    countdown_and_exit()