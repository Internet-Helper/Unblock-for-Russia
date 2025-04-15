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

Для каждого из двух списков (`geoblock` и `custom-geoblock`) доступны пять форматов файлов:

*   `.lst`: Используется как источник доменов для обновления остальных файлов.
*   `.srs`: Скомпилированный формат, предназначенный для использования с [sing-box](https://github.com/SagerNet/sing-box), содержащий список доменов.
*   `.json`: Файл в формате JSON, содержащий список доменов.
*   `.txt`: Простой текстовый файл, содержащий список доменов, каждый на новой строке.
*   `for-AGH.txt`: Простой текстовый файл, содержащий список доменов в формате AdGuard Home.

Содержимое доменов во всех пяти форматах ***идентично.***

***

> [!TIP]
> Хотите создать собственный обновляемый список?

Для этого измените файл `update.py` - это скрипт на Python, предназначенный для автоматического обновления списков доменов на основе ваших ссылок. Если запускаете на Widnows 11, то делайте это через cmd так как не работает через Windows PowerShell. 

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
И так же замените + на - в строке:
```
ADD_USA_COMMENT = '+' # + для включения, - для выключения
```
Чтобы скрипт дополнительно не создавал файлы со списком `custom_geoblock`, то удалите этот раздел в том же файле `update.py`:
```
# Использование ссылки для custom_geoblock_urls
custom_geoblock_urls = [
    'https://raw.githubusercontent.com/Internet-Helper/Unblock-for-Russia/refs/heads/main/custom-geoblock.lst'
]
```
