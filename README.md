# Unblock for Russia

Этот репозиторий содержит списки доменов, которые ограничивают доступ или функциональность для российских IP-адресов.

Вы можете выбрать один из двух списков, в зависимости от ваших потребностей:

## 1. `custom-geoblock`

*   Обрезанная версия `geoblock`. Содержит только те домены, которыми я пользуюсь лично или планирую пользоваться.

## 2. `geoblock`

*   Этот список доменов составляется из трех источников:
    *   [`custom-geoblock` от Internet-Helper](https://github.com/Internet-Helper/Unblock-for-Russia/blob/main/custom-geoblock.lst) (тот же, что и в пункте 1)
    *   [`no-russia-hosts` от dartraiden](https://github.com/dartraiden/no-russia-hosts/blob/master/hosts.txt)
    *   [`geoblock.lst` от itdoginfo](https://github.com/itdoginfo/allow-domains/blob/main/Categories/geoblock.lst)

***

Для каждого из двух списков (`custom-geoblock` и `geoblock`) доступны четыре формата файлов:

*   `.lst`: Используется как источник доменов для обновления остальных файлов.
*   `.srs`: Скомпилированный формат, предназначенный для использования с [sing-box](https://github.com/SagerNet/sing-box), содержащий список доменов.
*   `.txt`: Простой текстовый файл, содержащий список доменов, каждый на новой строке.
*   `.json`: Файл в формате JSON, содержащий список доменов.

Содержимое доменов во всех четырех форматах ***идентично.***

> [!TIP]
> Хотите создать собственный обновляемый список?

Используйте файл `update.py` - это скрипт на Python, предназначенный для автоматического обновления списков доменов на основе ваших ссылок. Он выполняет следующие действия:

1.  **Загружает списки доменов:** Скрипт скачивает списки доменов из указанных источников (URL-адресов).
2.  **Обрабатывает и фильтрует домены:** Скрипт удаляет дубликаты, сортирует домены по алфавиту и, если требуется, разделяет список на блоки, сохраняя структуру оригинального файла.
3.  **Генерирует файлы в различных форматах:** Скрипт создает файлы `.lst`, `.json` и `.txt` с обновленными списками доменов.
4.  **Компилирует `.srs` файлы (sing-box):** При наличии `sing-box` в той же папке, скрипт использует его для компиляции `.json` файлов в оптимизированные `.srs` файлы, предназначенные для rule-set.
5.  **Заменяет оригинальные файлы:** Только после успешной обработки и/или компиляции, скрипт заменяет предыдущие файлы новыми, обновленными версиями. В ином случае они остаются нетронутыми.

Условия для работы `update.py`:

*   Для работы скрипта требуется установленный [`Python 3`](https://www.python.org/downloads/) и библиотека `requests`.
*   Для компиляции `.srs` файлов требуется исполняемый файл [`sing-box`](https://github.com/SagerNet/sing-box/releases) в той же папке, где запускается `update.py`. В ином случае будут созданы только три формата без `.srs`.
Чтобы создать свой список доменов, просто замените на свои ссылки в переменной `geoblock_urls` в файле `update.py`:
```
# Использование ссылок для geoblock_urls
geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/geoblock.lst',
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt',
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst'
]
```
Чтобы скрипт не создавал файлы со списком `custom_geoblock`, то удалите этот раздел в том же файле `update.py`:
```
# Использование ссылки для custom_geoblock_urls
custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]
```
