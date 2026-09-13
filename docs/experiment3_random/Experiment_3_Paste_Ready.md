# 2.3. Experiment 3: Critical Event under Background Traffic

The goal of this experiment is to evaluate whether critical smoke/environmental alarms can be delivered reliably and promptly while periodic monitoring traffic shares the wireless channel. In a smart-home network, an alarm may occur while temperature/humidity and occupancy/motion sensors are transmitting routine reports. Increasing the number of background sensors can increase competition for channel access and may affect alarm delay and delivery reliability.

This experiment varies the number of background sensors while keeping two alarm sources fixed. Unlike periodic monitoring traffic, the alarm sources generate packets at randomized times. The evaluation focuses on alarm packet delivery ratio (PDR), observed packet loss, mean end-to-end delay, and maximum observed delay.

## 2.3.1. Implementation

The experiment uses the SmartHomeNetwork topology and the CriticalEvent configuration, which extends Baseline. All constrained devices communicate with the central gateway over the IEEE 802.15.4 wireless network. The background sensor count is swept over B = {5, 10, 20, 30}, with ceil(B/2) temperature/humidity sensors and floor(B/2) occupancy/motion sensors. Each background sensor sends a 50-byte application payload every 10 s. The number of smoke/environmental sensors remains fixed at two, and one actuator remains in the topology.

Each smoke/environmental sensor uses UdpBasicApp to represent a sequence of randomly occurring alarm events. Its first transmission time is sampled uniformly between 300 s and 600 s, allowing background traffic to begin before alarms occur. Subsequent inter-alarm intervals follow an exponential distribution with a mean of 30 s. Thus, 30 s is an average interval, not a fixed transmission period. Each generated 50-byte packet represents a new modeled alarm. This is an abstract alarm-arrival model, rather than a simulation of physical smoke detection. The mean interval is a workload assumption chosen for this experiment, not a measured real-world smoke-event frequency.

Each load configuration is simulated for 1800 s and repeated five times using seed sets 0 through 4, giving 20 runs in total. Repetitions retain the same configuration but change the pseudorandom sequence used by stochastic components. The results are stored separately in results_critical_event_random_1800s; the earlier periodic-alarm results are excluded from this analysis.

Critical alarms are received by SmartHomeNetwork.gateway.app[1]. The measured delay is the time from creation of an alarm packet at the sensor application to reception at this gateway application. It does not include physical detection time, forwarding to the monitoring application, or actuator response. No alarm-specific priority mechanism is introduced by this configuration.

Table 3.1: Experiment 3 configuration.

| Parameter | Value |
| --- | --- |
| Background sensor count, B | 5, 10, 20, 30 |
| Background reporting interval | 10 s per sensor |
| Background application payload | 50 bytes |
| Alarm sources | 2 smoke/environmental sensors |
| First alarm time | Uniform distribution between 300 s and 600 s |
| Subsequent inter-alarm intervals | Exponential distribution, mean 30 s |
| Alarm application payload | 50 bytes |
| Simulation duration | 1800 s per run |
| Repetitions | 5 per load, seed sets 0-4 |
| Total runs | 20 |
| Alarm receiver | SmartHomeNetwork.gateway.app[1] |

[Insert configuration screenshot here.]

Figure 3.1: CriticalEvent configuration showing the background-load sweep, randomized alarm timing, simulation duration, and repetitions.

## 2.3.2. Discussion of Results

Alarm transmission counts are obtained by summing packetSent:count from the two smoke/environmental sensor applications. Received alarm counts are obtained from packetReceived:count at gateway.app[1]. PDR is calculated as 100 times the received count divided by the transmitted count. Observed loss is the transmitted count minus the received count, and the observed loss percentage is 100 minus PDR. Delay statistics are extracted from the gateway application's endToEndDelay:histogram summary in the scalar result files.

Table 3.2 reports total transmitted and received alarms across the five repetitions at each load. Mean delay is the arithmetic mean of the five per-run mean delays; maximum delay is the largest individual delay observed across those runs. Consequently, the maximum column is not an average of run maxima.

Table 3.2: Critical alarm delivery and delay under increasing background load.

| B | Alarms sent | Alarms received | PDR (%) | Lost alarms | Mean delay (ms) | Maximum delay (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 496 | 496 | 100 | 0 | 4.403 | 7.562 |
| 10 | 445 | 445 | 100 | 0 | 4.503 | 10.145 |
| 20 | 491 | 491 | 100 | 0 | 4.440 | 9.185 |
| 30 | 479 | 479 | 100 | 0 | 4.543 | 22.881 |

[Insert exp3_random_delay_chart.png here.]

Figure 3.2: Mean and maximum sensor-to-gateway alarm delay for each background sensor count. Mean bars average five run means; maximum bars show the largest observed delay across five runs.

All 1911 generated alarm packets were received at the gateway, yielding an observed PDR of 100% and an observed loss rate of 0% at every tested load. Unlike the previous periodic-alarm configuration, the randomized configuration does not produce a fixed alarm count per run. The different totals are therefore consistent with the randomized first-alarm times and inter-alarm intervals. The measured zero loss applies to these simulated runs and should not be interpreted as a guarantee of zero loss under all operating conditions.

Mean delay remains approximately 4.4-4.5 ms and does not increase monotonically with B. These small differences do not demonstrate a strong average-delay dependence on background load. The largest observed delay increases from 7.562 ms at B = 5 to 22.881 ms at B = 30, although the intermediate results are also nonmonotonic. This is consistent with occasional longer channel-access delays, but the summary statistics alone do not identify the precise cause of each delay peak.

The offered background load ranges from 0.5 to 3 application packets per second in aggregate. These results indicate that, for the tested workload and topology, the network delivered the modeled alarms reliably with low sensor-to-gateway delay. They do not establish a congestion threshold or demonstrate behavior under more severe interference or heavier traffic. Alarm-generation assumptions, physical detection delays, and application-level response time remain outside the scope of this experiment.

[Insert gateway received-count screenshot here.]

Figure 3.3: Received alarm counts at gateway.app[1] for all 20 randomized CriticalEvent runs.

[Insert gateway delay-summary screenshot here.]

Figure 3.4: Per-run endToEndDelay histogram summaries at the alarm receiver, showing the sample count and mean delay for the randomized runs.

---

EDITOR NOTES - DO NOT INCLUDE IN REPORT

- Replace the feedback placeholder currently under section 2.3 in your Google document with the section above.
- Replace bracketed insertion instructions with the actual images; do not leave the instructions in the submitted report.
- Table/Figure 3.x numbering is experiment-based. If your final report numbers tables and figures consecutively, renumber these after Experiment 2 is finalized.
- The PDF supplied has a completed Experiment 1 and a draft Experiment 2; this section follows Experiment 1's Implementation / Discussion of Results structure.
- No jitter or time-series plot is claimed: the new vector files contain no sample records. The scalar histogram summaries do contain the delay statistics used here.
- If you retain a 100 ms deadline from an earlier draft, explicitly call it an assumed study target, not a handout requirement or safety standard. All observed delays are below it, but the report above does not introduce an unsupported deadline requirement.
- Do not reuse screenshots with 1800 alarms received per run or tables showing 9000 received per load: those belong to the old periodic experiment.
