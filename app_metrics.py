#!/usr/bin/python

import sys
import json
# import requests
# import socket
from subprocess import call
import time


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

    with open("/tmp/metrics.json", "r") as metrics_file:
        keys = metrics_file.read()
        keys = json.loads(keys)
        discovery_data_dict = \
            {"data": [{"{#TIMER}": key} for key in keys['timers']]}
    print(json.dumps(discovery_data_dict, indent=4, sort_keys=True))


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
            for key, value in keys['timers'].items():
                for metric_name, metric_value in value.items():
                    # NOTE < python2.7 needs to stipulate the index
                    # location inside of {}. E.g. "- timer[{0}.{1}] {2}\n"
                    sender_file.write("- timer[{}.{}] {}\n".format(
                        key,
                        metric_name,
                        metric_value))
    send_metrics("timer")


def send_metrics(metric_type):
    filename = "/tmp/{}_metrics_zabbix.sender".format(metric_type)
    sender_template = 'zabbix_sender ' \
                      '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                      '-i {} >/dev/null'.format(filename)
    debug_sender_template = 'zabbix_sender -vv ' \
                            '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                            '-i {}'.format(filename)
    # change sender_template to debug_sender_template for more output
    call(sender_template, shell=True)


# put into an if statement so that if any of the other classes are imported,
# the following lines aren't loaded and ran as well
if __name__ == '__main__':
    action = sys.argv[1].lower()
    url = sys.argv[2].lower()
    if action == 'query_timers':
        discover_timers()
    elif action == 'get_timers':
        # We want to return how long it took for the script to run
        startTime = time.time()
        get_timers()
        print(time.time() - startTime)
