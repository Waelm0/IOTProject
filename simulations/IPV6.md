# IPv6 configuration and manual runs

## Status and boundary

The active Baseline, Scalability, ReportingInterval, CriticalEvent, RequestResponse,
and PublishSubscribe configurations now use IPv6 only (`hasIpv4=false`, `hasIpv6=true`).
The C++ project was compiled and static configuration checks were performed.
No simulation, including a short smoke test or initialization-only run, was started
during this preparation. Runtime connectivity and numerical results remain unverified.

This is INET IPv6 carried by the existing IEEE 802.15.4 model, NOT a 6LoWPAN
implementation. No header compression or 6LoWPAN fragmentation layer was added.
The wireless MAC retains INET's 118-byte payload MTU (127 minus its 9-byte header).
The current 50-byte UDP application payload plus 8-byte UDP and 40-byte IPv6 headers
fits that modeled limit. Do not generalize this to standards-compliant IPv6 links,
which require a 1280-byte minimum IPv6 MTU and adaptation beneath IPv6 for smaller
physical frames. The required larger-payload/6LoWPAN study still needs separate
analytical treatment. Do not label ordinary IPv6 fragmentation as 6LoWPAN fragmentation.

## Addressing and routing

`src/SmartHomeIpv6Configurator.cc` provisions the fixed star topology using INET's
interface and routing-table APIs before applications initialize. It checks duplicate
addresses and installs connected routes plus host default routes through the gateway.
Application destinations explicitly select an interface and IPv6 address.

| Interface/node | Address |
| --- | --- |
| Gateway wireless (`wlan0`) | `2001:db8:1::1/64` |
| Gateway core (`eth0`) | `2001:db8:2::1/64` |
| Monitoring application (`eth0`) | `2001:db8:2::2/64` |
| Temperature sensor i | `2001:db8:1::1:<i+1 in hexadecimal>/64` |
| Occupancy sensor i | `2001:db8:1::2:<i+1 in hexadecimal>/64` |
| Smoke sensor i | `2001:db8:1::3:<i+1 in hexadecimal>/64` |
| Actuator i | `2001:db8:1::4:<i+1 in hexadecimal>/64` |

These documentation prefixes are simulation-only addresses. MAC-derived link-local
addresses are also installed. Static provisioning avoids SLAAC/DAD startup delays;
router advertisements are disabled. Neighbor Discovery still resolves next-hop MAC
addresses and tests reachability, so its traffic/queueing may affect new measurements.
This is not the old IPv4 GlobalArp shortcut and is not an evaluation of IPv6 bootstrap.

Traffic intervals, payloads, seeds, durations, and node-count sweeps are retained.
Scalability currently uses the checked-in N={5,10,20,30,40}; it does not reproduce the
N={10,50,100,150,200} values in the earlier report without deliberately changing N.
Only CriticalEvent randomizes the smoke arrivals; the baseline's low-rate smoke
reports remain periodic. Baseline/Experiments 1-3 terminate sensor traffic at the
gateway; Experiment 4 exercises routing between the monitoring host and sensors.

## Run from the OMNeT++ IDE

1. Select the project in Project Explorer and press F5.
2. Build in Release mode. The new configurator is a compiled C++ module, so an old
   executable is not sufficient. The build target remains `src/smarthome.exe`.
3. Use Run Configurations > OMNeT++ Simulation. Select the built executable using
   Browse; the Eclipse project may be displayed as `smarthome` or `IOTProject`.
4. Set Working directory to the project's `simulations` folder. NED source folders
   must include this project's `src`, `simulations`, and the referenced INET `src`.
5. First select `omnetpp.ini`, configuration `Baseline`, run `0`, and Qtenv.
   This is a manual verification step for you; it has not been executed here.
6. Inspect a sensor and the gateway: they should contain `ipv6`, not `ipv4`.
   Check interface addresses and the gateway's routes for both /64 prefixes.
   Confirm packets reach the gateway before starting experiment batches.
7. For batches choose Cmdenv, the INI/configuration below, and the run range shown.
   Leave the GUI simulation-time-limit override empty to use each INI's 1800 s.

| Experiment | INI file | Configuration | Runs | Output folder (under simulations) |
| --- | --- | --- | --- | --- |
| Baseline check | omnetpp.ini | Baseline | 0 | results_ipv6/Baseline |
| 1 | omnetpp.ini | Scalability | 0..24 | results_ipv6/Scalability |
| 2 | omnetpp.ini | ReportingInterval | 0..24 | results_ipv6/ReportingInterval |
| 3 | omnetpp.ini | CriticalEvent | 0..19 | results_ipv6/CriticalEvent |
| 4 polling | experiment4.ini | RequestResponse | 0..49 | results_ipv6/strategy |
| 4 publishing | experiment4.ini | PublishSubscribe | 0..9 | results_ipv6/strategy |

The root `run` script delegates to `simulations/run`; root `omnetpp.ini` only
includes the canonical configuration. Prefer the simulations working directory to
keep all outputs in the documented location. The shell launcher uses your existing
`/d/omnetpp/inet4.6` installation unless INET_ROOT is explicitly overridden.

## Analysis after you run

- Open `ipv6-analysis.anf`. Its input patterns include only `results_ipv6`.
- Old analysis files intentionally remain attached to historical IPv4 results.
- CriticalEvent enables `endToEndDelay:vector.vector-recording` specifically on
  gateway.app[1]. This corrects the earlier recording selector, but sample recording
  still needs verification when you run. Scalar histogram summaries remain available.
- `python analyze_exp4.py` now targets `results_ipv6/strategy`. To analyze the old
  data explicitly, use `python analyze_exp4.py --folder results_strategy_1800s`.
- The old report/export scripts and historical report tables are not automatically
  valid IPv6 results. Regenerate reports only from completed new runs.
- Existing IPv4 outputs and topology.xml files were preserved, not converted or
  overwritten. Neither active INI loads the old IPv4 XML files.
- For Experiment 3 retain an explicitly chosen latency requirement (for example
  100 ms), and calculate its success rate from NEW IPv6 data. Do not reuse 22.881 ms
  or 100% delivery as a claim about this configuration.

## Static checks (no simulation)

From the repository root, run `python tests/test_ipv6_configuration.py`.
The script checks configuration, output separation, and the static address plan.
Compile with the normal OMNeT++ Release build; use `opp_nedtool validate` on the
NED files for syntax validation. These do not prove runtime packet delivery.

References: INET source APIs in `Ipv6RoutingTable`, `Ipv6InterfaceData`,
`L3AddressResolver`, and `Ieee802154NarrowbandMac`;
[INET IPv6 documentation](https://inet.omnetpp.org/docs/users-guide/ch-ipv6.html);
[RFC 8200, section 5](https://www.rfc-editor.org/rfc/rfc8200#section-5).
