#!/usr/bin/python
#coding: utf-8
__author__    = "Janssen dos Reis Lima"

from zabbix_api import ZabbixAPI
import os, sys 
#from os import *
import time
import datetime
import csv
from termcolor import colored
from progressbar import ProgressBar, Percentage, ReverseBar, ETA, Timer, RotatingMarker
from conf.zabbix import *
import json

def banner():
    print colored('''
    ______       ______ ______ _____            ________
    ___  /______ ___  /____  /____(_)___  __    ___  __/___  _____________________
    __  / _  __ `/_  __ \_  __ \_  /__  |/_/    __  /  _  / / /_  __ \  _ \_  ___/
    _  /__/ /_/ /_  /_/ /  /_/ /  / __>  <      _  /   / /_/ /_  / / /  __/  /
    /____/\__,_/ /_.___//_.___//_/  /_/|_|      /_/    \__,_/ /_/ /_/\___//_/
    ''', 'red', attrs=['bold'])
    print "" 

try:
    zapi = ZabbixAPI(server=server, path="", timeout=timeout ,log_level=loglevel)
    zapi.login(username, password)
except:
    os.system('clear')
    banner()
    print colored('    Não foi possível conectar ao Zabbix Server.', 'yellow', attrs=['bold'])
    print u"\n    Verifique se a URL " + colored (server, 'red', attrs=['bold']) + u" está disponível."
    print ""
    print colored('''
    Desenvolvido por Janssen Lima - janssen@conectsys.com.br
    ''', 'blue', attrs=['bold'])
    exit(0)

def menu():
    os.system('clear')
    banner()
    print colored("[+] - Bem-vindo ao ZABBIX TUNER - [+]\n"
    "[+] - Zabbix Tuner faz um diagnóstico do seu ambiente e propõe melhorias na busca de um melhor desempenho - [+]\n"
    "[+] - Desenvolvido por Janssen Lima - [+]\n"
    "[+] - Dúvidas/Sugestões envie e-mail para janssen@conectsys.com.br - [+]", 'blue')
    print ""
    print colored("--- Escolha uma opção do menu ---",'yellow', attrs=['bold'])
    print ""
    print "[1] - Relatório de itens do sistema"
    print "[2] - Listar itens não suportados"
    print "[3] - Desabilitar itens não suportados"
    print "[4] - Relatório da média de coleta dos itens (por tipo)"
    print "[5] - Iniciar diagnóstico"
    print "[6] - Relatório de Agentes Zabbix desatualizados"
    print "[7] - Relatório de Triggers por tempo de alarme e estado"
    print "[8] - Relatório de It Services por tempo periodo"
    print ""
    print "[0] - Sair"
    print ""
    menu_opcao()

def menu_opcao():
    opcao = raw_input( "[+] - Selecione uma opção[0-8]: ")
    if opcao == '1':
        dadosItens()
    elif opcao == '2':
        listagemItensNaoSuportados()
    elif opcao == '3':
        desabilitaItensNaoSuportados()
    elif opcao == '5':
        diagnosticoAmbiente()
    elif opcao == '6':
        agentesDesatualizados()
    elif opcao == '7':
        menu_relack()
    elif opcao == '8':
        menu_relits()
    elif opcao == '0':
        sys.exit()
    else:
        menu()

def desabilitaItensNaoSuportados():
	query = {
			"output": "extend",
			"filter": {
				"state": 1
			},
			"monitored": True
		}

	filtro = raw_input('Qual a busca para key_? [NULL = ENTER] ')
	if filtro.__len__() > 0:
		query['search']={'key_': filtro}

	limite = raw_input('Qual o limite de itens? [NULL = ENTER] ')
	if limite.__len__() > 0:
		try:
			query['limit']=int(limite)
		except:
			print 'Limite invalido'
			raw_input("Pressione ENTER para voltar")
			main()

	opcao = raw_input("Confirma operação? [s/n]")
	if opcao == 's' or opcao == 'S':
		itens = zapi.item.get(query)
		print 'Encontramos {} itens'.format(itens.__len__())
		bar = ProgressBar(maxval=itens.__len__(),widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
		i = 0
		for x in itens:
			result = zapi.item.update({"itemid": x['itemid'], "status": 1})
			i += 1
			bar.update(i)
		bar.finish()
		print "Itens desabilitados!!!"
		raw_input("Pressione ENTER para continuar")
	main()

def agentesDesatualizados():
    itens = zapi.item.get ({
                            "filter": {"key_": "agent.version"},
                            "output": ["lastvalue", "hostid"],
                            "templated": False,
                            "selectHosts": ["host"],
                            "sortorder": "ASC"
    })
    
    try:
        versaoZabbixServer = zapi.item.get ({
                                "filter": {"key_": "agent.version"},
                                "output": ["lastvalue", "hostid"],
                                "hostids": "10084"
                                })[0]["lastvalue"]
    
        print colored('{0:6} | {1:30}' .format("Versão","Host"), attrs=['bold'])

        for x in itens:
            if x['lastvalue'] != versaoZabbixServer and x['lastvalue'] <= versaoZabbixServer:
                print '{0:6} | {1:30}'.format(x["lastvalue"], x["hosts"][0]["host"])        
                print ""
                raw_input("Pressione ENTER para continuar")     
                main()
    
    except IndexError:
        print "Não foi possível obter a versão do agent no Zabbix Server."
        raw_input("Pressione ENTER para continuar")     
        main()
    
def diagnosticoAmbiente():
    print colored("[+++]", 'green'), "analisando itens não númericos"
    itensNaoNumericos = zapi.item.get ({
                                        "output": "extend",
                                        "monitored": True,
                                        "filter": {"value_type": [1, 2, 4]},
                                        "countOutput": True
    })
    print colored("[+++]", 'green'), "analisando itens ICMPPING com histórico acima de 7 dias"
    itensPing = zapi.item.get ({
                                "output": "extend",
                                "monitored": True,
                                "filter": {"key_": "icmpping"},
    })
    
    contPing = 0    
    for x in itensPing:
        if int(x["history"]) > 7:
            contPing += 1
    
    print ""
    print colored("Resultado do diagnóstico:", attrs=['bold'])
    print colored("[INFO]", 'blue'), "Quantidade de itens com chave icmpping armazenando histórico por mais de 7 dias:", contPing
    print colored("[WARN]", 'yellow', None, attrs=['blink']), "Quantidade de itens não numéricos (ativos): ", itensNaoNumericos
    print ""
    raw_input("Pressione ENTER para continuar")     
    main()
        
def listagemItensNaoSuportados():
    itensNaoSuportados = zapi.item.get({"output": ["itemid", "error", "name"],
                              "filter": {"state": 1,"status":0},
                              "monitored": True,
                              "selectHosts": ["hostid", "host"],
                              })

    if itensNaoSuportados:
        print colored('{0:5} | {1:30} | {2:40} | {3:10}' .format("Item","Nome", "Error", "Host"), attrs=['bold'])

        for x in itensNaoSuportados:
            print u'{0:5} | {1:30} | {2:40} | {3:10}'.format(x["itemid"], x["name"], x["error"], x["hosts"][0]["host"])
        print ""
    else:
        print "Não há dados a exibir"
        print ""
    raw_input("Pressione ENTER para continuar")
    main()

def dadosItens():
    itensNaoSuportados = zapi.item.get({"output": "extend",
                              "filter": {"state": 1,"status": 0},
                              "monitored": True,
                              "countOutput": True                           
                              })
    
    totalItensHabilitados = zapi.item.get({"output": "extend",
                                         "filter": {"state": 0},
                                         "monitored": True,
                                         "countOutput": True
                                         })

    itensDesabilitados = zapi.item.get({"output": "extend",
                                   "filter": {"status": 1, "flags": 0},
                                   "templated": False,
                                   "countOutput": True
                                   })

    """
    VERIFICAR PROBLEMA NESTA REQUISICAO
    itensDescobertos = zapi.item.get({"output": "extend",
                                    "selectItemDiscovery": ["itemid"],
                                    "selectTriggers": ["description"],
                                    "monitored": True
                                    })
    """
                                    
    itensZabbixAgent = zapi.item.get({"output": "extend",
                               "filter": {"type": 0},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensSNMPv1 = zapi.item.get({"output": "extend",
                               "filter": {"type": 1},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensZabbixTrapper = zapi.item.get({"output": "extend",
                               "filter": {"type": 2},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })
                                
    itensChecagemSimples = zapi.item.get({"output": "extend",
                               "filter": {"type": 3},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })                                

    itensSNMPv2 = zapi.item.get({"output": "extend",
                               "filter": {"type": 4},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })
                                
    itensZabbixInterno = zapi.item.get({"output": "extend",
                               "filter": {"type": 5},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensSNMPv3 = zapi.item.get({"output": "extend",
                               "filter": {"type": 6},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensZabbixAgentAtivo = zapi.item.get({"output": "extend",
                               "filter": {"type": 7},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensZabbixAggregate = zapi.item.get({"output": "extend",
                               "filter": {"type": 8},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensWeb = zapi.item.get({"output": "extend",
                               "filter": {"type": 9},
                                "templated": False,
                                "webitems": True,
                                "countOutput": True,
                                "monitored": True
                                })

    itensExterno = zapi.item.get({"output": "extend",
                               "filter": {"type": 10},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensDatabase = zapi.item.get({"output": "extend",
                               "filter": {"type": 11},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensIPMI = zapi.item.get({"output": "extend",
                               "filter": {"type": 12},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensSSH = zapi.item.get({"output": "extend",
                               "filter": {"type": 13},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensTelnet = zapi.item.get({"output": "extend",
                               "filter": {"type": 14},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensCalculado = zapi.item.get({"output": "extend",
                               "filter": {"type": 15},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensJMX = zapi.item.get({"output": "extend",
                               "filter": {"type": 16},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })

    itensSNMPTrap = zapi.item.get({"output": "extend",
                               "filter": {"type": 17},
                                "templated": False,
                                "countOutput": True,
                                "monitored": True
                                })                                
    """
    COMENTADO ATE RESOLVER O PROBLEMA NA REQUISICAO DOS ITENS DE DISCOVERY
    cont = 0
    for i in itensDescobertos:
        if i["itemDiscovery"]:
            cont += 1
    """

    print ""
    print "Relatório de itens"
    print "=" * 18
    print ""
    print colored("[INFO]",'blue'), "Total de itens: ", int(totalItensHabilitados) + int(itensDesabilitados) + int(itensNaoSuportados)
    print colored("[INFO]",'blue'), "Itens habilitados: ", totalItensHabilitados
    print colored("[INFO]",'blue'), "Itens desabilitados: ", itensDesabilitados
    if itensNaoSuportados > "0":
        print colored("[ERRO]",'red'), "Itens não suportados: ", itensNaoSuportados
    else:
        print colored("[-OK-]",'green'), "Itens não suportados: ", itensNaoSuportados
    #print colored("[INFO]",'blue'), "Itens descobertos: ", cont
    print ""
    print "Itens por tipo em monitoramento"
    print "=" * 14
    print colored("[INFO]",'blue'), "Itens Zabbix Agent (passivo): ", itensZabbixAgent
    print colored("[INFO]",'blue'), "Itens Zabbix Agent (ativo): ", itensZabbixAgentAtivo
    print colored("[INFO]",'blue'), "Itens Zabbix Trapper: ", itensZabbixTrapper
    print colored("[INFO]",'blue'), "Itens Zabbix Interno: ", itensZabbixInterno
    print colored("[INFO]",'blue'), "Itens Zabbix Agregado: ", itensZabbixAggregate
    print colored("[INFO]",'blue'), "Itens SNMPv1: ", itensSNMPv1
    print colored("[INFO]",'blue'), "Itens SNMPv2: ", itensSNMPv2
    print colored("[INFO]",'blue'), "Itens SNMPv3: ", itensSNMPv3
    print colored("[INFO]",'blue'), "Itens SNMNP Trap: ", itensSNMPTrap
    print colored("[INFO]",'blue'), "Itens JMX: ", itensJMX
    print colored("[INFO]",'blue'), "Itens IPMI: ", itensIPMI
    print colored("[INFO]",'blue'), "Itens SSH: ", itensSSH
    print colored("[INFO]",'blue'), "Itens Telnet: ", itensTelnet
    print colored("[INFO]",'blue'), "Itens Web: ", itensWeb
    print colored("[INFO]",'blue'), "Itens Checagem Simples: ", itensChecagemSimples
    print colored("[INFO]",'blue'), "Itens Calculado: ", itensCalculado
    print colored("[INFO]",'blue'), "Itens Checagem Externa: ", itensExterno
    print colored("[INFO]",'blue'), "Itens Database: ", itensDatabase
    print ""
    raw_input("Pressione ENTER para continuar")    
    main()

def menu_relack():
    os.system('clear')
    banner()
    print colored("[+] - Bem-vindo ao ZABBIX TUNER - [+]\n" 
    "[+] - Zabbix Tuner faz um diagnóstico do seu ambiente e propõe melhorias na busca de um melhor desempenho - [+]\n"
    "[+] - Desenvolvido por Janssen Lima - [+]\n"
    "[+] - Dúvidas/Sugestões envie e-mail para janssen@conectsys.com.br - [+]", 'blue')
    print ""
    print colored("--- Escolha uma opção para o relatório ---",'yellow', attrs=['bold'])
    print ""
    print "[1] - Relatório de triggers com Acknowledged"
    print "[2] - Relatório de triggers com Unacknowledged"
    print "[3] - Relatório de triggers com ACK/UNACK"
    print ""
    print "[0] - Sair"
    print ""
    menu_opcao_relack()

def menu_opcao_relack():

    opcao = raw_input( "[+] - Selecione uma opção[0-3]: ")

    params = {'output': ['triggerid','lastchange','comments','description'],'selectHosts':['hostid', 'host'], 'expandDescription': True, 'only_true': True, 'active': True}
    if opcao == '1':
        params['withAcknowledgedEvents'] = True
        label = 'ACK'
    elif opcao == '2':
        params['withUnacknowledgedEvents'] = True
        label = 'UNACK'
    elif opcao == '3':
        label = 'ACK/UNACK'
    elif opcao == '0':
        main()
    else:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()

    hoje = datetime.date.today()
    try:
        tmp_trigger = int(raw_input( "[+] - Selecione qual o tempo de alarme (dias): "))
    except Exception, e:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()
    dt = (hoje - datetime.timedelta(days=tmp_trigger))
    conversao = int(time.mktime(dt.timetuple()))
    operador = raw_input( "[+] - Deseja ver Triggers com mais ou menos de {0} dias [ + / - ] ? ".format(tmp_trigger))

    if operador == '+':
        params['lastChangeTill'] = conversao
    elif operador == '-':
        params['lastChangeSince'] = conversao
    else:
        raw_input("\nPressione ENTER para voltar")
        menu_relack()

    rel_ack = zapi.trigger.get(params)
    for relatorio in rel_ack:
        lastchangeConverted = datetime.datetime.fromtimestamp(float(relatorio["lastchange"])).strftime('%Y-%m-%d %H:%M')
        print ""
        print colored("[-PROBLEM-]",'red'), "Trigger {} com {} de {} dias".format(label,operador,tmp_trigger)
        print "=" * 80
        print ""
        print colored("[INFO]",'blue'), "Nome da Trigger: ", relatorio["description"],"| HOST:"+relatorio["hosts"][0]["host"]+" | ID:"+relatorio["hosts"][0]["hostid"]
        print colored("[INFO]",'blue'), "Hora de alarme: ", lastchangeConverted
        print colored("[INFO]",'blue'), "URL da trigger: {}/zabbix.php?action=problem.view&filter_set=1&filter_triggerids%5B%5D={}".format(server,relatorio["triggerid"])
        print colored("[INFO]",'blue'), "Descrição da Trigger: ", relatorio["comments"]
        print ""

    print colored("\n[INFO]",'green'), "Total de {} triggers encontradas".format(rel_ack.__len__())
    opcao = raw_input("\nDeseja gerar relatorio em arquivo? [s/n]")
    if opcao == 's' or opcao == 'S':
        with open("relatorio.csv" ,"w") as arquivo:
            arquivo.write("Nome da Trigger,Hora de alarme:,URL da trigger:,Descrição da Trigger:\r\n ")
            for relatorio in rel_ack:
                arquivo.write((relatorio["description"]).encode('utf-8'))
                arquivo.write(("| HOST:"+relatorio["hosts"][0]["host"]+" | ID:"+relatorio["hosts"][0]["hostid"]))
                arquivo.write(",")
                arquivo.write(lastchangeConverted)
                arquivo.write(",")
                arquivo.write("{}/zabbix.php?action=problem.view&filter_set=1&filter_triggerids%5B%5D={}".format(server,relatorio["triggerid"]))
                arquivo.write(",")
                arquivo.write(("\""+relatorio["comments"]+"\"").encode('utf-8'))
                arquivo.write("\r\n")

        raw_input("\nArquivo gerado com sucesso ! Pressione ENTER para voltar")
        menu_relack()
    else:   
        raw_input("\nPressione ENTER para voltar")
        menu_relack()

def status_num2string(statusid):

    if statusid == '1':
        return 'Information'
    elif statusid == '2':
        return 'Warning'
    elif statusid == '3':
        return 'Average'
    elif statusid == '4':
        return 'High'
    elif statusid == '5':
        return 'Disaster'
    else:
        return 'Not classified'

def print_relatorio(it,itsla):
    print ""
    print colored("[-PROBLEM-]",'red'), "IT Service: ", it["serviceid"]
    print "=" * 80
    print ""
    print colored("[INFO]",'blue'), "Nome : ", it["name"]
    print colored("[INFO]",'blue'), "Status: ", status_num2string(it["status"])
    print colored("[INFO]",'blue'), "Problem Time: ", itsla[it["serviceid"]]["sla"][0]["problemTime"]
    print colored("[INFO]",'blue'), "SLA / Acceptable SLA: ", str(itsla[it["serviceid"]]["sla"][0]["sla"])+"/"+it["goodsla"]
    print ""

def menu_relits():
    os.system('clear')
    banner()
    print colored("[+] - Bem-vindo ao ZABBIX TUNER - [+]\n" 
    "[+] - Zabbix Tuner faz um diagnóstico do seu ambiente e propõe melhorias na busca de um melhor desempenho - [+]\n"
    "[+] - Desenvolvido por Janssen Lima - [+]\n"
    "[+] - Dúvidas/Sugestões envie e-mail para janssen@conectsys.com.br - [+]", 'blue')
    print ""

    try:
        serviceids = int(raw_input( "[+] - Informe o Service ID a ser listado : \n"))
    except Exception as e:
        print "Formato de ID inválido, insira um valor inteiro"
        raw_input("\nPressione ENTER para voltar")
        menu_relits()

    try:
        dt_init = raw_input( "[+] - Informe a data inicio do periodo do relatorio ? (D/M/A)\n")
        dt_end = raw_input( "[+] - Informe a data fim do periodo do relatorio ? (D/M/A)\n")
        #datetime.datetime.strptime(dt_init, '%d/%m/%Y')
        #datetime.datetime.strptime(dt_end, '%d/%m/%Y')
    except ValueError:
        print "Formato de data inválido, insira um formato válido"
        raw_input("\nPressione ENTER para voltar")
        menu_relits()

    #dt_init = time.mktime(datetime.datetime.strptime(dt_init, "%d/%m/%Y").timetuple())
    #dt_end = time.mktime(datetime.datetime.strptime(dt_end, "%d/%m/%Y").timetuple())

    sid = {"output" : "extend", "serviceids" : serviceids}
    get1 = zapi.service.get(sid)
    
    parent = {"output" : "extend", "parentids" : serviceids }
    childs = zapi.service.get(parent)

    ids = []
    temp = []

    for child in childs:
        ids.append(child["serviceid"])
        temp.append(child)

    ids.append(get1[0]["serviceid"])
    temp.append(get1[0])

    itservice = { 'serviceids' : ids ,  "intervals" : [ {"from" : dt_init, "to": dt_end}]}
    get2 = zapi.service.getsla(itservice)
    
    for it in get1:
        print ""
        print_relatorio(it,get2)

    for it in childs:
        print ""
        print_relatorio(it,get2)

    opcao = raw_input("\nDeseja gerar relatorio em arquivo? [s/n]")
    if opcao == 's' or opcao == 'S':
        with open("relatorio.csv" ,"w") as csv:
            csv.write("IT Service:,Nome:,Status:,Problem Time:,SLA / Acceptable SLA:\r\n ")

            for it in temp:
                csv.write(it['serviceid'])
                csv.write(",")
                csv.write(it['name'])
                csv.write(",")
                csv.write(status_num2string(get2[it['serviceid']]["status"]))
                csv.write(",")
                csv.write(str(get2[it['serviceid']]["sla"][0]['problemTime']))
                csv.write(",")
                csv.write(str(get2[it['serviceid']]["sla"][0]["sla"])+"/"+it["goodsla"])
                csv.write("\r\n")
        
        raw_input("\nArquivo gerado com sucesso ! Pressione ENTER para voltar")
        menu()
    else:   
        raw_input("\nPressione ENTER para voltar")
        menu()
def main():
    menu()

main()
