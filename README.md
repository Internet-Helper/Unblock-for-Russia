Нравится проект? Поддержи автора через [CloudTips](https://pay.cloudtips.ru/p/8ec8a87c) или [Юмани](https://yoomoney.ru/to/41001945296522) скинув на чашечку кофе ☕ 

***

# Unblock for Russia

Этот репозиторий содержит списки доменов, которые ограничивают доступ или функциональность для российских IP-адресов.

Вы можете выбрать один из двух списков, в зависимости от ваших потребностей:

## 1. `geoblock`

*   Этот список доменов составляется из трех источников:
    *   [`custom-geoblock` от Internet-Helper](https://github.com/Internet-Helper/Unblock-for-Russia/blob/main/custom-geoblock.lst) (тот же, что ниже в пункте 2)
    *   [`no-russia-hosts` от dartraiden](https://github.com/dartraiden/no-russia-hosts/blob/master/hosts.txt)
    *   [`geoblock.lst` от itdoginfo](https://github.com/itdoginfo/allow-domains/blob/main/Categories/geoblock.lst)

## 2. `custom-geoblock`

*   Содержит только те домены, которыми пользуюсь лично или планирую пользоваться.

Для каждого из двух списков (`geoblock` и `custom-geoblock`) доступны шесть форматов:

*   `.lst`: Текстовый файл, содержащий список доменов. Используется как источник для наполнения остальных файлов.
*   `.json`: Текстовый файл, содержащий список доменов.
*   `.txt`: Текстовый файл, содержащий список доменов.
*   `for-AGH.txt`: Текстовый файл файл, содержащий список доменов для формата AdGuard Home.
*   `for-3X-UI.txt`: Текстовый файл файл, содержащий список доменов для формата 3X-UI.
*   `.srs`: Скомпилированный файл, предназначенный для использования с [sing-box](https://github.com/SagerNet/sing-box), содержащий список доменов.

Содержимое доменов во всех шести форматах ***идентично.***

***

> [!TIP]
> Хотите создать собственный обновляемый список?

Для этого измените файл `update.py` - это скрипт на Python, предназначенный для автоматического обновления списков доменов на основе ваших ссылок. Если запускаете на Widnows 11, то выставите `cmd` в Терминале как основу так как не работает через `PowerShell`. 

Условия для работы `update.py`:

*   Для работы скрипта требуется установленный [`Python 3`](https://www.python.org/downloads/).
*   Для компиляции `.srs` файлов требуется исполняемый файл [`sing-box`](https://github.com/SagerNet/sing-box/releases) в той же папке, где запускается `update.py`. В ином случае будут созданы только четыре формата без `.srs`.

Чтобы создать свой список доменов, замените ссылки в переменной `geoblock_urls` на свои:
```
# Использование ссылок для geoblock_urls
geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/geoblock.lst',
    'https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt',
    'https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/geoblock.lst'
]
```
Чтобы скрипт дополнительно не создавал файлы со списком `custom_geoblock`, то удалите этот раздел в том же файле `update.py`:
```
# Использование ссылки для custom_geoblock_urls
custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]
```
