# Zabbix API custom lib via zabbix_utils 

Библиотека для удобного взаимодействия c Zabbix API и скрипты для формирования отчетов из кэша (in progress) для автоматизации задач мониторинга/etc.

##  Список файлов и их описание:

- `zabbix_api.py` - библиотека для работы с Zabbix API 
- `make_cache.py` - Скрипт для формирования отчетов
- Скрипты формирвания отчетов и рассылки на mail (в разработке)

_____________________

## Пример использования библиотеки:

from zabbix_api import API

### Инициализация подключения и создание объекта класса API:
api = API(creds_file="creds.ini")

### Получение проблем конкретного host по его id:
problems = api.get_problem(hosts=10084)

print(problems, "\n") 

### Получение id template by name
template = api.get_template_id_by_name("Linux by Zabbix agent")

print(template, "\n")


## Пример формирования кэша в json:
from zabbix_api import API
from make_cache import ZabbixCache
import os


api = API(creds_file="creds.ini")

cache = ZabbixCache(api, cache_dir="/Users/whoami?/Documents/_zabbix/cache_structure", pid_dir="/Users/whoami?/Documents/_zabbix/pid")


make_cache = cache.make_cache()

print(make_cache)
