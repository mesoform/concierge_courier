#!/usr/bin/python

import json
import sys
import os
import requests
from subprocess import call
import time

__start_time = None
_PORT = ''
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


def to_discovery_json_for(keys_json, metrics=__ALL_METRICS_TYPES):
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


def get_metrics(json_keys, metrics_types=__ALL_METRICS_TYPES,
                output_filename="/tmp/metrics_zabbix.sender"):
    """

    :param json_keys: TODO
    :param metrics_types: list of metric types to collect
    :param output_filename: temporary file used to store formatted metrics
            before sending
    """
    with open(output_filename, "w") as sender_file:
        for metrics_type in metrics_types:
            consume_metric_records(json_keys[metrics_type],
                                   sender_file.write,
                                   metrics_type)
    send_metrics(output_filename)


def get_http_metrics(path):
    # we only want to be able make call for metrics locally otherwise
    # we risk being able to have false data injected
    port_segment = ':' + _PORT if _PORT else ''
    url = 'http://localhost' + port_segment + path
    return json.loads(requests.get(url))


def get_file_metrics(path):
    with open(path, "r") as metrics_file:
        keys = metrics_file.read()
        return json.loads(keys)


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


if __name__ == '__main__':
    # We want to return how long it took for the script to run
    __mark_start_time()

    action = sys.argv[1].lower()
    if not sys.argv[2].lower():
        metrics_path = '/tmp/metrics.json'
    else:
        metrics_path = sys.argv[2].lower()
    if sys.argv[3]:
        _PORT = sys.argv[3]
    else:
        _PORT = ''

    metric_keys = get_file_metrics(metrics_path) \
        if os.path.exists(metrics_path) else get_http_metrics(metrics_path)

    if action == 'query_metrics':
        to_discovery_json_for(metric_keys)
    elif action == 'get_metrics':
        get_metrics(metrics_path)

    __mark_end_time()
