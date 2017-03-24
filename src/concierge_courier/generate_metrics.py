#!/usr/bin/python

import json

count = 0
data = {}
while count < 2000:
    data["my.test-timer-{}".format(count)] = {
      "count": 43,
      "max": 505.33599999999996,
      "mean": 502.585391215306,
      "min": 500.191,
      "p50": 502.443,
      "p75": 504.046,
      "p95": 505.291,
      "p98": 505.33599999999996,
      "p99": 505.33599999999996,
      "p999": 505.33599999999996,
      "stddev": 1.6838970975560197,
      "m15_rate": 0.8076284847453551,
      "m1_rate": 0.8883929708459906,
      "m5_rate": 0.8220236458023953,
      "mean_rate": 0.9799289583409866,
      "duration_units": "milliseconds",
      "rate_units": "calls/second"
    }
    count += 1

json_data = json.dumps(data)
print json_data