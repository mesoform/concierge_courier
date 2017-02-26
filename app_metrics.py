#!/usr/bin/python

import sys
import json
# import requests
# import socket
from subprocess import call
import time

# We want to return how long it took for the script to run
startTime = time.time()

# This is needed for querying Consul API but should be something passed
#  as a parameter and appended to a URL to make generic
# nodeName = socket.gethostname()


def discover_timers():
    # discovery_list = {}
    # discovery_list['data'] = []

    # nodeServices = requests.get(url).text

    # services = json.loads(nodeServices)
    # for service in services:
    #    if service['CheckID'] != 'serfHealth':
    #        #print service['Status']
    #        #print service['ServiceName']
    #        zbx_item = {"{#SERVICEID}": service['ServiceID']}
    #        discovery_list['data'].append(zbx_item)
    # print json.dumps(discovery_list, indent=4, sort_keys=True)
    #

    discovery_list = {'data': []}

    metrics = open("/tmp/metrics.json", "r")
    keys = metrics.read()
    keys = json.loads(keys)

    for key in keys['timers']:
        zbx_item = {"{#TIMER}": key}
        discovery_list['data'].append(zbx_item)
    print(json.dumps(discovery_list, indent=4, sort_keys=True))
    metrics.close()


def get_timers():
    # url = 'http://127.0.0.1:8500/v1/health/node/{0}'.format(nodeName)
    # nodeServices = requests.get(url).text
    # services = json.loads(nodeServices)
    # status = 0
    # for service in services:
    #    if service['ServiceID'] == ServiceID:
    #        if service['Status'] == 'passing':
    #            status = 1
    #        else:
    #            status = 0
    # print status

    # using with open() as file saves having to close of the file at the end.
    with open("/tmp/metrics.json", "r") as metrics_file:
        keys = metrics_file.read()
        keys = json.loads(keys)
        with open("/tmp/timer_metrics_zabbix.sender", "w") as sender_file:
            for timer_name, metrics in keys['timers'].items():
                # print timer_name
                # print metrics
                # dict.items() return a copy of the dictionary list in K/V pair format key, value
                for metric_name, metric_value in metrics.items():
                    # python3 doesn't need to stipulate the index location inside of {}
                    sender_file.write("- timer[{0}.{1}] {2}\n".format(timer_name, metric_name, metric_value))
                    # - timer[test.test-timer.count] 45
                    #    zbx_item = {"{#TIMER}": key}
                    #    discovery_list['data'].append(zbx_item)
                    # print json.dumps(discovery_list, indent=4, sort_keys=True)
    send_metrics("timer")


def send_metrics(metric_type):
    filename = "/tmp/" + metric_type + "_metrics_zabbix.sender"
    # call(["zabbix_sender", "-i", filename, "-c", "/etc/coprocesses/zabbix/zabbix_agentd.conf", ">/dev/null"])
    # For troubleshooting connectivity:
    # call("zabbix_sender -vv -c /etc/coprocesses/zabbix/zabbix_agentd.conf -i " + filename, shell=True)
    call("zabbix_sender -c /etc/coprocesses/zabbix/zabbix_agentd.conf -i " + filename + " >/dev/null", shell=True)
    print(time.time() - startTime)

# put into an if statement so that if any of the other classes are imported, the following lines aren't loaded and ran
# as well
if __name__ == '__main__':
    action = sys.argv[1].lower()
    url = sys.argv[2].lower()
    if action == 'query_timers':
        discover_timers()
    elif action == 'get_timers':
        get_timers()
