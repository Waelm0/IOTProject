"""Run the 60 strategy cases in separate processes; preserve per-run audit logs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import os
import subprocess
import time
from run_ipv6_batches import ROOT, INSTALL

def main(workers):
    logdir = ROOT/'results_ipv6'/'logs'
    logdir.mkdir(parents=True, exist_ok=True)
    cases = {'RequestResponse':50, 'PublishSubscribe':10}
    # Reserve the aggregate logs so other batch launchers refuse duplicate work.
    for config in cases:
        path = logdir/f'{config}.log'
        if path.exists():
            raise RuntimeError(f'Batch already has a log: {path}')
    for config in cases:
        (logdir/f'{config}.log').write_text('Parallel batch in progress; see per-run logs.\n')
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join(str(p) for p in [
        INSTALL/'omnetpp-6.2.0'/'bin', INSTALL/'inet4.6'/'src',
        INSTALL/'inet4.6'/'out'/'clang-release'/'src',
        INSTALL/'omnetpp-6.2.0'/'tools'/'win32.x86_64'/'clang64'/'bin'])+os.pathsep+env['PATH']
    def run(config, number):
        log = logdir/f'{config}-run{number}.log'
        command = [str(ROOT.parent/'src'/'smarthome.exe'), '-u', 'Cmdenv',
                   '-n', '.:../src:../../../inet4.6/src', '-f', 'experiment4.ini',
                   '-c', config, '-r', str(number), '--cmdenv-express-mode=true',
                   '--cmdenv-log-level=off', '--cmdenv-status-frequency=30s']
        started = time.monotonic()
        with log.open('x') as stream:
            stream.write('Command: '+repr(command)+'\n')
            stream.flush()
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        text = log.read_text()
        if result.returncode or text.count('Calling finish() at end of Run #') != 1 or '<!> Error:' in text:
            raise RuntimeError(f'{config} #{number} failed; see {log}\n{text[-1500:]}')
        return config, number, time.monotonic()-started
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, config, number) for config,count in cases.items() for number in range(count)]
        for done,future in enumerate(as_completed(futures),1):
            config, number, seconds = future.result()
            print(f'{done}/60 DONE {config} #{number} ({seconds:.1f}s)', flush=True)
    for config,count in cases.items():
        combined = '\n'.join((logdir/f'{config}-run{i}.log').read_text() for i in range(count))
        (logdir/f'{config}.log').write_text(combined)
    print('All 60 strategy runs completed successfully.', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('workers must be positive')
    main(args.workers)
