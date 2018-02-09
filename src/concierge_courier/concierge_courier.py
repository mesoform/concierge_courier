#!/usr/bin/python

import json
import sys
import os
import requests
# import socket
from subprocess import call
import time

__start_time = None
__ALL_METRICS_TYPES = [
    'timers',
    'counters',
    'gauges',
    'histograms'
]


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


def discover_metrics(path, port=None, metric_types=__ALL_METRICS_TYPES):
    """
    :return: Zabbix formatted JSON of keys
    """
    if not os.path.exists(path):
        # we only want to be able make call for metrics locally otherwise
        # we risk being able to have false data injected
        if port:
            port = ':' + port
        url = 'http://localhost' + port + path
        keys = requests.get(url)
        # print(to_discovery_json_for(json.loads(keys), metric_types))
    else:
        with open(path, "r") as metrics_file:
            keys = metrics_file.read()
    print(to_discovery_json_for(json.loads(keys), metric_types))


def to_discovery_json_for(keys_json, metrics):
    """
    Use list accumulation to fill data dictionary in one go.
    The square braces here are NOT part of the output, they are
    special characters that define a list and Python provides syntactic
    sugar that allows it to be wrapped (e.g. "{'data': " and "}").
    """
    return __as_json(
        {
            'data': [
                {"{#METRIC}": key} for metric in metrics
                for key in keys_json[metric]
            ]
        }
    )


def get_metrics(metrics_types=__ALL_METRICS_TYPES,
                path="/tmp/metrics.json", port=None,
                output_filename="/tmp/metrics_zabbix.sender"):
    """

    :param metrics_types: list of metric types to collect
    :param path: HTTP request path or file path
    :param port: HTTP port
    :param output_filename: temporary file used to store formatted metrics
            before sending
    """
    if not os.path.exists(path):
        # we only want to be able make call for metrics locally otherwise
        # we risk being able to have false data injected
        if port:
            port = ':' + port
        url = 'http://localhost' + port + path
        keys = requests.get(url)
        keys_json = json.loads(keys)
    else:
        with open(path, "r") as metrics_file:
            keys = metrics_file.read()
            keys_json = json.loads(keys)
    with open(output_filename, "w") as sender_file:
        for metrics_type in metrics_types:
            consume_metric_records(keys_json[metrics_type],
                                   sender_file.write,
                                   metrics_type)
    send_metrics(output_filename)


def consume_metric_records(metrics_dict, metric_consumer_fn, metrics_type):
    """
    Loops through the items in the input dictionary, creates a string
    record representing each metric contained in such a metric item and
    sends it for processing to the consumer input function

    :param metrics_dict:           dictionary containing metrics that represent
                                   objects each property of which is a
                                   separate metric value
    :param metric_consumer_fn:     callback function for consuming each
                                   constructed metric record string.
                                   This callback will be invoked immediately
                                   upon record acquisition so that progress
                                   is incremental
    :param metrics_type:            what type the metric is.
    """
    for metric_set_name, metric_set in metrics_dict.items():
        for metric_key, metric_value in metric_set.items():
            """
            here were passing back (callback) the returned response from
            get_metric_record function to sender_file.write file function
            passed to us from write metrics
            """
            metric_consumer_fn(
                get_metric_record(metric_set_name, metric_key, metric_value,
                                  metrics_type)
            )


def send_metrics(filename):
    # For troubleshooting connectivity:
    # call("zabbix_sender -vv -c /etc/coprocesses/zabbix/zabbix_agentd.conf" +
    #      "-i " + filename, shell=True)

    # call(["zabbix_sender", "-i", filename,
    #       "-c", "/etc/coprocesses/zabbix/zabbix_agentd.conf", ">/dev/null"])
    command_template = 'zabbix_sender ' \
                       '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                       '-i {} >/dev/null'
    call(command_template.format(filename), shell=True)


def get_metric_record(metric_set_name, metric_key, metric_value, metrics_type):
    """
    Creates a Zabbix processable string line denoting this metric value.
    Line is also terminated with a carriage return at the end.

    Example:
    Input: metric_set_name='test.test-timer', metric_key='count',
        metric_value=45, metrics_type='timer'
    Output: '- timers[test.test-timer.count] 45\n'
    hyphen in this output example is replaced by Zabbix for the system hostname

    :param metrics_type:       str: what type the metric is.
    :param metric_set_name:   str: name prefix of the recorded the metric
    :param metric_key:        str: metric property name
    :param metric_value:      object: recorded metric value
    :return:  str: String in the appropriate format:
              '- {metrics_type}[{metric_set_name}.{metric_key}] {metric_value}'
    """
    # python versions <2.7 require indices to be included in the braces. E.g.
    # "- {0}[{1}.{2}] {3}
    return "- {}[{}.{}] {}\n" \
        .format(metrics_type, metric_set_name, metric_key, metric_value)


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
the following lines aren't loaded and ran as well. __name__ is
special property
"""
if __name__ == '__main__':
    action = sys.argv[1].lower()
    if not sys.argv[2].lower():
        metrics_path = '/tmp/metrics.json'
    else:
        metrics_path = sys.argv[2].lower()

    if action == 'query_metrics':
        discover_metrics(metrics_path)
    elif action == 'get_metrics':
        # We want to return how long it took for the script to run
        __mark_start_time()
        get_metrics(metrics_path)
        __mark_end_time()
