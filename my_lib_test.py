from ZABBIX_TEST import API
from zabbix_utils import ZabbixAPI

api = API(creds_file="creds.ini")

#print(api.get_hostgroup_id(["Linux servers", "Databases", "Network devices"]))

#id_hostgroups = api.get_hostgroup_id(["Linux servers", "Databases", "Network devices"])

#print(id_hostgroups)

api2 = ZabbixAPI(credits_file="creds.ini")

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

problems = api.get_problem(hosts=10084)

print(problems, "\n") 

usermacro = api.get_usermacro(hosts=10084)
print(usermacro, "\n")

usergroup = api.get_usergroup()
print(usergroup, "\n")

host_tags = api.get_host_tags(hosts=["10084", "10631"])
print(host_tags, "\n")

template = api.get_template_id_by_name("Linux by Zabbix agent")
print(template, "\n")

hosts_template = api.get_hosts_by_template_id(template)
print(hosts_template, "\n")