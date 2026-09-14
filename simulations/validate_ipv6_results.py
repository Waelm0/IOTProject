"""Check IPv6 runs against configuration, counters, histograms and alarm vectors."""
from pathlib import Path
import argparse
import json
import math
import re
import shlex
import statistics
from analyze_exp4 import parse

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT/'results_ipv6'

def alarm_delays(path):
    ids, values = set(), []
    for line in path.read_text().splitlines():
        if line.startswith('vector '):
            fields = shlex.split(line)
            if fields[2:4] == ['SmartHomeNetwork.gateway.app[1]', 'endToEndDelay:vector']:
                ids.add(fields[1])
        elif line and line[0].isdigit():
            fields = line.split()
            if fields[0] in ids:
                values.append(float(fields[-1]))
    return values

def validate(path):
    attrs, config, scalars, stats = parse(path)
    scenario = attrs['configname']
    assert config['**.hasIpv4'] == 'false' and config['**.hasIpv6'] == 'true', path
    raw = path.read_text()
    ipv4 = re.findall(r'^par (\S+) hasIpv4 (\S+)$', raw, re.M)
    ipv6 = re.findall(r'^par (\S+) hasIpv6 (\S+)$', raw, re.M)
    assert ipv4 and ipv6 and all(v == 'false' for _, v in ipv4), path
    assert all(v == 'true' for _, v in ipv6), path
    assert {m for m, _ in ipv4} == {m for m, _ in ipv6}, path
    assert not re.search(r'^par \S+\.ipv4\.', raw, re.M), path
    duration = float(config['sim-time-limit'].removesuffix('s'))
    seed = int(attrs['repetition'])
    if scenario != 'Baseline':
        assert duration == 1800 and int(config['seed-set']) == seed, path
    def count(prefix, name='packetSent:count'):
        return sum(v for (m,n),v in scalars.items() if m.startswith('SmartHomeNetwork.'+prefix) and '.app[' in m and n == name)
    background_sent = count('tempHumiditySensor') + count('occupancyMotionSensor')
    background_received = count('gateway.app[0]', 'packetReceived:count')
    alarm_sent = count('smokeEnvSensor')
    alarm_received = count('gateway.app[1]', 'packetReceived:count')
    assert 0 < background_received <= background_sent, path
    row = dict(config=scenario, measurement=attrs['measurement'], seed=seed,
               run=int(attrs['runnumber']), source=str(path.relative_to(ROOT)),
               ipv6_nodes=len(ipv6), duration_s=duration,
               background_sent=int(background_sent), background_received=int(background_received),
               background_pdr_percent=100*background_received/background_sent,
               background_goodput_bps=background_received*50*8/duration)
    if scenario in ('Baseline', 'Scalability', 'ReportingInterval', 'CriticalEvent'):
        assert 0 < alarm_received <= alarm_sent, path
        row.update(alarm_sent=int(alarm_sent), alarm_received=int(alarm_received),
                   alarm_pdr_percent=100*alarm_received/alarm_sent)
        for index, category in [(0, 'background'), (1, 'alarm')]:
            h = stats[f'SmartHomeNetwork.gateway.app[{index}]', 'endToEndDelay:histogram']
            assert h['count'] == (background_received if index == 0 else alarm_received), path
            assert 0 <= h['min'] <= h['mean'] <= h['max'] and math.isfinite(h['max']), path
            row[f'{category}_mean_delay_ms'] = h['mean']*1000
            row[f'{category}_max_delay_ms'] = h['max']*1000
        energies = [10000-v for (m,n),v in scalars.items() if n == 'residualEnergyCapacity:last' and '.energyStorage' in m]
        assert len(energies) == len(ipv6) and all(-1e-7 <= v <= 10000 for v in energies), path
        row['network_energy_j'] = sum(energies)
        row['network_energy_per_delivered_packet_mj'] = sum(energies)*1000/(background_received+alarm_received)
    if scenario == 'Scalability':
        n = int(re.search(r'N=(\d+)', attrs['measurement']).group(1))
        assert background_sent == n*180 and len(ipv6) == n+5, path
    if scenario == 'ReportingInterval':
        interval = int(re.search(r'T=(\d+)', attrs['measurement']).group(1))
        assert background_sent == 8*1800/interval and len(ipv6) == 17, path
    if scenario == 'CriticalEvent':
        b = int(re.search(r'B=(\d+)', attrs['measurement']).group(1))
        assert background_sent == b*180 and len(ipv6) == b+5, path
        assert config['**.smokeEnvSensor[*].app[0].sendInterval'] == 'exponential(30s)', path
        delays = alarm_delays(path.with_suffix('.vec'))
        assert len(delays) == alarm_received, f'{path}: {len(delays)} delay samples vs {alarm_received} alarms'
        assert math.isclose(statistics.mean(delays)*1000, row['alarm_mean_delay_ms'], rel_tol=1e-8), path
        assert math.isclose(max(delays)*1000, row['alarm_max_delay_ms'], rel_tol=1e-8), path
        on_time = sum(v <= .1 for v in delays)
        row.update(alarm_lost=int(alarm_sent-alarm_received), alarm_late=sum(v > .1 for v in delays),
                   alarm_on_time=on_time, deadline_ms=100,
                   deadline_delivery_percent=100*on_time/alarm_sent,
                   consecutive_delay_variation_mean_ms=statistics.mean(abs(b-a) for a,b in zip(delays,delays[1:]))*1000)
    return row

def main(partial=False):
    rows = [validate(path) for path in sorted(RESULTS.glob('*/*.sca'))]
    expected_counts = {'Baseline':1, 'Scalability':25, 'ReportingInterval':25,
                       'CriticalEvent':20, 'RequestResponse':50, 'PublishSubscribe':10}
    if not partial:
        for name, expected in expected_counts.items():
            group = [r for r in rows if r['config'] == name]
            assert len(group) == expected and len({r['run'] for r in group}) == expected, (name, len(group))
            if name != 'Baseline':
                log = (RESULTS/'logs'/f'{name}.log').read_text()
                assert log.count('Calling finish() at end of Run #') == expected and '<!> Error:' not in log, name
    summaries = []
    for config, measurement in sorted({(r['config'],r['measurement']) for r in rows}):
        group = [r for r in rows if r['config'] == config and r['measurement'] == measurement]
        if not partial and config != 'Baseline':
            assert {r['seed'] for r in group} == set(range(5)), (config, measurement)
        item = dict(config=config, measurement=measurement, runs=len(group))
        for key in group[0]:
            if key in ('config','measurement','seed','run','source','ipv6_nodes','duration_s'):
                continue
            values = [r[key] for r in group]
            item[key] = max(values) if key.endswith('_max_delay_ms') else statistics.mean(values)
        if config == 'CriticalEvent':
            for key in ['alarm_sent','alarm_received','alarm_lost','alarm_late','alarm_on_time']:
                item[key+'_total'] = sum(r[key] for r in group)
        summaries.append(item)
    (RESULTS/'validation_per_run.json').write_text(json.dumps(rows, indent=2))
    (RESULTS/'validation_summary.json').write_text(json.dumps(summaries, indent=2))
    print(f'Validated {len(rows)} IPv6 runs in {len(summaries)} parameter groups')
    for row in summaries:
        print(json.dumps(row))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true')
    main(parser.parse_args().partial)
