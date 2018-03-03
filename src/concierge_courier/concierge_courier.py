#!/usr/bin/python

import json
import os
import requests
from subprocess import call
import time
import argparse

__start_time = None
__ALL_METRICS_TYPES = [
    'timers',
    'counters',
    'gauges',
    'histograms'
]
discovered_metrics = []


def get_args():
    """
    parses arguments passed on command line when running program
    :return: list of arguments
    """
    parser = argparse.ArgumentParser(
        description='Queries a given location to discover what metrics we have'
                    'available, collect and deliver them to an event management'
                    'server.\n'
                    'We can query a local file or a local HTTP endpoint. Simply'
                    ' provide a path (--path) and if there is no such file, the'
                    ' courier \nwill then attempt to query a localhost '
                    'interface. This allows easy testing. If you\'re HTTP '
                    'endpoint requires an additional \nport, specify this with '
                    '--port',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('action', choices=('discover', 'deliver'),
                        help='\ndiscover:\n'
                             'Query our metrics resource and discover what '
                             'metrics are available. Then construct a manifest '
                             'object\nand return to our event management '
                             'system.\n'
                             'deliver:\n'
                             'Query our metrics resource, collect the latest '
                             'item values and deliver them to our event '
                             'management\nsystem.\n'
                             '**Currently we only support Zabbix discovery'
                             'manifest and Dropwizard metrics resource**')
    parser.add_argument('--path', default='',
                        help='Path location to the metrics resource. If this is'
                             ' a file on disk, the file will be processed. If '
                             'no\nfile exists, concierge_courier will query:'
                             'http://localhost/metics/path/provided')
    parser.add_argument('--port', default=None,
                        help='If our HTTP metrics resource requires a port '
                             'other than port 80. This has no effect if our '
                             'metrics\nresource is a file on disk')
    return parser.parse_args()


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


def discover_metrics(keys_dict, metric_types=__ALL_METRICS_TYPES):
    """
    :return: Zabbix formatted JSON of keys
    """
    for metric_type in metric_types:
        consume_metric_records(keys_dict[metric_type],
                               discovered_metrics.append, metric_type,
                               discovery_formatter)
    print(to_discovery_json_for(discovered_metrics))


def to_discovery_json_for(keys_list):
    """
    Use list accumulation to fill data dictionary in one go.
    The square braces here are NOT part of the output, they are
    special characters that define a list and Python provides syntactic
    sugar that allows it to be wrapped (e.g. "{'data': " and "}").
    """
    return __as_json(
        {
            'data': [
                {"{#METRIC}": key} for key in keys_list
            ]
        }
    )


def get_metrics(keys_dict, metrics_types=__ALL_METRICS_TYPES,
                output_filename="/tmp/metrics_zabbix.sender"):
    """

    :param keys_dict: the whole set of metric keys as a dictionary
    :param metrics_types: list of metric types to collect
    :param output_filename: temporary file used to store formatted metrics
            before sending
    """
    with open(output_filename, "w") as sender_file:
        for metrics_type in metrics_types:
            consume_metric_records(keys_dict[metrics_type],
                                   sender_file.write, metrics_type,
                                   sender_formatter)
    send_metrics(output_filename)


def get_http_metrics(path, host_port):
    # we only want to be able make call for metrics locally otherwise
    # we risk being able to have false data injected
    port_segment = ':' + host_port if host_port else ''
    url = 'http://localhost' + port_segment + path
    return json.loads(requests.get(url))


def get_file_metrics(path):
    with open(path, "r") as metrics_file:
        metrics_json = metrics_file.read()
        return json.loads(metrics_json)


def consume_metric_records(metrics_dict, metric_consumer_fn, metrics_type,
                           metric_formatter_fn):
    """
    Loops through the items in the input dictionary, creates a string
    record representing each metric contained in such a metric item and
    sends it for processing to the consumer input function

    :param metric_formatter_fn:    function to use which returns the required
                                   output format
    :param metrics_dict:           dictionary containing metrics that represent
                                   objects each property of which is a
                                   separate metric value
    :param metric_consumer_fn:     callback function for consuming each
                                   constructed metric record string.
                                   This callback will be invoked immediately
                                   upon record acquisition so that progress
                                   is incremental
    :param metrics_type:           what type the metric is.
    """
    for metric_set_name, metric_set in metrics_dict.items():
        for metric_key, metric_value in metric_set.items():
            metric_consumer_fn(
                metric_formatter_fn(metric_set_name, metric_key, metric_value,
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


def sender_formatter(metric_set_name, metric_key, metric_value, metrics_type):
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


# noinspection PyUnusedLocal
def discovery_formatter(metric_set_name, metric_key,
                        metric_value, metrics_type):
    """
    Creates a Zabbix processable string line denoting a flattened metric name
    from a given keys of original dictionary

    :param metric_set_name: str: what type the metric is.
    :param metric_key:      str: name prefix of the recorded the metric
    :param metric_value:    NOT USED
    :param metrics_type:    str: metric property name
    :return:    str: String in the appropriate format:
              '{metrics_type}.{metric_set_name}.{metric_key}'
    """
    return "{}.{}.{}".format(metrics_type, metric_set_name, metric_key)


def __as_json(raw_dict):
    """
    Converts any input dictionary to a pretty printed JSON
    string with sorted keys
    :param raw_dict: dict: dictionary object to convert
    :return:         str: a valid json string
    """
    return json.dumps(raw_dict, indent=4, sort_keys=True)


if __name__ == '__main__':
    args = get_args()
    all_metrics_dict = get_file_metrics(args.path) \
        if os.path.exists(args.path) \
        else get_http_metrics(args.path, args.port)

    if args.action == 'discover':
        discover_metrics(all_metrics_dict)
    elif args.action == 'deliver':
        # We want to return how long it took for the script to run
        __mark_start_time()
        get_metrics(all_metrics_dict)
        __mark_end_time()
