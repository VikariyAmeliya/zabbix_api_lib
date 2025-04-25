# Zabbix API custom lib via zabbix_utils 

Библиотека для удобного взаимодействия c Zabbix API и скрипты для формирования отчетов из кэша (in progress) для автоматизации задач мониторинга/etc.

##  Список файлов и их описание:

- `zabbix_api.py` - библиотека для работы с API 
- `make_cache.py` - Скрипт для формирования отчетов
- Скрипты формирвания отчетов и рассылки на mail (в разработке)

_____________________

## Пример использования:

from zabbix_api import API

### Инициализация подключения
api = API(creds_file="creds.ini")

### Получение проблем конкретного host:
problems = api.get_problem(hosts=10084)

print(problems, "\n") 

### Получение id template by name
template = api.get_template_id_by_name("Linux by Zabbix agent")

print(template, "\n")
