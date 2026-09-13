from pathlib import Path
import sys
import re
import statistics
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2] / 'simulations'
sys.path.insert(0, str(ROOT))
from analyze_exp4 import parse

OUT = Path(__file__).resolve().parent
rows = []
for path in ROOT.joinpath('results_critical_event_random_1800s').glob('*.sca'):
    attrs, config, scalars, stats = parse(path)
    b = int(re.search(r'B=(\d+)', path.name).group(1))
    repetition = int(attrs['repetition'])
    sent = sum(scalars[f'SmartHomeNetwork.smokeEnvSensor[{i}].app[0]', 'packetSent:count'] for i in range(2))
    received = scalars['SmartHomeNetwork.gateway.app[1]', 'packetReceived:count']
    delay = stats['SmartHomeNetwork.gateway.app[1]', 'endToEndDelay:histogram']
    assert config['sim-time-limit'] == '1800s'
    assert 'exponential(30s)' in config.values()
    assert delay['count'] == received and received <= sent
    rows.append((b, repetition, sent, received, delay['mean'] * 1000, delay['max'] * 1000))
assert {(r[0], r[1]) for r in rows} == {(b, k) for b in [5, 10, 20, 30] for k in range(5)}
summary = []
for b in [5, 10, 20, 30]:
    runs = [r for r in rows if r[0] == b]
    summary.append((b, sum(r[2] for r in runs), sum(r[3] for r in runs), statistics.mean(r[4] for r in runs), max(r[5] for r in runs)))
print('B | sent | received | mean of run means (ms) | maximum (ms)')
for row in summary:
    print(row)

im = Image.new('RGB', (1800, 1050), 'white')
d = ImageDraw.Draw(im)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('arialbd.ttf' if bold else 'arial.ttf'), size)
def center(x, y, label, size=27, bold=False, color='#222222'):
    d.text((x, y), label, font=font(size, bold), fill=color, anchor='mt')
center(900, 32, 'Critical alarm delay under background traffic', 40, True)
center(900, 91, 'Random alarm arrivals | 1,800 s per run | 5 repetitions per load', 26)
left, right, top, bottom = 170, 1720, 220, 840
for tick in range(0, 26, 5):
    y = bottom - tick / 25 * (bottom-top)
    d.line((left, y, right, y), fill='#dddddd', width=2)
    d.text((left-22, y), str(tick), font=font(27), fill='#333333', anchor='rm')
d.line((left, top, left, bottom, right, bottom), fill='#333333', width=3)
d.text((left, 174), 'Delay (ms)', font=font(28), fill='#222222')
colors = ['#167d9a', '#b54461']
for i, row in enumerate(summary):
    x = left + (i + .5) * (right-left)/4
    for j, value in enumerate(row[3:]):
        cx = x + (-64 if j == 0 else 64)
        y = bottom - value/25*(bottom-top)
        d.rectangle((cx-46, y, cx+46, bottom-2), fill=colors[j])
        center(cx, y-42, f'{value:.3f}', 27, True)
    center(x, bottom+20, str(row[0]), 29)
center(945, 905, 'Background sensor count, B', 29)
for x, color, label in [(350, colors[0], 'Mean of five run means'), (960, colors[1], 'Maximum across five runs')]:
    d.rectangle((x, 980, x+26, 1006), fill=color)
    d.text((x+40, 977), label, font=font(27), fill='#222222')
im.save(OUT/'exp3_random_delay_chart.png', dpi=(250, 250))
print('Chart saved; all 20 randomized runs validated.')
