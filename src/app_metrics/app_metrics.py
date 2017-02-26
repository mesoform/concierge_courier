#!/usr/bin/python

import json
import sys

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

    with open("/tmp/metrics.json", "r") as metrics:
        keys = metrics.read()
        keys_json = json.loads(keys)

        for key in keys_json['timers']:
            zbx_item = {"{#TIMER}": key}
            discovery_list['data'].append(zbx_item)
        print(__as_json(discovery_list))


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
        write_metrics("/tmp/timer_metrics_zabbix.sender", keys['timers'])
    send_metrics("timer")


def write_metrics(filename, timers_dict):
    with open(filename, "w") as sender_file:
        for timer_name, metrics in timers_dict.items():
            # print('timer_name=\'{}\', value={}'.format(timer_name, metrics))

            # dict.items() return a copy of the dictionary
            # as a list in K/V pair format key, value
            for metric_name, metric_value in metrics.items():
                sender_file.write(
                    __get_metric_record(timer_name,
                                        metric_name,
                                        metric_value)
                )
                # - timer[test.test-timer.count] 45
                #    zbx_item = {"{#TIMER}": key}
                #    discovery_list['data'].append(zbx_item)
                # print json.dumps(discovery_list, indent=4, sort_keys=True)


def send_metrics(metric_type):
    filename = "/tmp/" + metric_type + "_metrics_zabbix.sender"
    # For troubleshooting connectivity:
    # call("zabbix_sender -vv -c /etc/coprocesses/zabbix/zabbix_agentd.conf" +
    #      "-i " + filename, shell=True)

    # call(["zabbix_sender", "-i", filename,
    #       "-c", "/etc/coprocesses/zabbix/zabbix_agentd.conf", ">/dev/null"])
    command_template = 'zabbix_sender ' \
                       '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                       '-i {} >/dev/null'
    call(command_template.format(filename), shell=True)
    print(time.time() - startTime)


def __get_metric_record(timer_name: str, metric_name: str, metric_value: str):
    """
    Creates a Zabbix processable string line denoting this metric value
    :param timer_name: timer that recorded the metric
    :param metric_name: metric property name
    :param metric_value: recorded metric value
    :return: String in the format:
    '- timer[{timer_name}.{metric_name}] {metric_value}'
    """
    # python3 doesn't need to stipulate the index location inside of {}
    return "- timer[{0}.{1}] {2}\n" \
        .format(timer_name, metric_name, metric_value)


def __as_json(raw_dict: dict):
    """
    Converts any input dictionary to a pretty printed JSON
    string with sorted keys
    :param raw_dict: dictionary object to convert
    :return: a valid json string
    """
    return json.dumps(raw_dict, indent=4, sort_keys=True)


"""
put into an if statement so that if this module is imported,
the following lines aren't loaded and ran as well
"""
if __name__ == '__main__':
    action = sys.argv[1].lower()
    url = sys.argv[2].lower()
    if action == 'query_timers':
        discover_timers()
    elif action == 'get_timers':
        get_timers()
