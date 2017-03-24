"""
allow for Python2 and Python 3 import syntax of relative and absolute imports
used in imported modules like unittest. Suggest that absolute is needed
because tests are being ran from the unittest module (AppMetricsTest() extends
TestCase
"""
from __future__ import absolute_import

from unittest import TestLoader, TestCase

# mock is used to simulate any dependencies by returning some predefined result
from mock import MagicMock

""" Since the concierge_courier module itself imports the 'call' function
 from the 'subprocess' module, we ned to rename this one so that
 it doesn't get shadowed and can be used for testing """
from mock import call as mock_call

from concierge_courier.concierge_courier import *


# extend TestCase class which considers every defined method in this class as a
# individual test. Good practice should require there is a separate test for
# every function in the main application
class AppMetricsTest(TestCase):
    def test_get_metric_record(self):
        """ Test expected format on valid values """
        record = get_metric_record(metric_set_name='foo.bar',
                                   metric_key='mean_rate',
                                   metric_value=0.5, metric_type='timer')

        print("get_metric_record returned: \n'{}'".format(record))
        # function as part of TestCase that asserts an equal match of any type
        # NOTE CTRL+SPACE to list suggested functions
        self.assertEquals(record, "- timer[foo.bar.mean_rate] 0.5\n")

    def test_get_metric_record_empty_values(self):
        """ Test that it doesn't break on bad input """
        record = get_metric_record(metric_set_name='', metric_key='',
                                   metric_value='', metric_type='')

        print("get_metric_record returned: \n'{}'".format(record))
        self.assertEqual(record, "- [.] \n")

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
        # .write is not a method of MagicMock, it is just a dynamically given
        # name that identifies what is happening in the main program. E.g.
        # open(filename, "w")
        mock_callback.write.return_value = None

        consume_metric_records(test_dict, mock_callback.write, 'timer')

        mock_callback.write.assert_has_calls(
            [mock_call("- timer[foo.count] 5\n"),
             mock_call("- timer[foo.mean_rate] 2\n"),
             mock_call("- timer[bar.1m_rate] 5\n"),
             mock_call("- timer[bar.5m_rate] 6\n"),
             mock_call("- timer[bar.15m_rate] 3.4\n")], any_order=True)


def suite():
    return TestLoader().loadTestsFromTestCase(AppMetricsTest)
