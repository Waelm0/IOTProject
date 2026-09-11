"""Expose existing latency statistics as ordinary scalars for IDE screenshots.

No simulation is run and no original result is modified. Keep this view separate
from exp4-analysis.anf so its derived values are not mixed with raw measurements.
"""
import json
import math
from analyze_exp4 import ROOT, parse

source = ROOT / 'results_strategy_1800s'
destination = ROOT / 'results_strategy_latency_view'
destination.mkdir(exist_ok=True)
fields = {'mean': 'eventLatencyMean', 'max': 'eventLatencyMax',
          'stddev': 'eventLatencyStddev', 'count': 'eventLatencySamples'}
files = sorted(source.glob('*-rep*.sca'))
assert len(files) == 60, 'Expected the completed 60-run experiment'
total = 0
for path in files:
    attrs, _, _, stats = parse(path)
    lines = ['version 3', 'run ' + json.dumps(path.stem + '-latency-view')]
    for key in ['configname', 'experiment', 'measurement', 'replication',
                'repetition', 'seedset', 'iterationvars', 'network']:
        if key in attrs:
            lines.append('attr ' + key + ' ' + json.dumps(attrs[key]))
    lines.append('attr derivedFrom ' + json.dumps(path.name))
    for (module, name), values in stats.items():
        if not module.startswith('SmartHomeNetwork.monitoringApp.app[') or name != 'eventLatency:stats':
            continue
        assert values['count'] > 0
        for field, display_name in fields.items():
            value = values[field]
            assert math.isfinite(value)
            lines.append(f'scalar {module} {display_name} {value:.17g}')
            if field != 'count':
                lines.append('attr unit s')
            total += 1
    (destination/path.name).write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(f'Exported {total} ordinary scalar entries from {len(files)} original runs.')
