# Experiment 3: screenshot and Google Docs insertion guide

## 1. Insert the report text

1. Open your Google document and locate 2.3. Experiment 3: Critical Event under Background Traffic.
2. Remove the partner-feedback placeholder under that heading. Keep the Experiment 4 heading below it.
3. Insert the report section from Experiment_3_Paste_Ready.md, stopping before EDITOR NOTES. Use the same font, size, paragraph spacing and heading styles as Experiment 1. Do not duplicate the 2.3 heading.
4. If the tables do not paste as tables, use Insert > Table. Table 3.1 requires 2 columns and 12 rows; Table 3.2 requires 7 columns and 5 rows. Fill them with the provided values. Put captions above the tables, as in Experiment 1.
5. Remove the bracketed insertion instructions once the images are inserted. Figure captions go below images.

## 2. Screenshot for Figure 3.1: randomized configuration

1. In OMNeT++, open IOTProject > simulations > omnetpp.ini.
2. Scroll to [Config CriticalEvent]. Maximize the editor area if necessary.
3. Show the lines for sim-time-limit, repeat, seed-set, B, both 10s background intervals, uniform(300s, 600s), and exponential(30s). Include result-dir when it fits legibly.
4. Press Windows+Shift+S and drag around the configuration. Capture two consecutive images if one image makes the text too small. Do not omit the randomized timing lines.
5. Save the image(s) in this folder as exp3_config.png (and exp3_config_part2.png if needed).
6. Insert directly after Table 3.1 with the supplied Figure 3.1 caption.

## 3. Insert the chart for Figure 3.2

The finished chart is already generated from your 20 new .sca files:
D:/omnetpp/output/experiment3_random/exp3_random_delay_chart.png

1. In Google Docs, place the cursor after Table 3.2.
2. Choose Insert > Image > Upload from computer.
3. Navigate to D:\omnetpp\output\experiment3_random and select exp3_random_delay_chart.png.
4. Use In line placement and resize proportionally to fit the text width. Do not stretch the image.
5. Add the supplied Figure 3.2 caption on the next line. There is no need to screenshot the chart or rerun simulations.

## 4. Confirm the analysis contains only new runs

1. In OMNeT++ Project Explorer select IOTProject and press F5 to refresh.
2. Open simulations > exp3-random-analysis.anf.
3. On Inputs, verify that both patterns refer only to results_critical_event_random_1800s:
   results_critical_event_random_1800s/CriticalEvent-B=*-rep*.sca
   results_critical_event_random_1800s/CriticalEvent-B=*-rep*.vec
4. Do not add results_critical_event_1800s, any previous periodic folder, or a broad simulations/**/*.sca pattern. Matching the CriticalEvent experiment name alone does not distinguish old and new runs.
5. Open Browse Data. Clear measurement and replication filters to show all loads and all five repetitions.

## 5. Screenshot for Figure 3.3: received alarms

1. Select Scalars.
2. Enter CriticalEvent in the experiment filter.
3. In the module filter, select SmartHomeNetwork.gateway.app[1] from the dropdown.
4. In the result-name filter, enter packetReceived:count.
5. Confirm that there are 20 rows. Enlarge the table so Experiment, Measurement, Replication, Module, Name and Value are readable.
6. These are the expected counts for repetitions 0, 1, 2, 3 and 4 respectively:
   B=5: 96, 99, 86, 116, 99
   B=10: 90, 96, 87, 88, 84
   B=20: 96, 82, 103, 113, 97
   B=30: 101, 101, 94, 107, 76
7. Use Windows+Shift+S to capture the filters and table. Save as exp3_received.png and insert with the Figure 3.3 caption.
8. Seeing 1800 in every row means the old periodic results are loaded; fix Inputs before taking the screenshot.

## 6. Screenshot for Figure 3.4: delay summaries

1. In the same analysis, select Histograms rather than Scalars or Vectors.
2. Keep experiment CriticalEvent and module SmartHomeNetwork.gateway.app[1].
3. Replace the result-name filter with endToEndDelay:histogram.
4. Leave measurement and replication filters empty so all 20 runs remain visible.
5. Widen the Count and Mean columns so their values and units can be read. Include StdDev if there is space. Capture the table and filters as exp3_delay_summary.png.
6. Insert it under the Figure 3.4 caption. Histogram range endpoints are bin boundaries, not exact observed maxima: do not use them to recreate the maximum-delay column.
7. Do not search for eventLatency:stats here. Experiment 3 uses endToEndDelay:histogram; eventLatencyMean belongs to the separate Experiment 4 reporting view.

## 7. Optional supporting screenshots: transmitted alarms

These can go in an appendix; they are not needed as two more large figures in the main section.

1. Return to Scalars and set result name to packetSent:count.
2. Select module SmartHomeNetwork.smokeEnvSensor[0].app[0]. Keep CriticalEvent selected and other filters empty. Capture all 20 rows.
3. Repeat for SmartHomeNetwork.smokeEnvSensor[1].app[0].
4. For each matching B and repetition, add the two sensor counts and compare the sum with the gateway received count. Do not compare one sensor alone with the gateway total.
5. Caption: Application-layer transmitted alarm counts for smoke/environmental sensor 0 (or 1), across all randomized CriticalEvent runs.

## 8. Final checks

- Main section: two tables, one chart, and three screenshot figures (configuration, received counts, delay summaries).
- All screenshot tables come from exp3-random-analysis.anf.
- Units in Table 3.2 and the chart are milliseconds.
- Counts are totals across five repetitions; mean delay averages five per-run means; maximum is the largest observed sample across those repetitions.
- No old 9000-alarm totals, periodic 2s alarm description, or fixed 1800 received alarms per run remains.
- Do not claim proven reliability outside the simulated conditions or a safety-standard deadline.

Official UI references:
- Google Docs images: https://support.google.com/docs/answer/97447
- Google Docs tables: https://support.google.com/docs/answer/1696711
- OMNeT++ result analysis: https://docs.omnetpp.org/6.4/userguide/result-analysis (the exact layout may differ slightly from your installed version).
