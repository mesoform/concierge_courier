#!/usr/bin/python

import json
import sys
import os

import requests
# import socket
from subprocess import CalledProcessError, check_output
import time

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


def discover_timers(path, port=None):
    """
    :return: string
    Zabbix formatted JSON of keys
    """

    if not os.path.exists(path):
        # we only want to be able make call for metrics locally otherwise
        # we risk being able to have false data injected
        if port:
            port = ':' + port
        url = 'http://localhost' + port + path
        keys = requests.get(url)
        keys_json = json.loads(keys)

        discovery_data_dict = \
            {'data': [{"{#TIMER}": key} for key in keys_json['timers']]}
    else:
        with open(path, "r") as metrics_file:
            keys = metrics_file.read()
            keys_json = json.loads(keys)

            # Note: List comprehension contained within
            # dictionary
            discovery_data_dict = \
                {'data': [{"{#TIMER}": key} for key in keys_json['timers']]}
    print(__as_json(discovery_data_dict))


def get_timers(path, port=None):
    """
    collect metrics from application and process for delivery
    :param path: HTTP of file path
    :param port: HTTP port for metrics interface, if needed
    :return: None
    """
    metric_type = "timer"
    if not os.path.exists(path):
        # we only want to be able make call for metrics locally otherwise
        # we risk being able to have false data injected
        if port:
            port = ':' + port
        url = 'http://localhost' + port + path
        keys = requests.get(url)
        keys_json = json.loads(keys)
        write_metrics("/tmp/{}_metrics_zabbix.sender".format(metric_type),
                      keys_json['timers'],
                      metric_type)
    else:
        with open(path, "r") as metrics_file:
            keys = metrics_file.read()
            keys_json = json.loads(keys)
            '''
            call out to write_metrics function, passing the file it should 
            write. Just the timers' objects
            '''
            write_metrics("/tmp/{}_metrics_zabbix.sender".format(metric_type),
                          keys_json['timers'],
                          metric_type)
    send_metrics(metric_type)


def write_metrics(filename, metrics_dict, metric_type):
    """
    Loops through the items in the input dictionary,
    collects each metric contained in such a dictionary item and
    writes a record of that in the file represented by the input filename.
    The main purpose for having this function AND consume_metric_records is
    so that consume_metric_records can be tested and isn't tied to opening a
    file (e.g. output could just be print())

    :param filename:    file to write the metrics into
    :param metrics_dict: metrics source dictionary
    :param metric_type: what type the metric is. E.g. gauge, timer, etc.
    """
    with open(filename, "w") as sender_file:
        consume_metric_records(metrics_dict, sender_file.write, metric_type)


def consume_metric_records(metrics_dict, metric_consumer_fn, metric_type):
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
    :param metric_type:            what type the metric is.
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
                                  metric_type)
            )


def send_metrics(metric_type):
    filename = "/tmp/{}_metrics_zabbix.sender".format(metric_type)
    # For troubleshooting connectivity:
    # call("zabbix_sender -vv -c /etc/coprocesses/zabbix/zabbix_agentd.conf" +
    #      "-i " + filename, shell=True)

    # call(["zabbix_sender", "-i", filename,
    #       "-c", "/etc/coprocesses/zabbix/zabbix_agentd.conf", ">/dev/null"])
    command_template = 'zabbix_sender ' \
                       '-c /etc/coprocesses/zabbix/zabbix_agentd.conf ' \
                       '-i {} 2>&1 > /dev/null'
    try:
        check_output(command_template.format(filename), shell=True)
    except CalledProcessError as e:
        ret = e.returncode
        if ret not in (0, 2):
            print(0)
            sys.exit(e.returncode)


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


if __name__ == '__main__':
    action = sys.argv[1].lower()
    if not sys.argv[2].lower():
        metrics_path = '/tmp/metrics.json'
    else:
        metrics_path = sys.argv[2].lower()

    if action == 'discover_timers':
        discover_timers(metrics_path)
    elif action == 'get_timers':
        # We want to return how long it took for the script to run
        __mark_start_time()
        get_timers(metrics_path)
        __mark_end_time()
