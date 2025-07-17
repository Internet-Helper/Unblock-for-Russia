import requests
import json
import subprocess
import os
import tempfile
import shutil
import time
import sys
import re

os.chdir(os.path.dirname(os.path.realpath(__file__)))

custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]

additional_urls_for_geoblock = [
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt',
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst'
]

domains_for_delete = {
    'google.com', 'googleapis.com', 'github.com', 'twimg.com', 'twitter.com', 'x.com', 
    'tweetdeck.com', 't.co', 'nvidia.com', 'api.vk.com'
}

try:
    custom_geoblock_urls
except NameError:
    custom_geoblock_urls = None

GEOBLOCK_LST = 'geoblock.lst'
CUSTOM_GEOBLOCK_LST = 'custom-geoblock.lst'
SING_BOX_PATH = 'sing-box.exe'
LAST_BLOCK_WORDS = ['остальное']

# Нормализация комментария
def normalize_comment(comment):
    return comment.lstrip('# ').strip().lower()

# Создание ключа для сортировки блоков
def get_block_sort_key(block):
    if not block.get('comments'):
        return (3, 0, '')

    comment = block['comments'][0]
    norm_comment = normalize_comment(comment)
    first_word = norm_comment.split()[0] if norm_comment else ''

    if first_word in LAST_BLOCK_WORDS:
        return (2, 0, '')

    has_russian = bool(re.search(r'[а-яА-Я]', norm_comment))
    
    if has_russian:
        return (0, block.get('first_index', 999), '')
    else:
        return (1, 0, norm_comment)

# Загрузка содержимого по URL
def fetch_url_content(url):
    try:
        print(f"Загрузка доменов по ссылке:\n{url}")
        response = requests.get(url)
        response.raise_for_status()
        print(f"Загрузка успешно завершена!\n")
        return response.text.splitlines()
    except requests.RequestException:
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

# Получение корневого домена
def get_root_domain(domain):
    parts = domain.split('.')
    known_suffixes = {'co.uk', 'com.au', 'com.cn', 'org.cn', 'net.cn', 'com.tw', 'com.hk', 'co.jp'}
    
    if len(parts) > 2:
        last_two = ".".join(parts[-2:])
        if last_two in known_suffixes:
            return ".".join(parts[-3:])
        else:
            return ".".join(parts[-2:])
    return domain

# Извлечение уникальных доменов
def extract_unique_domains(text_lines, to_root_domain=False):
    unique_domains = set()
    for line in text_lines:
        cleaned_line = ''.join(char for char in line if char.isprintable())
        parts = cleaned_line.split()
        domain = parts[-1] if parts else ''
        
        # Условия для пропуска невалидных строк
        if (not domain or 
            domain.startswith('#') or 
            ':' in domain or 
            '/' in domain or 
            '.' not in domain):  # <-- Вот новый, самый важный фильтр
            continue

        if to_root_domain:
            domain = get_root_domain(domain)
            
        unique_domains.add(domain.strip())
    return unique_domains

# Парсинг списка на блоки
def parse_content_with_comments(lines):
    blocks = []
    current_block = {'comments': [], 'domains': set()}
    for line in lines:
        line = line.strip()
        if not line:
            if current_block['comments'] or current_block['domains']:
                blocks.append(current_block)
                current_block = {'comments': [], 'domains': set()}
        elif line.startswith('#'):
            current_block['comments'].append(line)
        else:
            domain = line.split()[-1]
            if domain:
                current_block['domains'].add(domain.strip())
    if current_block['comments'] or current_block['domains']:
        blocks.append(current_block)
    return blocks

# Обработка и генерация файлов
def process_geoblock_file(filename, urls, temp_filenames, base_file_content=None, additional_urls=None):
    print(f"Запуск работы с {filename}...\n")
    all_blocks = []
    misc_domains = set()

    if base_file_content:
        all_blocks = parse_content_with_comments(base_file_content)
    elif urls:
        for url in urls:
            lines = fetch_url_content(url)
            if lines is False: return (False, None)
            if lines is None: continue
            parsed_blocks = parse_content_with_comments(lines)
            all_blocks.extend(parsed_blocks)

    if additional_urls:
        for url in additional_urls:
            lines = fetch_url_content(url)
            if lines is False: return (False, None)
            if lines is None: continue
            new_domains = extract_unique_domains(lines, to_root_domain=True)
            misc_domains.update(new_domains)

    merged_blocks = {}
    for i, block in enumerate(all_blocks):
        block['domains'] -= domains_for_delete
        if not block['comments']:
            misc_domains.update(block['domains'])
            continue
        key = normalize_comment(block['comments'][0])
        if key not in merged_blocks:
            block['first_index'] = i
            merged_blocks[key] = block
        else:
            merged_blocks[key]['domains'].update(block['domains'])
    
    final_blocks = list(merged_blocks.values())

    domains_in_structured_blocks = set().union(*(b['domains'] for b in final_blocks))
    misc_domains -= domains_for_delete
    misc_domains -= domains_in_structured_blocks

    if misc_domains:
        other_block = next((b for b in final_blocks if b['comments'] and normalize_comment(b['comments'][0]).split()[0] in LAST_BLOCK_WORDS), None)
        if other_block:
            other_block['domains'].update(misc_domains)
        else:
            final_blocks.append({'comments': ['# Остальное'], 'domains': misc_domains, 'first_index': 999})

    sorted_blocks = sorted(final_blocks, key=get_block_sort_key)
    result_lines = []
    final_domains = set()

    for i, block in enumerate(sorted_blocks):
        if not block.get('domains'): continue
        result_lines.extend(sorted(block['comments']))
        sorted_domains = sorted(list(block['domains']))
        result_lines.extend(sorted_domains)
        final_domains.update(sorted_domains)
        if i < len(sorted_blocks) - 1 and any(b.get('domains') for b in sorted_blocks[i+1:]):
             result_lines.append('')
    
    is_geoblock = filename == GEOBLOCK_LST
    temp_prefix = 'geoblock' if is_geoblock else 'custom_geoblock'
    
    with open(temp_filenames[f'{temp_prefix}_lst'], 'w', encoding='utf-8') as f: f.write('\n'.join(result_lines))
    json_data = {"version": 1, "rules": [{"domain_suffix": sorted(list(final_domains))}]}
    with open(temp_filenames[f'{temp_prefix}_json'], "w", encoding="utf-8") as json_file: json.dump(json_data, json_file, ensure_ascii=False, indent=2)
    with open(temp_filenames[f'{temp_prefix}_txt'], 'w', encoding='utf-8') as txt_file: txt_file.write("\n".join(sorted(list(final_domains))))
    with open(temp_filenames[f'{temp_prefix}_agh'], 'w', encoding='utf-8') as agh_file: agh_file.write(f"[{'/' + '/'.join(sorted(list(final_domains))) + '/'}]")
    with open(temp_filenames[f'{temp_prefix}_3xui'], 'w', encoding='utf-8') as ui_file: ui_file.write(",".join(sorted(list(final_domains))))

    print(f"Файл {filename} успешно сгенерирован с {len(final_domains)} доменами.\n")
    return (True, result_lines)

# Обновление всех файлов
def update_files(custom_geoblock_urls, temp_filenames, create_srs, has_custom):
    custom_success, custom_content = (False, None)
    if has_custom:
        print("Обработка custom-geoblock.lst (основной файл)...")
        custom_success, custom_content = process_geoblock_file(CUSTOM_GEOBLOCK_LST, custom_geoblock_urls, temp_filenames)
        if not custom_success: return False

    print("Обработка geoblock.lst (расширенный файл)...")
    geoblock_success, _ = process_geoblock_file(GEOBLOCK_LST, None, temp_filenames, base_file_content=custom_content, additional_urls=additional_urls_for_geoblock)
    if not geoblock_success: return False
    
    if create_srs:
        print("\nКомпиляция .srs файлов...")
        srs_geoblock = run_srs_cmd(temp_filenames['geoblock_json'], temp_filenames['geoblock_srs'])
        srs_custom = True
        if has_custom: srs_custom = run_srs_cmd(temp_filenames['custom_geoblock_json'], temp_filenames['custom_geoblock_srs'])
        if not (srs_geoblock and srs_custom): return False

    return replace_original_with_temp(temp_filenames, create_srs, has_custom)

# Запуск компиляции .srs файлов
def run_srs_cmd(geoblock_json_path, srs_path):
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmd', encoding='utf-8') as temp_file:
            temp_cmd_path = temp_file.name
            command = f'@echo off\n"{SING_BOX_PATH}" rule-set compile "{geoblock_json_path}" -o "{srs_path}"\n'
            temp_file.write(command)

        process = subprocess.Popen([temp_cmd_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stdout and stdout.strip(): print("Sing-box output:", stdout.decode('cp866').strip())
        if stderr and stderr.strip(): print("Sing-box error:", stderr.decode('cp866').strip())
        if process.returncode != 0:
            print(f"Ошибка sing-box: код {process.returncode}")
            return False
        print(f"Файл .srs успешно создан: {os.path.basename(srs_path)}")
        return True
    except Exception as e:
        print(f"Произошла ошибка при запуске sing-box: {e}")
        return False
    finally:
        try: os.remove(temp_cmd_path)
        except (OSError, NameError): pass

# Создание временных файлов
def create_temp_filenames(has_custom):
    filenames = {
        'geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="geoblock_temp_"), 'geoblock_json': tempfile.mktemp(suffix=".json", prefix="geoblock_temp_"),
        'geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="geoblock_temp_"), 'geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="geoblock_temp_"),
        'geoblock_agh': tempfile.mktemp(suffix=".txt", prefix="geoblock-for-AGH_temp_"), 'geoblock_3xui': tempfile.mktemp(suffix=".txt", prefix="geoblock-for-3X-UI_temp_")
    }
    if has_custom:
        filenames.update({
            'custom_geoblock_lst': tempfile.mktemp(suffix=".lst", prefix="custom_geoblock_temp_"), 'custom_geoblock_json': tempfile.mktemp(suffix=".json", prefix="custom_geoblock_temp_"),
            'custom_geoblock_txt': tempfile.mktemp(suffix=".txt", prefix="custom_geoblock_temp_"), 'custom_geoblock_srs': tempfile.mktemp(suffix=".srs", prefix="custom_geoblock_temp_"),
            'custom_geoblock_agh': tempfile.mktemp(suffix=".txt", prefix="custom-geoblock-for-AGH_temp_"), 'custom_geoblock_3xui': tempfile.mktemp(suffix=".txt", prefix="custom-geoblock-for-3X-UI_temp_")
        })
    return filenames

# Удаление временных файлов
def cleanup_temp_files(temp_filenames, create_srs, has_custom):
    print("\nУдаление временных файлов...")
    for key, temp_file in temp_filenames.items():
        if not create_srs and temp_file.endswith(".srs"): continue
        if not has_custom and "custom" in key: continue
        try:
            if os.path.exists(temp_file): os.remove(temp_file)
        except OSError as e: print(f"Ошибка при удалении временного файла {temp_file}: {e}")
    print("Удаление временных файлов завершено.")

# Замена старых файлов новыми
def replace_original_with_temp(temp_filenames, create_srs, has_custom):
    print("\nЗамена оригинальных файлов обновленными...")
    try:
        shutil.copy2(temp_filenames['geoblock_lst'], GEOBLOCK_LST); shutil.copy2(temp_filenames['geoblock_json'], 'geoblock.json')
        shutil.copy2(temp_filenames['geoblock_txt'], 'geoblock.txt'); shutil.copy2(temp_filenames['geoblock_agh'], 'geoblock-for-AGH.txt')
        shutil.copy2(temp_filenames['geoblock_3xui'], 'geoblock-for-3X-UI.txt')
        if create_srs: shutil.copy2(temp_filenames['geoblock_srs'], 'geoblock.srs')
        if has_custom:
            shutil.copy2(temp_filenames['custom_geoblock_lst'], CUSTOM_GEOBLOCK_LST); shutil.copy2(temp_filenames['custom_geoblock_json'], 'custom-geoblock.json')
            shutil.copy2(temp_filenames['custom_geoblock_txt'], 'custom-geoblock.txt'); shutil.copy2(temp_filenames['custom_geoblock_agh'], 'custom-geoblock-for-AGH.txt')
            shutil.copy2(temp_filenames['custom_geoblock_3xui'], 'custom-geoblock-for-3X-UI.txt')
            if create_srs: shutil.copy2(temp_filenames['custom_geoblock_srs'], 'custom-geoblock.srs')
        print("Замена завершена.")
        return True
    except Exception as e:
        print(f"Ошибка при замене файлов: {e}")
        return False

# Завершение работы скрипта
def exit_script():
    sys.exit(0)

if __name__ == "__main__":
    has_custom = custom_geoblock_urls is not None
    temp_filenames = create_temp_filenames(has_custom)
    
    try:
        create_srs = os.path.exists(SING_BOX_PATH)
        print(f"Sing-box найден: {SING_BOX_PATH}\n" if create_srs else "Sing-box не найден. Файлы .srs создаваться не будут.\n")

        if update_files(custom_geoblock_urls, temp_filenames, create_srs, has_custom):
            print("\nОбновление завершено успешно!")
        else:
            print("\nОбновление прервано или завершилось с ошибкой.")
            exit_script()

    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        exit_script()

    finally:
        cleanup_temp_files(temp_filenames, create_srs, has_custom)
        exit_script()