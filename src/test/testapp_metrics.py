from __future__ import absolute_import

from unittest import TestLoader, TestCase

from mock import MagicMock

""" Since the app_metrics module itself imports the 'call' function
 from the 'subprocess' module, we ned to rename this one so that
 it doesn't get shadowed and can be used for testing """
from mock import call as mock_call

from app_metrics.app_metrics import *


class AppMetricsTest(TestCase):
    def test_get_get_metric_record(self):
        """ Test expected format on valid values """
        record = get_metric_record(timer_name='foo.bar',
                                   metric_name='mean_rate',
                                   metric_value=0.5)

        print("get_metric_record returned: \n'{}'".format(record))
        self.assertEquals(record, "- timer[foo.bar.mean_rate] 0.5\n")

    def test_get_get_metric_record_empty_values(self):
        """ Test that it doesn't break on bad input """
        record = get_metric_record(timer_name='',
                                   metric_name='',
                                   metric_value='')

        print("get_metric_record returned: \n'{}'".format(record))
        self.assertEquals(record, "- timer[.] \n")

    @staticmethod
    def test_consume_metric_records():
        """ Test callback is invoked """
        test_dict = {
            'foo': {
                'count': 5,
                'mean_rate': 2
            },
            'bar': {
                '1m_rate': 5,
                '5m_rate': 6,
                '15m_rate': 3.4
            }
        }
        # mock a callback object so that test does not have side effects
        mock_callback = MagicMock()
        mock_callback.write.return_value = None

        consume_metric_records(test_dict, mock_callback.write)

        mock_callback.write.assert_has_calls(
            [mock_call("- timer[foo.count] 5\n"),
             mock_call("- timer[foo.mean_rate] 2\n"),
             mock_call("- timer[bar.1m_rate] 5\n"),
             mock_call("- timer[bar.5m_rate] 6\n"),
             mock_call("- timer[bar.15m_rate] 3.4\n")], any_order=True)


def suite():
    return TestLoader().loadTestsFromTestCase(AppMetricsTest)
