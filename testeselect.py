#from zabbix_api import ZabbixAPI
from pyzabbix import ZabbixAPI
from conf.zabbix import *
import json

zapi = ZabbixAPI(server)#=server, timeout=None ,log_level=loglevel)
zapi.login(username, password)


#print zapi.trigger.get({"hostids":["12500"],"selectLastEvent":["extend"]})

print json.dumps(zapi.trigger.get(hostids = '68626' , selectLastEvent = "extend"))       