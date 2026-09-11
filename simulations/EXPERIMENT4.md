# Experiment 4: application communication strategy

## Model and scope

`experiment4.ini` includes the existing baseline without changing Experiments 1-3.
`StrategyApp` extends INET 4.6 `UdpBasicApp` for UDP sockets, lifecycle and packet statistics.
It models CoAP-like polling and MQTT-like broker forwarding, not full CoAP/MQTT:
no TCP, retransmission at application level, QoS negotiation or subscription handshake.
One subscriber is statically provisioned at the gateway broker.

Both strategies use four smoke sensors, eight background sensors, one actuator,
the gateway and a core application. Sensor values change every 10 seconds starting
at `1 + 0.03 * sensorIndex` seconds: 180 updates per sensor, 720 per run.
Polling sensors compute the latest value's event identity/time at request arrival;
publishers transmit at each value change. These timestamps/identities are modeled
as fields within the stated application payload (not extra serialized bytes).

- Request/response: four core pollers each contact one sensor via IP routing through
  the gateway. The sensor returns its latest value to the requesting core port.
  Requests are 20 bytes; responses are 50 bytes. T = 1, 5, 10, 30, 60 seconds.
  Each poller's initial phase is uniform over its polling interval, after 1.2 seconds.
- Publish/subscribe: each sensor publishes 50 bytes to the gateway broker, which
  sends a 50-byte notification to the core subscriber. Event generation remains 10 s;
  it does not change with polling T.
- H = 10 or 0.1 s is the background interval for each of eight monitoring sensors:
  0.8 or 80 background packets/s. H is not the Experiment 3 sensor-count variable B.
- Duration 1800 s, five seeds 0-4. There are 50 polling runs and 10 publishing runs.

## Build and run

In the OMNeT++ terminal, build the project first. `src/Makefile` includes the new
StrategyApp.cc and the INET include path. If regenerating the Makefile, retain the
INET include directory and library reference. Local INET location: D:/omnetpp/inet4.6.

From simulations, using the bundled Windows OMNeT++ terminal:

```sh
bash run_exp4.sh -c RequestResponse -r 0..49
bash run_exp4.sh -c PublishSubscribe -r 0..9
python analyze_exp4.py
```

IDE: use executable `/IOTProject/src/smarthome`, working directory
`/IOTProject/simulations`, and ini file **experiment4.ini**. Choose RequestResponse
with runs 0..49 or PublishSubscribe with runs 0..9, using Cmdenv. Refresh afterward
and open exp4-analysis.anf for Browse Data. Do not include results_strategy_smoke.

## Metrics and interpretation

For latency screenshots, run `python export_exp4_latency.py` and open
`exp4-latency.anf`. This separate view exposes the recorded statistical fields as
ordinary scalars named `eventLatencyMean`, `eventLatencyMax`, `eventLatencyStddev`
and `eventLatencySamples`. Delay values retain seconds as their base unit. These
are derived copies of the original statistics, not new simulation measurements.
Do not add the derived folder to the main analysis, which would mix duplicated
data with the original results.

- Event latency: time from a sensor value change until the core first observes it.
  Only distinct received events contribute. Unobserved intermediate values are
  excluded from latency, so always interpret it together with event coverage.
- Event coverage: distinct events observed / 720. Slow polling can skip values even
  when every request and response arrives; this is not necessarily network loss.
  No drain period is added: updates not seen by 1800 s count as unobserved.
- Poll RTT: response arrival minus request creation time. This is different from
  event latency, which includes waiting for a poll.
- Transaction delivery: replies received / requests sent, or notifications received
  / publications sent. This includes both communication legs.
- Application traffic cost: source requests + sensor messages + broker notifications.
  IP forwarding of a poll does not create an additional application message.
  Byte totals exclude UDP/IP/MAC overhead; they are not radio airtime or total wire bytes.
- Broker forwarding overhead: number of notifications and 50 bytes per notification.
- Network energy: sum of initial minus final node storage energy under the inherited
  energy model; interpret as modeled energy, not a hardware battery-life prediction.

`deliveryDelay` is an auxiliary last-leg metric. For publishing it measures broker
to core only; use `eventLatency` for the complete sensor-to-core comparison.
All reported averages in exp4_summary.csv are averages of per-run metrics across
five seeds, except event_latency_max_ms, which is the largest observed value.
Fixed periodic events and polls can phase-lock; these results are not a general
random-event latency guarantee. Static subscriptions omit connection/setup costs.

## Evidence and checks

The analysis script checks the complete 60-run parameter/seed matrix, 1800 s duration,
counts, forward-chain conservation, nonnegative delay, and unique-event statistics.
Raw scalar files and exp4_per_run.csv preserve individual seeds. exp4_all_scalars.csv
contains raw scalar records; statistical summaries are extracted into exp4_per_run.csv.

Reference implementation reused: INET 4.6 src/inet/applications/udpapp/UdpBasicApp
and UDP socket addressing conventions from UdpEchoApp, available in the installed
INET source. Custom StrategyApp implements only the application behavior above.
