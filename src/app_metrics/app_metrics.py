#!/usr/bin/python

import json
import sys

# import requests
# import socket
from subprocess import call
import time

# This is needed for querying Consul API but should be something passed
#  as a parameter and appended to a URL to make generic
# nodeName = socket.gethostname()

"""
Hide start time to the external world by protecting it with __ prefix.
"""
__start_time = None


def __mark_start_time():
    """
    Initializes the _start_time variable with the current time.
    Note: method will always overwrite any previous value set to that variable
    """
    global __start_time
    __start_time = time.time()


def __mark_end_time():
    """
    Prints to the standard out the difference in milliseconds between
    current time and the value contained in the _start_time variable
    """
    print(time.time() - __start_time)


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

    """ Temporarily keep code for reference """
    # discovery_list = {'data': []}
    # with open("/tmp/metrics.json", "r") as metrics_file:
    #     keys = metrics_file.read()
    #     keys = json.loads(keys)
    #     for key in keys['timers']:
    #         zbx_item = {"{#TIMER}": key}
    #         discovery_list['data'].append(zbx_item)

    with open("/tmp/metrics.json", "r") as metrics_file:
        keys = metrics_file.read()
        keys_json = json.loads(keys)
        # Use list accumulation to fill data dictionary in one go
        discovery_list = \
            {'data': [{"{#TIMER}": key} for key in keys_json['timers']]}
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
        keys_json = json.loads(keys)
        write_metrics("/tmp/timer_metrics_zabbix.sender", keys_json['timers'])
    send_metrics("timer")


def write_metrics(filename, timers_dict):
    """
    Loops through the items in the input timers dictionary,
    collects each metric contained in such a timer item and
    writes a log of that in the file represented by the input filename

    :param filename:    file to write the metrics into
    :param timers_dict: metrics source dictionary
    """
    with open(filename, "w") as sender_file:
        consume_metric_records(timers_dict, sender_file.write)


def consume_metric_records(timers_dict, metric_record_consumer):
    """
    Loops through the items in the input timers dictionary,
    creates a string record representing each metric contained in
    such a timer item and sends it for processing
    to the consumer input function

    :param timers_dict:            dictionary containing timers that represent
                                   objects each property of which is a
                                   separate metric value
    :param metric_record_consumer: callback function for consuming each
                                   constructed metric record string.
                                   This callback will be invoked immediately
                                   upon record acquisition so that progress
                                   is incremental
    """
    for timer_name, metrics in timers_dict.items():
        # print('timer_name=\'{}\', value={}'.format(timer_name, metrics))

        # dict.items() return a copy of the dictionary
        # as a list in K/V pair format key, value
        for metric_name, metric_value in metrics.items():
            metric_record_consumer(
                __get_metric_record(timer_name,
                                    metric_name,
                                    metric_value)
            )
            # zbx_item = {"{#TIMER}": key}
            # discovery_list['data'].append(zbx_item)
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


def __get_metric_record(timer_name: str,
                        metric_name: str, metric_value: object):
    """
    Creates a Zabbix processable string line denoting this metric value.
    Line is also terminated with a carriage return at the end.

    Example:
    Input: timer_name='test.test-timer', metric_name='count', metric_value=45
    Output: '- timer[test.test-timer.count] 45\n'

    :param timer_name:   timer that recorded the metric
    :param metric_name:  metric property name
    :param metric_value: recorded metric value
    :return:             String in the appropriate format:
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

    # We want to return how long it took for the script to run
    __mark_start_time()

    if action is 'query_timers':
        discover_timers()
    elif action is 'get_timers':
        get_timers()

    __mark_end_time()
