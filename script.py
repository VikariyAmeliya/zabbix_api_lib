from test_lib import API
from configparser import ConfigParser

creds = ConfigParser()
creds.read("creds.ini")

url = creds.get("ZABBIX", "URL", fallback=None)
token = creds.get("ZABBIX", "TOKEN", fallback=None)

print(url, token)

api = API(creds_file="creds.ini")

if api is not None:
    print("Connected to ", url)

#template_id = api.templates_id(api, "")
print("Template ID:", template_id)
#template_hosts = api.template_hosts(api.api, template_id)
#print("Hosts for template:", template_hosts)