"""Run IPv6 experiments with retained console logs and explicit completion checks."""
from pathlib import Path
import argparse
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parent
INSTALL = ROOT.parents[2]
BATCHES = {'Scalability': ('omnetpp.ini', 25),
           'ReportingInterval': ('omnetpp.ini', 25),
           'CriticalEvent': ('omnetpp.ini', 20),
           'RequestResponse': ('experiment4.ini', 50),
           'PublishSubscribe': ('experiment4.ini', 10)}

def run(config, pilot=False):
    ini, count = BATCHES[config]
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join(str(p) for p in [
        INSTALL/'omnetpp-6.2.0'/'bin', INSTALL/'inet4.6'/'src',
        INSTALL/'inet4.6'/'out'/'clang-release'/'src',
        INSTALL/'omnetpp-6.2.0'/'tools'/'win32.x86_64'/'clang64'/'bin']) + os.pathsep + env['PATH']
    logdir = ROOT/('results_ipv6_validation' if pilot else 'results_ipv6')/'logs'
    logdir.mkdir(parents=True, exist_ok=True)
    log = logdir/f'{config}.log'
    if log.exists():
        raise RuntimeError(f'Log already exists: {log}; refusing to silently overwrite a batch')
    command = [str(ROOT.parent/'src'/'smarthome.exe'), '-u', 'Cmdenv',
               '-n', '.:../src:../../../inet4.6/src', '-f', ini, '-c', config,
               '-r', '0' if pilot else f'0..{count-1}',
               '--cmdenv-express-mode=true', '--cmdenv-log-level=off']
    if pilot:
        command += ['--sim-time-limit=20s', f'--result-dir=results_ipv6_validation/{config}']
    print(f'START {config}: {1 if pilot else count} runs; log={log}', flush=True)
    started = time.monotonic()
    with log.open('w') as stream:
        stream.write('Command: '+repr(command)+'\n')
        stream.flush()
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    text = log.read_text()
    completed = text.count('Calling finish() at end of Run #')
    expected = 1 if pilot else count
    if result.returncode or completed != expected or '<!> Error:' in text:
        raise RuntimeError(f'{config}: exit={result.returncode}, completed={completed}/{expected}; see {log}\n{text[-2500:]}')
    print(f'DONE {config}: {completed} runs in {time.monotonic()-started:.1f}s', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('configs', nargs='*', choices=list(BATCHES))
    args = parser.parse_args()
    for config in args.configs or BATCHES:
        run(config, args.pilot)
