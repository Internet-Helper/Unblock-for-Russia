import requests
import json

def fetch_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"Загрузка не удалась для следующей ссылки:\n{e}")
        return None  # Возвращаем None при ошибке

def extract_unique_domains(text_lines):
    unique_domains = set()
    for line in text_lines:
        cleaned_line = ''.join(char for char in line if char.isprintable())
        domains = [domain.strip() for domain in cleaned_line.split() if domain.strip() and domain != '#']
        unique_domains.update(domains)
    return unique_domains

def process_geoblock_file(filename, urls):
    domains_for_delete = {'google.com', 'googleapis.com', 'github.com', 'twimg.com', 'twitter.com', 'x.com', 'tweetdeck.com', 't.co'}
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.split('\n\n')
    
    initial_lines = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('#')]
        initial_lines.extend(lines)
    initial_domains = extract_unique_domains(initial_lines) - domains_for_delete
    
    processed_blocks = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and not line.startswith('#')]
        if not lines:
            continue
            
        seen = set()
        filtered_lines = []
        for line in lines:
            domains = [domain.strip() for domain in line.split() if domain.strip() and domain != '#']
            for domain in domains:
                if domain not in seen and domain not in domains_for_delete:
                    filtered_lines.append(domain)
                    seen.add(domain)
        
        processed_blocks.append(filtered_lines)
    
    all_local_domains = set()
    for block in processed_blocks:
        all_local_domains.update(block)
    
    url_stats = []
    seen_domains = set(all_local_domains)  
    added_domains_lists = {}

    for index, url in enumerate(urls, start=1):
        url_lines = fetch_url_content(url)
        if url_lines is None:  # Если ошибка загрузки, пропускаем ссылку
            continue  

        cleaned_lines = [line.strip() for line in url_lines if line.strip() and not line.strip().startswith('#')]
        total_url_domains = len(extract_unique_domains(cleaned_lines))
        
        url_domains = extract_unique_domains(cleaned_lines)
        new_domains = [domain for domain in url_domains if domain not in seen_domains and domain not in domains_for_delete]
        new_domains_count = len(new_domains)
        
        added_domains_lists[f"added_domains_{index}"] = new_domains
        
        if new_domains:
            processed_blocks[-1].extend(new_domains)
            processed_blocks[-1].sort()
            seen_domains.update(new_domains)
        
        url_stats.append((url, total_url_domains, new_domains_count))
    
    result = []
    seen_domains = set()
    for i, block in enumerate(processed_blocks):
        block_result = []
        for domain in block:
            if domain not in seen_domains:
                block_result.append(domain)
                seen_domains.add(domain)
        if block_result:
            result.extend(block_result)
            if i < len(processed_blocks) - 1:
                result.append('')
    
    final_domains = set(result) - {''}  
    
    # Запись в geoblock.lst
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
    
    # Создание geoblock.json
    json_data = {
        "version": 1,
        "rules": [
            {
                "domain_suffix": sorted(final_domains)  # Сортируем домены по алфавиту
            }
        ]
    }
    
    with open("geoblock.json", "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    # Создание geoblock.txt (чистый список доменов)
    with open("geoblock.txt", "w", encoding="utf-8") as txt_file:
        txt_file.write("\n".join(sorted(final_domains)))  # Сортируем домены по алфавиту

    print()
    for index, (url, total, new_count) in enumerate(url_stats, start=1):
        print(f"Количество доменов в списке ({url}): {total}")
        print(f"Из них добавлено новых доменов: {new_count}")
        print()
    print(f"Для просмотра новых доменов используйте команду - added_domains\n")
    print(f"Было в geoblock: {len(initial_domains)}")
    print(f"Стало в geoblock: {len(final_domains)}")

    return added_domains_lists

# Использование ссылок
filename = 'geoblock.lst'
urls = [
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst',
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt'
]

added_domains = process_geoblock_file(filename, urls)