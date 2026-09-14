"""Validate all Experiment 4 runs and export reproducible comparison tables."""
from pathlib import Path
import csv
import math
import shlex
import statistics
import argparse

ROOT = Path(__file__).resolve().parent

def parse(path):
    scalars, stats, attrs, config = {}, {}, {}, {}
    current = None
    for line in path.read_text().splitlines():
        if line.startswith('attr ') and current is None:
            tokens = shlex.split(line)
            if len(tokens) == 3:
                attrs[tokens[1]] = tokens[2]
        elif line.startswith('config '):
            tokens = shlex.split(line)
            if len(tokens) == 3:
                config.setdefault(tokens[1], tokens[2])
        elif line.startswith('scalar '):
            _, module, name, value = shlex.split(line)
            scalars[module, name] = float(value)
            current = None
        elif line.startswith('statistic '):
            _, module, name = shlex.split(line)
            current = stats.setdefault((module, name), {})
        elif line.startswith('field ') and current is not None:
            _, name, value = line.split()
            try:
                current[name] = float(value)
            except ValueError:
                current[name] = math.nan
    return attrs, config, scalars, stats

def export(folder, partial=False):
    rows, all_scalars = [], []
    for path in sorted(folder.glob('*-rep*.sca')):
        attrs, config, scalars, stats = parse(path)
        strategy = attrs['configname']
        import re
        h = float(re.search(r'H=([\d.]+)', path.name).group(1))
        tmatch = re.search(r'T=([\d.]+)', path.name)
        t = float(tmatch.group(1)) if tmatch else 0
        seed = int(attrs['repetition'])
        assert config['sim-time-limit'] == '1800s', path
        assert config['seed-set'] == str(seed), path
        def count(prefix, name):
            return sum(v for (m,n),v in scalars.items() if m.startswith('SmartHomeNetwork.'+prefix) and '.app[' in m and n==name)
        def timing(name):
            ss = [v for (m,n),v in stats.items() if m.startswith('SmartHomeNetwork.monitoringApp.app[') and n==name+':stats' and v['count']>0]
            total = sum(v['count'] for v in ss)
            return (sum(v['mean']*v['count'] for v in ss)/total if total else math.nan,
                    max((v['max'] for v in ss), default=math.nan), total)
        observed = count('monitoringApp', 'uniqueEventsObserved')
        latency, maximum, observations = timing('eventLatency')
        rtt, _, _ = timing('roundTripTime')
        sensor_sent = count('smokeEnvSensor', 'packetSent:count')
        core_sent = count('monitoringApp', 'packetSent:count')
        received = count('monitoringApp', 'packetReceived:count')
        broker_sent = scalars.get(('SmartHomeNetwork.gateway.app[1]', 'packetSent:count'), 0)
        assert observed == observations and 0 <= observed <= 720, path
        assert 0 <= received <= sensor_sent, path
        if strategy == 'PublishSubscribe':
            assert sensor_sent == 720 and received <= broker_sent <= sensor_sent, path
        else:
            assert sensor_sent <= core_sent, path
            assert 4*math.floor((1800-1.2)/t) <= core_sent <= 4*math.ceil((1800-1.2)/t), path
        assert latency >= 0 and maximum >= latency, path
        energy = sum(10000-v for (m,n),v in scalars.items() if n=='residualEnergyCapacity:last' and '.energyStorage' in m)
        row = dict(strategy=strategy,H_s=h,T_s=t,seed=seed,generated_events=720,
            unique_events_received=int(observed),event_coverage_percent=100*observed/720,
            event_latency_mean_ms=latency*1000,event_latency_max_ms=maximum*1000,
            poll_rtt_mean_ms=rtt*1000,requests_sent=int(core_sent),sensor_messages_sent=int(sensor_sent),
            broker_forwards=int(broker_sent),core_messages_received=int(received),
            transaction_delivery_percent=100*received/(core_sent if strategy=='RequestResponse' else sensor_sent),
            strategy_app_messages=int(core_sent+sensor_sent+broker_sent),
            strategy_payload_bytes=int(core_sent*20+(sensor_sent+broker_sent)*50),
            background_sent=int(count('tempHumiditySensor','packetSent:count')+count('occupancyMotionSensor','packetSent:count')),
            background_received=int(scalars['SmartHomeNetwork.gateway.app[0]', 'packetReceived:count']),
            network_energy_j=energy)
        rows.append(row)
        for (module,name),value in scalars.items():
            all_scalars.append(dict(run=attrs['run'] if 'run' in attrs else path.stem,strategy=strategy,H=h,T=t,repetition=seed,module=module,name=name,value=value))
    if not partial:
        expected={(s,h,t,k) for s,ts in [('RequestResponse',[1,5,10,30,60]),('PublishSubscribe',[0])] for h in [10,.1] for t in ts for k in range(5)}
        assert {(r['strategy'],r['H_s'],r['T_s'],r['seed']) for r in rows}==expected, f'Expected 60 complete runs; found {len(rows)}'
    def write(name, data):
        if data:
            with (folder/name).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
    summary=[]
    for key in sorted({(r['strategy'],r['H_s'],r['T_s']) for r in rows}):
        group=[r for r in rows if (r['strategy'],r['H_s'],r['T_s'])==key]
        row=dict(strategy=key[0],H_s=key[1],T_s=key[2],runs=len(group))
        for name in rows[0]:
            if name in ['strategy','H_s','T_s','seed']: continue
            values=[r[name] for r in group]
            row[name]=max(values) if name=='event_latency_max_ms' else statistics.mean(values)
        summary.append(row)
    write('exp4_per_run.csv',rows);write('exp4_summary.csv',summary);write('exp4_all_scalars.csv',all_scalars)
    print(f'Validated {len(rows)} runs in {len(summary)} parameter groups.')
    for r in summary:
        print(f"{r['strategy']:16} H={r['H_s']:4} T={r['T_s']:4}: coverage={r['event_coverage_percent']:.2f}% latency={r['event_latency_mean_ms']:.2f}ms messages={r['strategy_app_messages']:.0f}")
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--partial',action='store_true')
    parser.add_argument('--folder',type=Path,default=ROOT/'results_ipv6'/'strategy')
    args=parser.parse_args()
    export(args.folder,args.partial)
