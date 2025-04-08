from ZABBIX_TEST import API
from zabbix_utils import ZabbixAPI

api = API(url = "http://192.168.1.100:8080/api_jsonrpc.php", token = "e404d027a6bf9406ec58c1eb432c2d17e423c799469256470aaa0326eb6cfa5f")

#print(api.get_hostgroup_id(["Linux servers", "Databases", "Network devices"]))

#id_hostgroups = api.get_hostgroup_id(["Linux servers", "Databases", "Network devices"])

#print(id_hostgroups)

api2 = ZabbixAPI(url = "http://192.168.1.100:8080/api_jsonrpc.php", token = "e404d027a6bf9406ec58c1eb432c2d17e423c799469256470aaa0326eb6cfa5f")

#template = api2.template.get(
 #   params = {
  #      "output": "extend",
   #     "filter":  {
    #        "host": "Linux",
     #       "templateid": ["20", "2"],
     #       "name": "Linux by Zabbix agent",
      #      "id": 1
    #    }
  #  }
#)


template = api2.template.get(
    params={
        "output": ["host", "name", "templateid"],  # Только нужные поля
        "filter": {'templateids': ["20", "2"]}
    }
)


#print(template)

problems = api.get_problem(hosts='10084')

print(problems)

