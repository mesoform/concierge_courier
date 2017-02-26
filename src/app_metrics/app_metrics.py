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
    metric_type = "timer"

    # using with open() as file saves having to close of the file at the end.
    with open("/tmp/metrics.json", "r") as metrics_file:
        keys = metrics_file.read()
        keys_json = json.loads(keys)
        write_metrics("/tmp/timer_metrics_zabbix.sender",
                      keys_json['timers'],
                      metric_type)
    send_metrics(metric_type)


def write_metrics(filename, metrics_dict, metric_type):
    """
    Loops through the items in the input dictionary,
    collects each metric contained in such a dictionary item and
    writes a record of that in the file represented by the input filename

    :param filename:    file to write the metrics into
    :param metrics_dict: metrics source dictionary
    :param metric_type: what type the metric is. E.g. gauge, timer, etc.
    """
    with open(filename, "w") as sender_file:
        consume_metric_records(metrics_dict, sender_file.write, metric_type)


def consume_metric_records(metrics_dict, metric_consumer_fn, metric_type):
    """
    Loops through the items in the input timers dictionary,
    creates a string record representing each metric contained in
    such a timer item and sends it for processing
    to the consumer input function

    :param metrics_dict:           dictionary containing metrics that represent
                                   objects each property of which is a
                                   separate metric value
    :param metric_consumer_fn:     callback function for consuming each
                                   constructed metric record string.
                                   This callback will be invoked immediately
                                   upon record acquisition so that progress
                                   is incremental
    :param metric_type:            what type the metric is.
    """
    for metric_set_name, metric_set in metrics_dict.items():

        # dict.items() return a copy of the dictionary
        # as a list in K/V pair format key, value
        for metric_key, metric_value in metric_set.items():
            metric_consumer_fn(
                get_metric_record(metric_set_name, metric_key, metric_value,
                                  metric_type)
            )
            # zbx_item = {"{#TIMER}": key}
            # discovery_list['data'].append(zbx_item)
            # print json.dumps(discovery_list, indent=4, sort_keys=True)


def send_metrics(metric_type):
    filename = "/tmp/{}_metrics_zabbix.sender".format(metric_type)
    # For troubleshooting connectivity:
    # call("zabbix_sender -vv -c /etc/coprocesses/zabbix/zabbix_agentd.conf" +
    #      "-i " + filename, shell=True)

    # call(["zabbix_sender", "-i", filename,
    #       "-c", "/etc/coprocesses/zabbix/zabbix_agentd.conf", ">/dev/null"])
    command_template = 'zabbix_sender ' \
                       '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                       '-i {} >/dev/null'
    call(command_template.format(filename), shell=True)


def get_metric_record(metric_set_name, metric_key, metric_value, metric_type):
    """
    Creates a Zabbix processable string line denoting this metric value.
    Line is also terminated with a carriage return at the end.

    Example:
    Input: metric_set_name='test.test-timer', metric_key='count',
        metric_value=45, metric_type='timer'
    Output: '- timer[test.test-timer.count] 45\n'
    hyphen in this output example is replaced by Zabbix for the system hostname

    :param metric_type:       str: what type the metric is.
    :param metric_set_name:   str: name prefix of the recorded the metric
    :param metric_key:        str: metric property name
    :param metric_value:      object: recorded metric value
    :return:  str: String in the appropriate format:
              '- {metric_type}[{metric_set_name}.{metric_key}] {metric_value}'
    """
    # python2.7+ doesn't need to stipulate the index location inside of {}
    return "- {}[{}.{}] {}\n" \
        .format(metric_type, metric_set_name, metric_key, metric_value)


def __as_json(raw_dict):
    """
    Converts any input dictionary to a pretty printed JSON
    string with sorted keys
    :param raw_dict: dict: dictionary object to convert
    :return:         str: a valid json string
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

    if action == 'query_timers':
        discover_timers()
    elif action == 'get_timers':
        get_timers()

    __mark_end_time()
