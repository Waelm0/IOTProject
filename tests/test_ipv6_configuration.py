"""Static checks only: never launch OMNeT++ or generate simulation results."""
from pathlib import Path
import configparser
import ipaddress
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def read_ini(name):
    parser = configparser.ConfigParser(interpolation=None, strict=False, delimiters=('=',))
    parser.optionxform = str
    text = (ROOT / 'simulations' / name).read_text()
    parser.read_string('\n'.join(line for line in text.splitlines()
                                 if not line.startswith('include ')))
    return parser

class Ipv6PreparationTests(unittest.TestCase):
    def test_stack_and_output_isolation(self):
        base = read_ini('omnetpp.ini')
        self.assertEqual(base['General']['**.hasIpv4'], 'false')
        self.assertEqual(base['General']['**.hasIpv6'], 'true')
        self.assertEqual(base['General']['*.gateway.forwarding'], 'true')
        for ini in [base, read_ini('experiment4.ini')]:
            for section in ini.values():
                if 'result-dir' in section:
                    self.assertTrue(section['result-dir'].startswith('results_ipv6/'))
                for key, value in section.items():
                    self.assertNotIn('GlobalArp', value)
                    self.assertNotIn('xmldoc("topology.xml")', value)
                    if key.endswith('.destAddresses') and value != '""':
                        self.assertIn('(ipv6)', value)

    def test_new_analysis_does_not_load_ipv4(self):
        root = ET.parse(ROOT/'simulations'/'ipv6-analysis.anf').getroot()
        patterns = [item.attrib['pattern'] for item in root.findall('inputs/input')]
        self.assertEqual(len(patterns), 2)
        self.assertTrue(all(p.startswith('results_ipv6/') for p in patterns))

    def test_static_address_plan(self):
        source = (ROOT/'src'/'SmartHomeIpv6Configurator.cc').read_text()
        self.assertIn('"2001:db8:1::%x:%x", family + 1, i + 1', source)
        addresses = {ipaddress.IPv6Address(value) for value in
                     ['2001:db8:1::1', '2001:db8:2::1', '2001:db8:2::2']}
        for family in range(1, 5):
            for index in range(1, 201):
                address = ipaddress.IPv6Address(f'2001:db8:1::{family:x}:{index:x}')
                self.assertNotIn(address, addresses)
                self.assertIn(address, ipaddress.IPv6Network('2001:db8:1::/64'))
                addresses.add(address)
        self.assertIn('numInitStages() const override { return NUM_INIT_STAGES; }', source)
        self.assertIn('stage != INITSTAGE_STATIC_ROUTING', source)
        self.assertIn('data->permanentlyAssign(linkLocal)', source)

    def test_canonical_network_and_recording(self):
        network = (ROOT/'simulations'/'package.ned').read_text()
        self.assertIn('configurator: SmartHomeIpv6Configurator', network)
        self.assertNotIn('Ipv4NetworkConfigurator', network)
        self.assertNotIn('network SmartHomeNetwork', (ROOT/'package.ned').read_text())
        self.assertIn('include simulations/omnetpp.ini', (ROOT/'omnetpp.ini').read_text())
        critical = read_ini('omnetpp.ini')['Config CriticalEvent']
        self.assertEqual(critical['repeat'], '5')
        self.assertEqual(critical['**.smokeEnvSensor[*].app[0].sendInterval'], 'exponential(30s)')
        self.assertEqual(critical['**.gateway.app[1].endToEndDelay:vector.vector-recording'], 'true')

if __name__ == '__main__':
    unittest.main()
