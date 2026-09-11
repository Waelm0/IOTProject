"""Build the report section from the validated 60-run data package."""
from pathlib import Path
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from PIL import Image as PILImage
import shutil
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, String, Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
import pypdfium2
from analyze_exp4 import export, ROOT

summary=export(ROOT/'results_strategy_1800s')
OUT=ROOT/'results_strategy_1800s'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyR',fontName='Times-Roman',fontSize=11,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='HeadR',fontName='Times-Bold',fontSize=13,leading=16,spaceAfter=12))
styles.add(ParagraphStyle(name='SmallR',fontName='Times-Roman',fontSize=8.5,leading=10))
styles.add(ParagraphStyle(name='CapR',fontName='Times-Italic',fontSize=9,leading=11,spaceAfter=10))
story=[]
def p(s,sty='BodyR'):story.append(Paragraph(s,styles[sty]))
def table(data,widths):
    t=Table([[Paragraph(str(v),styles['SmallR']) for v in row] for row in data],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('GRID',(0,0),(-1,-1),.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(t);story.append(Spacer(1,8))
def new(title):story.append(PageBreak());p(title,'HeadR')
def get(s,h,t):return next(r for r in summary if r['strategy']==s and r['H_s']==h and r['T_s']==t)
def label(r):return 'Publish' if r['strategy']=='PublishSubscribe' else f"Poll {r['T_s']:g}s"
ordered=[get(s,h,t) for h in [10,.1] for s,ts in [('RequestResponse',[1,5,10,30,60]),('PublishSubscribe',[0])] for t in ts]

p('2.4. Experiment 4 - Application Communication Strategy','HeadR')
p('<b>Requirements:</b> Compare request/response polling with publish/subscribe forwarding through a gateway. Evaluate event latency, traffic cost versus polling interval, and behavior under higher background traffic.')
p('<b>Procedure:</b> Four smoke/environment sensors produce a new readout every 10 s. Eight other sensors generate background reports. The gateway connects the IEEE 802.15.4 access network to the Ethernet-side monitoring application. One actuator is retained. Node positions and radio settings are fixed across the comparison.')
table([['Setting','Value'],['Duration / seeds','1800 s / seed sets 0-4'],['Sensor event schedule','1 + 0.03 x sensor index, then every 10 s'],['Event count','180 per sensor; 720 total per run'],['Polling intervals, T','1, 5, 10, 30, 60 s'],['Background intervals, H','10 s (normal) and 0.1 s (high), per background sensor'],['Offered background load','0.8 versus 80 packets/s; 50-byte payloads'],['Request / response / publication size','20 / 50 / 50 bytes of application payload'],['Total runs','50 request/response + 10 publish/subscribe = 60']],[175,293])
p('<b>Strategy A - Request/response:</b> The core application runs one poller per sensor. A request passes through the gateway to the sensor, which returns its latest readout through the gateway. Each poller starts at 1.2 s plus a uniform random phase over its polling interval. Repeated replies carrying the same sensor value count only once for event coverage.')
p('<b>Strategy B - Publish/subscribe:</b> Each sensor publishes its new readout to a UDP broker application at the gateway. The broker forwards one notification to the statically configured core subscriber. Sensor identity and original event time are retained across forwarding.')
p('<b>Notes:</b> These are behavioral CoAP-like and MQTT-like strategies over UDP, not full implementations of those protocols. There is no TCP, application retry, QoS negotiation or subscription handshake. Sensor value changes are periodic; the polling sensor computes the latest value from the same schedule used by publishing. Five seeds vary random start times and wireless backoff.')
p('Source/configuration: src/StrategyApp.cc, src/StrategyApp.ned and simulations/experiment4.ini. The implementation reuses INET 4.6 UdpBasicApp socket/lifecycle behavior and the existing SmartHomeNetwork routing.','CapR')

new('Experiment 4 - Results')
p('Each row averages five 1800-second runs, except maximum event latency, which is the largest observed value. Event latency includes waiting for the core to learn a changed sensor value, while polling RTT measures only a request/reply exchange.')
table([['Load','Strategy','Event coverage (%)','Mean event latency (ms)','Max event latency (ms)','Transaction delivery (%)','App messages / run']]+[[('Normal' if r['H_s']==10 else 'High'),label(r),f"{r['event_coverage_percent']:.2f}",f"{r['event_latency_mean_ms']:.2f}",f"{r['event_latency_max_ms']:.2f}",f"{r['transaction_delivery_percent']:.3f}",f"{r['strategy_app_messages']:.1f}"] for r in ordered],[43,54,62,81,81,77,70])
p('Table 4.1. Event coverage = unique received events / 720. Transaction delivery = replies / requests for polling, or notifications / publications for publishing. Application messages exclude ordinary background traffic and do not count IP routing as an extra application send.','CapR')
new('Experiment 4 - Traffic and Energy Cost')
table([['Load','Strategy','Poll RTT (ms)','App payload bytes / run','Broker forwards / run','Network energy (J)']]+[[('Normal' if r['H_s']==10 else 'High'),label(r),('-' if r['strategy']=='PublishSubscribe' else f"{r['poll_rtt_mean_ms']:.3f}"),f"{r['strategy_payload_bytes']:.0f}",f"{r['broker_forwards']:.1f}",f"{r['network_energy_j']:.3f}"] for r in ordered],[43,63,70,105,95,92])
p('Table 4.2. Application payload cost is 20 bytes per poll plus 50 bytes per response/publication/notification. Each broker forward adds 50 application bytes. UDP/IP/MAC overhead and physical retransmissions are excluded. Energy sums initial minus final node storage under the inherited energy model.','CapR')
p('Normal and high loads use the same eight background sources. The high setting offers 100 times the background reporting rate. Traffic shown here counts only the strategy applications, while the network energy includes background traffic and all modeled node storage. These quantities therefore have different scopes.')
p('Polling repeats request/reply exchanges even if a sensor value has not changed. Publishing sends one update and one broker notification per change, so its cost tracks the event generation rate. Slow polling reduces traffic further, but the coverage results show how many intermediate values it misses.')

def chart(metric,title,ymax,step,filename):
    d=Drawing(468,175)
    lp=LinePlot();lp.x=48;lp.y=35;lp.width=395;lp.height=110
    data=[]
    for h in [10,.1]:
        data.append([(t,get('RequestResponse',h,t)[metric]) for t in [1,5,10,30,60]])
        data.append([(t,get('PublishSubscribe',h,0)[metric]) for t in [1,60]])
    lp.data=data
    palette=['#146775','#146775','#b04440','#b04440']
    for i in range(4):
        lp.lines[i].strokeColor=colors.HexColor(palette[i]);lp.lines[i].strokeWidth=1.5
        if i%2:lp.lines[i].strokeDashArray=[4,3]
    lp.xValueAxis.valueMin=0;lp.xValueAxis.valueMax=60;lp.xValueAxis.valueSteps=[1,5,10,30,60]
    lp.yValueAxis.valueMin=0;lp.yValueAxis.valueMax=ymax;lp.yValueAxis.valueStep=step
    lp.yValueAxis.visibleGrid=True;lp.yValueAxis.gridStrokeColor=colors.HexColor('#dddddd')
    d.add(lp);d.add(String(48,159,title,fontName='Times-Bold',fontSize=10));d.add(String(185,10,'Polling interval T (s)',fontSize=9))
    story.append(d);renderPDF.drawToFile(d,str(OUT/filename))

new('Experiment 4 - Comparison and Discussion')
p('Blue: normal background load. Red: high background load. Solid lines: polling. Dashed lines: publish/subscribe, shown as a fixed reference because its event interval remains 10 s.')
chart('event_latency_mean_ms','Mean event-to-core latency (ms)',10000,2000,'exp4_latency_plot.pdf')
chart('event_coverage_percent','Unique-event coverage (%)',100,20,'exp4_coverage_plot.pdf')
p('Figures 4.1-4.2. Latency must be interpreted with coverage: a low conditional delay does not account for updates that polling never observes. Overlapping curves indicate similar results at the two loads.','CapR')
normal_pub=get('PublishSubscribe',10,0);high_pub=get('PublishSubscribe',.1,0);fast=get('RequestResponse',10,1)
p(f"Publishing achieved mean event latency of {normal_pub['event_latency_mean_ms']:.2f} ms under normal load and {high_pub['event_latency_mean_ms']:.2f} ms under high load. Normal-load one-second polling averaged {fast['event_latency_mean_ms']:.2f} ms, because a new sensor value can wait for the next poll before its request/reply exchange begins.")
p(f"At normal load, one-second polling used {fast['strategy_app_messages']:.0f} application messages per run versus {normal_pub['strategy_app_messages']:.0f} for publishing. Polling at 10 s uses approximately the same message count as publishing but delays discovery. Slower 30 s and 60 s polling reduces traffic by skipping intermediate values: normal-load coverage is {get('RequestResponse',10,30)['event_coverage_percent']:.2f}% and {get('RequestResponse',10,60)['event_coverage_percent']:.2f}%, respectively.")
p('The higher background load tests contention with the same physical layout. Transaction delivery separates communication failures from missed values caused by polling frequency. Compare both loads in Table 4.1 rather than treating every unobserved event as a dropped packet.')

new('Experiment 4 - Reproducibility and Limitations')
p('<b>Reproduce:</b> Build the project, then run RequestResponse runs 0..49 and PublishSubscribe runs 0..9 using experiment4.ini with Cmdenv. In the IDE, the working directory is /IOTProject/simulations and the executable is /IOTProject/src/smarthome. Open exp4-analysis.anf after refreshing the project.')
p('The provided run_exp4.sh executes either configuration from the bundled OMNeT++ terminal. analyze_exp4.py verifies the complete run matrix and exports exp4_per_run.csv, exp4_summary.csv and exp4_all_scalars.csv. report_exp4.py regenerates this report and its two standalone plots. Detailed commands and metric definitions are in EXPERIMENT4.md.')
p('<b>Browse Data:</b> Select the RequestResponse or PublishSubscribe experiment. At monitoringApp.app[*], uniqueEventsObserved gives distinct readouts received. For the latency screenshots, export_exp4_latency.py exposes the original statistics as ordinary scalars eventLatencyMean and eventLatencyMax in exp4-latency.anf. This derived view does not rerun the simulation or change measurements. At gateway.app[1] in PublishSubscribe, packetSent:count gives broker notifications.')
p('<b>Validation:</b> All 60 parameter/seed combinations must be present. The analyzer checks 1800 s duration, seed metadata, 720 publications per publishing run, unique-event counts, nonnegative delays, and counts consistent with the request/reply or publication/forwarding chain. Short smoke tests exercise both routes before the full runs.')
p('<b>Interpretation limits:</b> Event latency is calculated only for received distinct events. Intermediate readouts overwritten before a poll cannot be recovered. No extra drain period is added at 1800 s. Periodic event generation can phase-lock with polling intervals; five random polling phases reduce dependence on one alignment but do not establish behavior for arbitrary event arrival processes.')
p('The static subscription excludes setup costs and assumes one subscriber. Poll requests cross a wireless hop in each direction, whereas publications cross the wireless link once and are forwarded over Ethernet. The reported application traffic metric counts application sends, not every link transmission. These results support this architecture and workload, not a universal CoAP-versus-MQTT performance ranking.')
p('The original high-power radio settings and simplified energy model are inherited from the baseline. Energy values describe this simulation; hardware battery-life claims require calibrated device parameters. The auxiliary deliveryDelay statistic measures the last application leg and must not replace eventLatency in the strategy comparison.')
p('<b>Source references:</b> Course handout, Experiment 4 (Project_22_8_2026.pdf, page 2). INET 4.6 UdpBasicApp and UdpEchoApp source in the installed INET framework. OMNeT++ 6.2.0 simulation environment. All values in this report come from the local results_strategy_1800s scalar files.')
def screenshot(filename, caption):
    assets=ROOT/'exp4_report_images'
    assets.mkdir(exist_ok=True)
    target=assets/filename
    if not target.exists():
        shutil.copyfile(Path('C:/Users/Layal/AppData/Local/Temp')/filename,target)
    with PILImage.open(target) as source:
        width,height=source.size
    story.append(Image(str(target),width=468,height=468*height/width))
    story.append(Spacer(1,6))
    p(caption,'CapR')

new('Experiment 4 - Polling Request Screenshots')
screenshot('codex-clipboard-ab7bacfe-c285-44e5-acef-8c9948e345fd.png',
    'Figure 4.3a. Requests sent by monitoringApp.app[0], the first of four pollers. This upper portion shows the 1 s, 10 s and part of the 30 s cases across both background loads.')
screenshot('codex-clipboard-b24d2a67-a5f9-4122-ba47-3f2a988da99b.png',
    'Figure 4.3b. Continuation of the same request-count table. The 5 s and 60 s cases send 360 and 30 requests per run, respectively. Overlapping rows retain the context of the scrolled view; they are not additional runs.')

new('Experiment 4 - Polling Coverage Screenshots')
screenshot('codex-clipboard-d06fd183-af37-4ce7-9946-64d0a4d5de02.png',
    'Figure 4.4a. Distinct events observed by the first poller. Its sensor generates 180 updates per run. At T = 10 s and high background load (H = 0.1 s), replications #2 and #3 each observe 179 of those updates.')
screenshot('codex-clipboard-caaccd94-eb2f-4011-ad90-6cd3e3a74bdf.png',
    'Figure 4.4b. Continuation of the event-coverage table. The first poller observes 60 events at T = 30 s and 30 at T = 60 s. These screenshots show one sensor; Table 4.1 combines the four sensors and five repetitions.')

new('Experiment 4 - Subscriber and Broker Screenshots')
screenshot('codex-clipboard-fb8426b9-bdcc-4a67-bfda-32fcf4dee7de.png',
    'Figure 4.5. Unique events received by the single core subscriber from all four sensors. Normal load delivers all 720 events per run; high load delivers 717-719. H is the background interval, so H = 0.1 s represents the higher traffic load.')
screenshot('codex-clipboard-610995de-c4e2-44a5-936d-d42b1ba41d3c.png',
    'Figure 4.6. Notifications sent by gateway.app[1], the broker. Counts match the subscriber observations in Figure 4.5 for every run, consistent with no further notification loss on the broker-to-core leg in these runs.')
p('The screenshots document packet and event counts. The verified event-latency measurements are presented in Table 4.1 and Figure 4.1.')

new('Experiment 4 - Mean Polling Latency Screenshots')
screenshot('codex-clipboard-181348e9-b6a0-41b3-b0bb-7e15f7532f93.png',
    'Figure 4.7a. Mean event-to-core latency for monitoringApp.app[0], the first poller. Values include waiting for a poll, not just request/reply transport time. The IDE displays either milliseconds or seconds (1 s = 1000 ms).')
screenshot('codex-clipboard-d2a94609-e4db-466d-9c13-2cfebfd866c5.png',
    'Figure 4.7b. Continuation of the first poller\'s mean latency table. These are per-run means for one sensor; Table 4.1 combines all four pollers within each run and then averages five repetitions. Slow-polling latency excludes events never observed, so it must be read with coverage.')

new('Experiment 4 - Maximum Polling Latency Screenshots')
screenshot('codex-clipboard-1b5b54fc-0c44-4436-884c-29915a93ddbe.png',
    'Figure 4.8a. Maximum observed event latency for the first poller, showing T = 1 s, 10 s and part of 30 s. These are exact statistic maxima displayed with rounded values, not histogram range boundaries.')
screenshot('codex-clipboard-7d8eda54-8c21-45c8-bc15-5f32288b2a2f.png',
    'Figure 4.8b. Continuation of the maximum latency table. Overlapping rows are repeated screen context, not extra runs. Table 4.1 reports the largest maximum over all four pollers and five seeds, so it can exceed the individual values shown here.')

new('Experiment 4 - Publish/Subscribe Latency Screenshots')
screenshot('codex-clipboard-2a1d2a80-6b58-4c91-bbb8-d16a30481d9d.png',
    'Figure 4.9. Mean sensor-event-to-core latency at the single subscriber. Each row combines all received events from the four publishers in one run. Averaging the five per-run means gives 4.70 ms at normal load and 7.48 ms at high load.')
screenshot('codex-clipboard-ca7473ae-ac31-4648-871e-3bb31a47b507.png',
    'Figure 4.10. Maximum event-to-core latency per publishing run. The worst observed values across five seeds are 24.81 ms at normal load (H = 10 s) and 62.11 ms at high load (H = 0.1 s).')
p('Figures 4.7-4.10 use a derived scalar view of the original eventLatency:stats records: eventLatencyMean copies the mean field and eventLatencyMax copies the max field. The displayed values are the existing measurements, not newly simulated results. Polling and publishing both measure from the original sensor value change to its first observation at the core.')

def footer(c,d):c.setFont('Times-Roman',9);c.drawRightString(540,30,f'Experiment 4 | {d.page}')
pdf=OUT/'Experiment_4_Report_Section.pdf'
SimpleDocTemplate(str(pdf),pagesize=(612,792),leftMargin=72,rightMargin=72,topMargin=48,bottomMargin=48).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pypdfium2.PdfDocument(str(pdf))
qa=ROOT/'results_strategy_qa';qa.mkdir(exist_ok=True)
for i in range(len(doc)):doc[i].render(scale=1.4).to_pil().save(str(qa/f'page{i+1}.png'))
print(f'Report: {pdf}, {len(doc)} pages')
