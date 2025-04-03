from zabbix_utils import ZabbixAPI
from configparser import ConfigParser


class API:
    def __init__(self, url=None, token=None, user=None, password=None, creds_file=None):

        creds = None
        if creds_file:
            creds = ConfigParser()
            creds.read(creds_file)
        
        self.url = url or (creds.get("ZABBIX", "URL", fallback=None) if creds else None)
        self.token = token or (creds.get("ZABBIX", "TOKEN", fallback=None) if creds else None)
        self.user = user or (creds.get("ZABBIX", "LOGIN", fallback=None) if creds else None)
        self.password = password or (creds.get("ZABBIX", "PASSWORD", fallback=None) if creds else None)

        if not self.url:
            raise ValueError("Need to set URL")
        if not self.token and not (self.user and self.password):
            raise ValueError("Need to set CREDS")

        # Подключение к API
        self.api = self._connect()
        if self.api is not None:
            print("good")
        else:
            print("Not good")


    def _connect(self):
        api = ZabbixAPI(url=self.url)
        if self.token:
            api.login(token=self.token)
        elif self.user and self.password:
            api.login(user=self.user, password=self.password)
        else:
            raise ValueError("No credentials provided")
        # Тестовый запрос
        hosts = api.host.get(output=['hostid'], monitored_hosts=1, limit=1)
        if not hosts:
            raise ValueError("Connection test failed")
        return api


def get_templates_id(api, name):
    template_id = None
    if name is not None:
        try:
            templates = api.template.get(filter={'host': [name]}, output=['templateid'])
            if templates:
                template_id = templates[0].get('templateid')
            else:
                print("Template not found")
        except Exception as e:
            print("Error:", e)
    return template_id

def get_template_hosts(api, template_id):
    template_hosts = []
    if template_id is not None:
        try:
            res = api.template.get(templateids=[template_id], selectHosts=1, output=['hostid'])
            if res and res[0]['hosts']:
                for host in res[0]['hosts']:
                    if host.get('hostid'):
                        template_hosts.append(host['hostid'])
        except Exception as e:
            print("Error:", e)
    return template_hosts


