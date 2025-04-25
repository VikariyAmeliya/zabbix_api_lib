from zabbix_utils import ZabbixAPI
from configparser import ConfigParser


class API:

    def __init__(self, url=None, token=None, user=None, password=None, creds_file=None):
        """
        Args:
            url: URL Zabbix API
            token: API токен
            user: Имя пользователя Zabbix
            password: Пароль Zabbix
            creds_file: Путь к .ini файлу с кредами
        """
        creds = None
        if creds_file:
            creds = ConfigParser()
            if not creds.read(creds_file):
                print(
                    f"Предупреждение: Файл конфигурации '{creds_file}' не найден или пуст.")
                creds = None

        self.url = url or (
            creds.get("ZABBIX", "URL", fallback=None) if creds else None)
        self.token = token or (
            creds.get("ZABBIX", "TOKEN", fallback=None) if creds else None)
        self.user = user or (
            creds.get("ZABBIX", "LOGIN", fallback=None) if creds else None)
        self.password = password or (
            creds.get("ZABBIX", "PASSWORD", fallback=None) if creds else None)

        if not self.url:
            raise ValueError("Необходимо указать URL")
        if not self.token and not (self.user and self.password):
            raise ValueError(
                "Необходимо указать токен или логин/пароль для аутентификации.")

        # Атрибут для хранения активного подключения ZabbixAPI
        self.api = None
        # Выполняем подключение ПРИ СОЗДАНИИ объекта
        self._connect()
        print(f"Успешное подключение к Zabbix API: {self.url} \n")

    def _connect(self):
        try:
            print(f"Попытка подключения к {self.url} \n")
            self.api = ZabbixAPI(url=self.url, timeout=5)

            if self.token:
                self.api.login(token=self.token)
            else:
                self.api.login(user=self.user, password=self.password)
                
            # Небольшая проверка, что API живой (запросим хосты)
            try_hosts = self.api.host.get(limit=1)
            if try_hosts:
                print("API доступен", "\n")
            else:
                print(f"Ошибка: Не удалось получить данные хостов. \n")
                raise ConnectionError(f"Не удалось получить данные хостов. \n") 
            
        except Exception as e:
            self.api = None
            error_message = f"Ошибка подключения к Zabbix {self.url} \n"
            print(error_message)
            raise ConnectionError(e) from None

# -------------------------------------------------------------------------------------------

    def get_template_id_by_name(self, name):
        if not self.api:
            print("Ошибка: Экземпляр API не инициализирован.")
            return None
        if not name:
            print("Предупреждение: Имя шаблона не указано.")
            return None

        try:
            templates = self.api.template.get(
                filter={'host': [name]},
                output=['templateid']
            )

            if templates:
                template_id = templates[0]['templateid']
                print(f"Найден ID: {template_id}")
                return template_id
            else:
                print(f"Шаблон с именем '{name}' не найден.")
                return None

        except Exception as e:
            print(f"Ошибка при получении ID шаблона '{name}': {e}")
            return None

# -------------------------------------------------------------------------------------------

    def get_hosts_by_template_id(self, id):
        if not self.api:
            print("Ошибка: Экземпляр API не инициализирован.")
            return []
        if not id:
            print("Предупреждение: Template ID не указан.")
            return []

        host_ids = []

        try:
            result = self.api.template.get(
                templateids=[id],
                selectHosts=['hostid'],
                output=[]
            )
            if result and 'hosts' in result[0] and result[0]['hosts']:
                host_ids = [host['hostid'] for host in result[0]['hosts']]
                print(f"Найдено хостов: {len(host_ids)}")
            else:
                print(f"Хосты для шаблона ID {id} не найдены.")

        except Exception as e:
            print(f"Ошибка при получении хостов для шаблона ID {id}: {e}")
            return []

        return host_ids

# -------------------------------------------------------------------------------------------

    def get_hostgroup_id(self, name):
        if not self.api:
            print("Ошибка: Экземпляр API не инициализирован.")
            return []
        if not name:
            print("Предупреждение: Hostgroup name не указан.")
            return []

        try:
            # Преобразуем в список, если пришла строка
            if isinstance(name, str):
                names = [name]
            else:
                names = name

            hostgroups = self.api.hostgroup.get(
                filter={"name": names},
                output=["groupid", "name"]
            )

            return [group["groupid"] for group in hostgroups]

        except Exception as e:
            print(f"Ошибка при получении hostgroup ID: {e}"
            )
            return []

# -------------------------------------------------------------------------------------------

    def get_usermacro(self, hosts):
        """
        Получение макросов хостов
        """
        if not self.api:
            print("Ошибка: API не инициализирован")
            return {}

        # Проверка входных данных
        if not hosts:
            print("Предупреждение: Не указаны хосты")
            return {}

        # Преобразуем к списку если hosts != списку если это возможно либо выдаем ошибку
        if isinstance(hosts, str):
            hosts = [hosts]
        elif not isinstance(hosts, list):
            try:
                hosts = [str(hosts)]
            except:
                print("Ошибка: hosts должен быть списком, числом или строкой")
                return {}

        # Структура для результатов
        result = {}

        try:
            # Запрашиваем макросы
            macros = self.api.usermacro.get(hostids=hosts)

            # Обрабатываем результаты
            for macro in macros:
                if 'hostid' in macro and 'macro' in macro and 'value' in macro:
                    hostid = macro['hostid']
                    macro_name = macro['macro']
                    value = macro['value']

                    # Создаем структуру словаря
                    if 'host' not in result:
                        result['host'] = {}

                    if hostid not in result['host']:
                        result['host'][hostid] = {}

                    if 'macro' not in result['host'][hostid]:
                        result['host'][hostid]['macro'] = {}

                    if macro_name not in result['host'][hostid]['macro']:
                        result['host'][hostid]['macro'][macro_name] = {}

                    # Записываем значение
                    result['host'][hostid]['macro'][macro_name]['value'] = value

            return result

        except Exception as e:
            print(f"Ошибка при получении макросов: {e}")
            return {}

# -------------------------------------------------------------------------------------------

    def get_host_tags(self, hosts):
        if not self.api:
            print("Ошибка: API не инициализирован")
            return {}

        # Проверяем входные данные
        if not hosts:
            print("Предупреждение: Не указаны хосты")
            return {}

        # Преобразуем к списку если нужно
        if isinstance(hosts, str):
                hosts = [hosts]
        elif not isinstance(hosts, list):
            try:
                hosts = [str(hosts)]     
            except:
                print("Ошибка: hosts должен быть списком, числом или строкой")
                return {}

        # Структура для результатов
        result = {}

        try:
            host_data = self.api.host.get(
                hostids=hosts,
                selectTags="extend",
                output=["host"]
            )

            # Обрабатываем результаты
            for host in host_data:
                if 'hostid' in host and 'tags' in host:
                    hostid = host['hostid']
                    tags = host['tags']

                    # Создаем структуру в результатах
                    if 'host' not in result:
                        result['host'] = {}

                    if hostid not in result['host']:
                        result['host'][hostid] = {}

                    if 'tags' not in result['host'][hostid]:
                        result['host'][hostid]['tags'] = {}

                    # Обрабатываем каждый тег
                    for tag in tags:
                        if 'tag' in tag and 'value' in tag:
                            tag_name = tag['tag']
                            tag_value = tag['value']

                            # Добавляем тег в структуру
                            if tag_name not in result['host'][hostid]['tags']:
                                result['host'][hostid]['tags'][tag_name] = {}

                            result['host'][hostid]['tags'][tag_name]['value'] = tag_value

            return result

        except Exception as e:
            print(f"Ошибка при получении тегов: {e}")
            return {}

# -------------------------------------------------------------------------------------------

    def get_usergroup(self):
        if not self.api:
            
            print("Ошибка: API не инициализирован")
            return {}

        try:
            usergroups = self.api.usergroup.get(
                output=["usrgrpid", "name", "users"],
                selectUsers=1
            )
        except Exception as e:
            print(f"Ошибка при получении данных usergroup: {e}")
            return {}

        result = {'usrgrp': {}, 'users': {}}

        for usergroup in usergroups:
            if not all(key in usergroup for key in ['usrgrpid', 'name', 'users']):
                continue

            usergrpid = usergroup['usrgrpid']
            name = usergroup['name']
            users = usergroup['users']

            # Инициализируем структуру группы
            if usergrpid not in result['usrgrp']:
                result['usrgrp'][usergrpid] = {
                    'name': name,
                    'users': {}
                }

            # Обрабатываем пользователей группы
            if isinstance(users, list):
                for user in users:
                    if isinstance(user, dict) and 'userid' in user:
                        userid = user['userid']

                        # Добавляем в группу
                        result['usrgrp'][usergrpid]['users'][userid] = {
                            'exist': True}

                        # Добавляем обратную ссылку
                        if userid not in result['users']:
                            result['users'][userid] = {'usrgrp': {}}
                        result['users'][userid]['usrgrp'][usergrpid] = {
                            'exist': True}

        return result

# -------------------------------------------------------------------------------------------

    def get_problem(self, hosts):
        if not self.api:
            print("Ошибка: API не инициализирован")
            return {}

        # Проверяем входные данные
        if not hosts:
            print("Предупреждение: Не указаны хосты")
            return {}

        # Преобразуем к списку
        if isinstance(hosts, str):
            hosts = [hosts]
        elif not isinstance(hosts, list):
            try:
                hosts = [str(hosts)]
            except:
                print("Ошибка: hosts должен быть списком, числом или строкой")
                return {}

        # Структура
        result = {}

        try:
            problems = self.api.problem.get(
                hostids=hosts,
                selectAcknowledges="extend"
            )
        except Exception as e:
            print(f"Ошибка при получении данных о problems: {e}")
            return {}

        for problem in problems:
            if not all(key in problem for key in ['name', 'clock', 'severity', 'eventid', 'objectid']):
                continue

            eventid = problem['eventid']
            result[eventid] = {
                'name': problem['name'],
                'clock': problem['clock'],
                'severity': problem['severity'],
                'objectid': problem['objectid'],
                'acknowledged': problem['acknowledged'],
                'acknowledges': {}
            }

            if 'acknowledges' in problem and isinstance(problem['acknowledges'], list):
                for acknowledge in problem['acknowledges']:
                    acknowledges_fields = ['acknowledgeid', 'message', 'clock', 'userid', 'action']
                    if all(key in acknowledge for key in acknowledges_fields):
                        ack_id = acknowledge['acknowledgeid']
                        result[eventid]['acknowledges'][ack_id] = {
                            'message': acknowledge['message'],
                            'clock': acknowledge['clock'],
                            'userid': acknowledge['userid'],
                            'action': acknowledge['action'],
                            'old_severity': acknowledge.get('old_severity', ''),
                            'new_severity': acknowledge.get('new_severity', '')
                        }

        return result
    
 # -------------------------------------------------------------------------------------------
   
    def get_hostgroup_list_v64(self):
        array = []
        hash = {}
        try:
           res = self.api.hostgroup.get()
        except Exception as e:
            print("Ошибка при получении хостов")
            return {}
        if isinstance(res, list) and len(res)>0: #Проверяем, что res = список и числовое значение > 0
            for group in res:
                if isinstance(group, dict) and "name" in group and "groupid" in group:
                    hash[group["groupid"]] = {"name": group["name"]} 
                    array.append(group["groupid"])
        return {"hash": hash, "array": array}
   
    # dict = {}
    # group = {"groupid": 123, "name": "Servers"}
    # hash = {
    #    123: {"name": "Servers"},
    #    456: {"name": "Workstations"},
    # }
# -------------------------------------------------------------------------------------------

    def get_hostgroup_hosts_v64(self, groups):
         groupids = []
         groupids = groups.split()
         
         hash = {}
         
         try:
            res = self.api.hostgroup.get(
              groupids=groupids
              selectHosts="extend"
         )
         except Exception as e:
            print(f"Ошибка при запросе хост-групп: {e}")
            return hash
        
         if isinstance(res, list) and len(res)>0:
             for groups in res:
                 if (isinstance (groups, dict) and len(groups)>0 and 'hosts' in groups and isinstance(groups['hosts'], list) and 'groupid' in groups and groups['groupid']):
                     groupid = groups['groupid']
                     for hosts in groups['hosts']:
                         if isinstance(hosts, dict) and 'name' in hosts and 'host' in hosts and 'hostid' in hosts and 'status' in hosts:
                             
                             hostid = hosts['hostid']
                             hash['all']['hostid'] = {
                                 'host': hosts['host'],
                                 'name': hosts['name'],
                                 'status': hosts['status'],
                                 'flags': hosts['flags'],
                                 'proxy': hosts['proxy']
                             }
                             

