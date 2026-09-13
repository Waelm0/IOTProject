# Experiment 3: corrected random alarms

Use [the report section](Experiment_3_Paste_Ready.md), [capture guide](Screenshot_and_Insertion_Guide.md), and [delay chart](exp3_random_delay_chart.png) for the randomized CriticalEvent experiment. The guide's D: paths describe the original author's local workspace; the same report assets are available in this directory for other checkouts.

The authoritative results are in `simulations/results_critical_event_random_1800s`, with 20 runs: four background sensor counts and five repetitions. Open `simulations/exp3-random-analysis.anf` to inspect them. Earlier periodic results remain historical and must not be mixed with these results.

Validated totals: 1911 alarms sent and received. Mean-of-run-mean delays range from 4.403 to 4.543 ms. The largest observed delay is 22.881 ms. These are observations under the tested conditions, not a reliability guarantee.

The checked-in `.vec` files contain headers but no sample rows. Delay summaries are taken from `endToEndDelay:histogram` in `.sca` files; this package does not provide jitter or time-series measurements. `.vci` indexes are generated locally and are not included.

To regenerate the chart on Windows, install Pillow and run `python docs/experiment3_random/build_chart.py` from the repository root. The script uses the repository's existing scalar parser and Windows Arial fonts. It validates the 20 runs and writes the PNG beside the script. Screenshots described in the capture guide still need to be taken from the new results; they are not fabricated or included here.
