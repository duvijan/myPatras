# Prompt: Tridosha (Vata / Pitta / Kapha) Wearable Sensing Circuit

Copy everything inside the fenced block below into your LLM of choice.
Fill in the `<<...>>` placeholders first. A shorter variant is at the end.

---

````text
# ROLE
You are a senior embedded hardware + firmware + biosignal engineer. You design
low-power wearable sensing systems in C/C++ (firmware) and Python (analysis),
and you document like an aerospace program: requirements with IDs, rationale,
verification method, and traceability.

# GOAL
Design a complete sensing system that estimates a person's relative
Vata / Pitta / Kapha (tridosha) balance from physiological signals captured by
ONE of these front-ends (I will pick; design both, flag differences):

  Option A — Wrist watch: PPG + IMU + skin temperature + EDA on the wrist.
  Option B — HRV source: chest-strap ECG (own design) OR an existing BLE
             heart-rate device that streams RR intervals (BLE Heart Rate
             Service 0x180D, characteristic 0x2A37), processed on a host.
  Option C — (optional add-on) 3-point radial pulse probe imitating Nadi
             Pariksha: three pressure/PPG elements at the index (Vata),
             middle (Pitta) and ring (Kapha) finger positions on the radial
             artery.

# SCIENTIFIC HONESTY CONSTRAINT (must be respected throughout)
- Doshas are Ayurvedic constructs with no validated one-to-one physiological
  sensor. Treat every signal->dosha mapping as a TESTABLE HYPOTHESIS, not a fact.
- The output is a "wellness / constitution index" with a confidence value,
  NOT a medical diagnosis. State this in the design and in the UI text.
- Cite literature where it exists (e.g. HRV–Prakriti studies, Nadi tarangini
  pulse studies) and mark anything speculative as [HYPOTHESIS].
- Provide a validation plan against a reference (practitioner assessment
  and/or a standardized Prakriti questionnaire, e.g. the CCRAS Prakriti
  assessment). Report agreement with Cohen's kappa / confusion matrix.

# MY CONSTRAINTS
- Skills: C, C++, Python. Prefer Zephyr RTOS or bare-metal C on the MCU,
  Python (numpy/scipy/neurokit2) on the host.
- Form factor: <<watch strap 22 mm | chest strap | benchtop proto>>
- Battery life target: <<e.g. >= 48 h with 5 min measurement every hour>>
- Budget per unit (proto): <<e.g. < 80 EUR>>
- Tools: KiCad for schematic/PCB, <<STM32CubeIDE | nRF Connect SDK>>.
- Non-medical wellness device; no mains connection while worn.

# SIGNALS TO ACQUIRE (justify sample rate, resolution, bandwidth for each)
1. PPG (green + IR/red), >= 100 Hz, ideally 250–500 Hz for waveform morphology.
2. ECG single lead (Option B own design), 250–500 Hz, 16–24 bit.
3. RR / NN intervals (derived or received via BLE), 1 ms resolution.
4. Skin temperature, +/-0.1 °C, 1 Hz.
5. EDA / GSR (tonic + phasic), DC-coupled, 4–16 Hz.
6. 3-axis accelerometer for motion artifact rejection and activity context.
7. Respiration rate (derived from RSA / PPG amplitude modulation).
8. Option C: 3-channel radial pulse pressure, >= 500 Hz, 16 bit.

# HARDWARE DESIGN — DELIVER
1. System block diagram (ASCII or Mermaid): sensors -> AFE -> MCU -> BLE ->
   phone/host -> dosha engine.
2. Component selection table with 2 candidates per block and the rationale.
   Starting candidates (challenge them if better exist):
   - MCU + BLE: nRF52840 or nRF5340
   - PPG AFE: MAX86141 / MAX30101 / AFE4404
   - ECG AFE: MAX30003 / ADS1292R / AD8232
   - EDA: MAX30001 BioZ or constant-voltage divider + 24-bit ADC (ADS1220)
   - Skin temp: TMP117 / MAX30208
   - IMU: BMI270 / LIS2DW12
   - Pulse pressure (Option C): piezo film + charge amp, or MEMS pressure
     sensors with a gel coupling cap
   - Power: LiPo + BQ25120A (or equivalent) charger/LDO, fuel gauge
3. Full schematic description per block: pin-level connections, pull-ups,
   decoupling, reference values, filter corner frequencies with the
   calculation shown, ESD on skin electrodes, electrode bias / RLD for ECG.
   Output also as a KiCad-importable netlist or SKiDL (Python) script.
4. Analog front-end math: transimpedance gain for PPG, ADC LSB vs. expected
   signal amplitude, SNR budget, anti-aliasing filter order.
5. Power budget table (mode x current x duty cycle) and resulting battery life.
6. PCB guidance: stack-up, analog/digital ground split, LED/photodiode optical
   isolation, antenna keep-out, electrode placement.
7. Safety: skin-contact materials (ISO 10993 awareness), leakage current
   limits for electrodes, battery protection, no mains while worn.
8. BOM with part numbers, quantities, and approximate cost.

# FIRMWARE — DELIVER (C / C++)
- Driver skeletons for each AFE (SPI/I2C register init, FIFO read via IRQ).
- Sampling scheduler with timestamps from a single monotonic clock.
- On-device processing: PPG peak detection, RR extraction, signal-quality
  index (SQI), motion-artifact gating with the IMU.
- BLE GATT spec: custom service with characteristics for raw stream,
  features, and dosha result; plus standard HRS for interoperability.
- Low-power state machine (idle / measure / transmit / charge).
- Unit-testable structure (pure-C feature functions testable on host).

# SIGNAL PROCESSING + FEATURE EXTRACTION — DELIVER (Python reference,
# C port for features that run on-device)
Compute over a 5-minute resting window (and 24-h trends where available):
- HRV time domain: mean HR, SDNN, RMSSD, pNN50.
- HRV frequency domain: LF, HF, LF/HF (Lomb–Scargle on RR, no resampling).
- HRV non-linear: SD1/SD2 (Poincaré), sample entropy, DFA alpha1.
- Pulse morphology: rise time, pulse width, augmentation index, dicrotic
  notch timing, amplitude variability, pulse-rate variability.
- Skin temperature mean and slope; EDA tonic level and SCR rate.
- Respiration rate; activity level (to discard non-resting windows).
- Option C: per-channel amplitude, upstroke slope, rhythm regularity, and
  cross-channel ratios (Vata/Pitta/Kapha positions).

# DOSHA ESTIMATION ENGINE — DELIVER
1. Stage 1 — transparent rule-based score, weights in a JSON config.
   Starting [HYPOTHESIS] mapping to refine with data:
   - Vata  ~ high irregularity / entropy, variable pulse amplitude,
             cooler skin, labile sympathetic activity, light fast pulse.
   - Pitta ~ higher resting HR, warmer skin, higher EDA, sharp upstroke,
             strong forceful pulse, higher LF/HF.
   - Kapha ~ lower resting HR, high vagal tone (high HF, RMSSD), slow broad
             smooth waveform, stable rhythm, low EDA.
   Normalize features with population z-scores, produce three scores that
   sum to 1 (softmax), and a confidence from SQI + window count.
2. Stage 2 — data-driven calibration: multinomial logistic regression (or
   small gradient-boosted model) trained on features vs. reference Prakriti
   labels; leave-one-subject-out cross-validation; report feature
   importance so the mapping stays explainable.
3. Distinguish Prakriti (baseline constitution, from many sessions) vs.
   Vikriti (current state, from today's session vs. personal baseline).

# REQUIREMENTS + VERIFICATION (aerospace style)
Produce a table: ID | Requirement | Rationale | Verification (T/A/I/D) |
Acceptance criterion. At least 25 requirements covering signal quality,
timing, power, BLE, safety, and algorithm. Example:
  REQ-SIG-001 | RR interval error <= 5 ms RMS vs. reference ECG at rest |
  HRV accuracy | Test | Bland–Altman vs. Polar H10 / Holter, n >= 10.

# TEST + VALIDATION PLAN
- Bench: signal generator / PPG phantom, ECG simulator, thermal chamber.
- Human pilot: n >= 30, resting supine 5 min, controlled time of day,
  caffeine/food restrictions; reference = practitioner + questionnaire.
- Metrics: accuracy, kappa, confusion matrix, test–retest repeatability (ICC).
- Failure modes: FMEA table for sensor detachment, motion, low perfusion,
  dark skin tones / tattoos (PPG bias), low battery.

# OUTPUT FORMAT
Respond in this order, using headings:
1. Assumptions and open questions (ask before guessing critical values)
2. Architecture + block diagram
3. Component selection
4. Schematic per block (+ SKiDL/KiCad netlist)
5. Power budget
6. Firmware architecture + key C code
7. Python feature + dosha pipeline (runnable, with synthetic test data)
8. Requirements table
9. Test, validation, FMEA
10. Risks, limitations, and next steps
Show calculations. Keep code compilable. Do not invent part numbers —
if unsure, say so.
````

---

## Short variant (for quick iterations)

````text
Act as an embedded biosignal engineer. Design a low-power wearable (wrist
watch: PPG+IMU+skin temp+EDA on nRF52840, OR a host app consuming RR intervals
from a BLE HRV chest strap via 0x180D/0x2A37) that estimates relative
Vata/Pitta/Kapha balance. Treat every signal->dosha mapping as a testable
hypothesis, label output as a non-medical wellness index with confidence.
Deliver: block diagram, component table, schematic per block with filter/gain
calculations, power budget, C firmware skeleton (drivers, peak detection,
SQI, BLE GATT), Python pipeline (HRV time/freq/non-linear, pulse morphology,
EDA, temp) with a rule-based softmax dosha score in JSON config plus an ML
calibration path vs. Prakriti questionnaire labels, a requirements table
(ID / requirement / verification T-A-I-D / acceptance), and a validation plan
(n>=30, kappa, ICC, FMEA). Ask for missing critical constraints first.
````

## Tips for using it
- Run it in stages: ask for sections 1–5 first, review, then 6–10.
  Long single responses tend to degrade in the later sections.
- Paste back the LLM's component choices and ask it to verify each part's
  datasheet values (supply range, interface, package) before you lay out a PCB.
- For Option B without custom hardware, start with an off-the-shelf BLE
  strap streaming RR intervals and only the Python pipeline — fastest way to
  collect data and test the dosha hypotheses before building a circuit.
