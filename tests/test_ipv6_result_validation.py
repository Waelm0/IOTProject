"""Unit tests for delay-vector selection, independent of simulator execution."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'simulations'))
from validate_ipv6_results import alarm_delays

class AlarmVectorTests(unittest.TestCase):
    def test_only_alarm_receiver_delay_samples_are_selected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'sample.vec'
            path.write_text('version 2\n'
                            'vector 1 SmartHomeNetwork.gateway.app[1] endToEndDelay:vector ETV\n'
                            'vector 2 SmartHomeNetwork.gateway.app[0] endToEndDelay:vector ETV\n'
                            '1 200 301.0 0.005\n'
                            '2 201 302.0 0.9\n'
                            '1 202 303.0 0.12\n')
            self.assertEqual(alarm_delays(path), [.005, .12])

    def test_header_only_is_not_treated_as_measurement(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'empty.vec'
            path.write_text('version 2\nvector 0 SmartHomeNetwork.gateway.app[1] endToEndDelay:vector ETV\n')
            self.assertEqual(alarm_delays(path), [])

if __name__ == '__main__':
    unittest.main()
