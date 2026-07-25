# Clinical Alarm Management Simulator
## Master Technical Walkthrough — Phases 2, 3, and 4

> **Purpose:** This document explains how the project was built from physiological waveforms to a simplified alarm-management simulator and an educational Streamlit dashboard. It is written so that a reader with limited Python, biomedical signal-processing, or alarm-system knowledge can follow the implementation.
>
> **Important disclaimer:** This is an educational engineering project. It is not a medical device, has not undergone clinical or regulatory validation, and must not be used for diagnosis, treatment, patient monitoring, or clinical decision-making.

---

# 1. Project at a Glance

The Clinical Alarm Management Simulator explores a simplified version of the data path that can exist in patient monitoring:

**Physiological waveform → signal processing → derived parameter → threshold evaluation → contextual checks → simulated alarm decision → workflow explanation**

The project focuses on retrospective Bradycardia and Tachycardia records from the selected PhysioNet/Computing in Cardiology Challenge 2015 training data.

The implementation is divided conceptually into:

- **Phase 2 — Signal-processing foundation:** extract ECG-derived heart rate (HR), PLETH-derived pulse rate (PR), and simple rate-quality indicators.
- **Phase 3 — Alarm-system simulation and evaluation:** create a threshold-only baseline system (System A), a simplified context-aware system (System B), persistence logic, cross-parameter context, dataset evaluation, and error-case analysis.
- **Phase 4 — Educational clinical-workflow dashboard:** present waveforms, derived parameters, alarm decisions, decision explanations, and representative troubleshooting cases in Streamlit.

The target portfolio roles are:

- Clinical Application Specialist
- Product Specialist
- Technical/Application Support

The value of the project is therefore not only the code. It is also the ability to explain how raw signals become displayed parameters, how parameter behavior affects alarm logic, where uncertainty can enter the pipeline, and how a user might systematically investigate an unexpected alarm.

---

# 2. End-to-End Architecture

The main ECG path is:

```text
WFDB physiological record
        ↓
Select ECG Lead II
        ↓
QRS detection using WFDB XQRS
        ↓
QRS sample indices
        ↓
Convert samples to time
        ↓
Calculate RR intervals
        ↓
HR = 60 / RR interval
        ↓
Select HR estimates in 290–300 s evaluation window
        ↓
System A threshold classification
        ↓
Target threshold-crossing count
        ↓
Persistence + rate-quality context
        ↓
System B decision
        ↓
ALARM / REVIEW / NO_ALARM
        ↓
Dashboard explanation and educational workflow
```

The secondary PLETH path is:

```text
PLETH waveform
        ↓
Peak detection using scipy.signal.find_peaks
        ↓
Peak times
        ↓
Pulse intervals
        ↓
PR = 60 / pulse interval
        ↓
PR quality assessment
        ↓
Time-matched HR–PR comparison
        ↓
Context displayed to the user
```

A central design principle is that **downstream alarm logic depends on upstream parameter extraction**. If the ECG-to-HR pipeline does not represent the waveform correctly, a later threshold or contextual algorithm may never receive the correct evidence.

---

# 3. Phase 2 — Signal-Processing Foundation

## 3.1 Why Phase 2 exists

Alarm logic cannot operate directly on the idea of “the patient is bradycardic” or “the patient is tachycardic.” The simulator first needs numerical parameters derived from physiological waveforms.

For this project:

- ECG is used to derive **heart rate (HR)**.
- PLETH is used to derive **pulse rate (PR)**.
- HR and PR sequences are subjected to simple plausibility/stability checks.

These are intentionally simplified educational pipelines, not clinically validated measurement algorithms.

---

## 3.2 ECG to heart rate

The ECG module contains three conceptual steps.

### Step 1 — Detect QRS complexes

`detect_qrs(ecg_signal, fs)`:

1. Converts the input into a one-dimensional NumPy array.
2. Rejects an empty or multidimensional signal.
3. Rejects a non-positive sampling frequency.
4. Calls `wfdb.processing.xqrs_detect`.
5. Returns the detected QRS sample indices.

A QRS complex is used here as the event representing ventricular depolarization from which beat timing is estimated.

### Step 2 — Calculate beat-to-beat HR

`calculate_heart_rate(qrs_indices, fs)` converts QRS sample positions into seconds:

```text
QRS time = QRS sample index / sampling frequency
```

It then calculates consecutive RR intervals:

```text
RR interval = current QRS time - previous QRS time
```

Positive intervals are converted to beat-to-beat HR:

```text
HR (bpm) = 60 / RR interval (seconds)
```

For example:

```text
RR interval = 1.0 s → HR = 60 bpm
RR interval = 0.5 s → HR = 120 bpm
```

If fewer than two QRS detections are available, an RR interval cannot be calculated, so the function returns empty RR and HR arrays.

### Step 3 — Package the complete pipeline

`extract_heart_rate(ecg_signal, fs)` combines detection and calculation and returns:

- `qrs_indices`
- `qrs_times`
- `rr_intervals`
- `heart_rates`
- `heart_rate_times`

The HR timestamp is associated with `qrs_times[1:]`, because each HR estimate requires two QRS detections and becomes available at the second beat.

This timing detail matters later when selecting the evaluation window and calculating persistence delay.

---

## 3.3 PLETH to pulse rate

The PLETH pipeline follows a parallel structure.

### Step 1 — Detect pulse peaks

`detect_pleth_peaks()` uses `scipy.signal.find_peaks`.

The simplified defaults are:

- minimum peak distance: `0.3` seconds
- prominence: `0.03`

The minimum time is converted to samples using:

```text
minimum distance in samples = minimum distance in seconds × sampling frequency
```

The function validates:

- one-dimensional input
- non-empty signal
- positive sampling frequency
- positive minimum peak distance
- positive prominence

### Step 2 — Calculate pulse rate

`calculate_pulse_rate(peak_indices, fs)` calculates:

```text
Peak times → pulse intervals → PR
```

with:

```text
PR (bpm) = 60 / pulse interval (seconds)
```

As with HR, fewer than two peaks cannot produce an interval or rate.

### Step 3 — Package the pipeline

`extract_pulse_rate()` returns:

- `peak_indices`
- `peak_times`
- `pulse_intervals`
- `pulse_rates`
- `pulse_rate_times`

The pulse-rate timestamp is associated with `peak_times[1:]`.

---

## 3.4 Simple rate-quality assessment

`assess_rate_quality()` does not inspect raw waveform morphology. It evaluates the **derived rate sequence**.

The default educational checks are:

- empty sequence
- non-finite values such as `NaN`
- values outside `20–220 bpm`
- a change greater than `50 bpm` between consecutive finite estimates

The output includes:

```text
empty
non_finite
out_of_range
sudden_jump
caution
```

The `caution` flag becomes true if a non-finite value, out-of-range value, or sudden jump is detected. An empty rate sequence also returns `caution=True`.

### Critical interpretation

A quality caution means:

> “The derived parameter sequence contains behavior that may reduce confidence in the measurement.”

It does **not** mean:

> “The alarm is false.”

It also does not constitute a clinically validated signal-quality index.

That distinction becomes important in System B and in the dashboard explanations.

---

# 4. Phase 3 — System A: Baseline Threshold Logic

## 4.1 Purpose

System A provides a simple baseline for comparison.

It asks essentially:

> Did the ECG-derived HR cross the target threshold at least once?

It deliberately does **not** use:

- persistence
- signal-quality context
- PLETH
- HR–PR consistency

This creates a transparent reference system against which the contextual logic can be compared.

---

## 4.2 Heart-rate classification

`classify_heart_rate()` uses:

```text
HR < 40 bpm  → BRADYCARDIA
HR > 140 bpm → TACHYCARDIA
otherwise    → NORMAL
```

The boundaries are strict.

Therefore:

```text
40 bpm  → NORMAL
140 bpm → NORMAL
```

The function rejects:

- non-finite HR values
- invalid threshold configurations where the bradycardia threshold is greater than or equal to the tachycardia threshold

These thresholds are simplified project settings and should not be interpreted as universal clinical alarm limits.

---

## 4.3 Evaluating a sequence

`evaluate_baseline()` classifies every HR estimate independently.

Each result contains:

```text
index
heart_rate
classification
alarm
```

where `alarm` is true whenever the classification is not `NORMAL`.

For each record, the dataset alarm type determines the **target classification**:

```text
Bradycardia record  → target = BRADYCARDIA
Tachycardia record  → target = TACHYCARDIA
```

The project then counts how many HR estimates match the target classification.

System A's record-level decision is:

```text
target threshold crossings > 0 → ALARM
target threshold crossings = 0 → NO_ALARM
```

This is intentionally simple.

---

# 5. The Evaluation Window

The project evaluates derived HR and PR estimates in:

```text
290.0 to 300.0 seconds
```

Only parameter estimates whose timestamps fall inside this interval are used by the simplified alarm evaluation.

This is important because the simulator is evaluating a selected pre-alarm time window rather than claiming to reproduce a commercial monitor's complete proprietary alarm algorithm.

The same windowing concept is used for both HR and PR.

---

# 6. Phase 3 — Persistence

## 6.1 Why persistence was added

A single threshold crossing and a sustained abnormal condition are not necessarily the same event.

The project therefore adds a persistence rule:

```text
required consecutive target classifications = 3
```

`check_persistence()` scans the classification sequence and tracks:

- the current consecutive target count
- the maximum consecutive target count
- whether the required consecutive count was reached

Example:

```text
NORMAL
BRADYCARDIA
BRADYCARDIA
BRADYCARDIA
NORMAL
```

With a requirement of three consecutive target classifications:

```text
persistent = True
max_consecutive = 3
```

But:

```text
BRADYCARDIA
BRADYCARDIA
NORMAL
BRADYCARDIA
BRADYCARDIA
```

produces:

```text
persistent = False
max_consecutive = 2
```

The normal classification interrupts the run.

---

## 6.2 Persistence delay

`calculate_persistence_delay()` adds a time-based measurement.

It identifies:

1. the first target threshold-crossing time
2. the time at which the required consecutive sequence is first completed
3. the difference between those times

Conceptually:

```text
persistence delay =
persistence confirmation time - first threshold time
```

For example:

```text
NORMAL       at 290 s
TACHYCARDIA  at 291 s
TACHYCARDIA  at 292 s
TACHYCARDIA  at 293 s
```

gives:

```text
first threshold time = 291 s
persistence confirmation time = 293 s
persistence delay = 2 s
```

If threshold evidence occurs but persistence is never reached, the first threshold time can exist while confirmation time and delay remain `None`.

If no target threshold crossing occurs, all three values are `None`.

### Why this measurement matters

Persistence can reduce sensitivity to isolated threshold events, but it can also introduce a confirmation interval. The project therefore measures the delay rather than treating persistence as a free improvement.

---

# 7. HR–PR Cross-Parameter Context

`check_hr_pr_consistency()` compares ECG-derived HR with PLETH-derived PR.

The simplified matching procedure:

1. For each HR estimate, find the nearest PR estimate in time.
2. Accept it as a pair only if the time difference is within the configured tolerance.
3. Calculate the absolute rate difference.
4. Mark the pair consistent if the difference is within the configured rate tolerance.

The output includes:

- matched pairs
- consistent pairs
- inconsistent pairs
- consistency fraction
- detailed matches

Conceptually:

```text
consistency fraction =
consistent matched pairs / all matched pairs
```

If no valid pairs exist, the fraction is `None`.

### Important design decision

HR–PR disagreement is **contextual information**, not a hard suppression rule in the final System B logic.

The project's tests explicitly preserve the behavior that persistent, acceptable-quality ECG threshold evidence can still produce `ALARM` even when:

- HR–PR consistency is low, or
- no HR–PR matches are available.

This prevents the simulator from making the unsupported assumption:

> HR and PR disagree, therefore the ECG alarm is false.

---

# 8. Phase 3 — System B: Context-Aware Simulator

System B uses three outcomes:

```text
ALARM
REVIEW
NO_ALARM
```

Its role is not to diagnose the patient. It is an educational comparison showing how contextual checks can change the handling of threshold evidence.

The logic can be summarized as:

```text
No target threshold evidence
        ↓
NO_ALARM

Target threshold evidence
        ↓
Persistence reached + acceptable ECG-derived HR quality
        ↓
ALARM

Target threshold evidence but contextual uncertainty
        ↓
REVIEW
```

The decision reasons used by the implementation include:

- `NO_TARGET_THRESHOLD_CROSSING`
- `PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_HR_QUALITY`
- `NON_PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_QUALITY`
- `THRESHOLD_EVIDENCE_WITH_QUALITY_CAUTION`

### Interpretation of REVIEW

`REVIEW` means that threshold evidence was found, but the simplified contextual conditions for an immediate `ALARM` decision were not satisfied.

It does **not** mean:

- the original alarm was false
- the event was clinically unimportant
- the alarm can safely be suppressed
- no clinician response is required

It is a simulator state designed to expose uncertainty and encourage investigation.

---

# 9. Dataset Evaluation Pipeline

The final dataset-evaluation script provides the bridge between the individual modules and the project-level results.

For each candidate record, `evaluate_record(record_name)` performs:

```text
Load WFDB record
        ↓
Read alarm type and retrospective reference label
        ↓
Keep Bradycardia/Tachycardia cases
        ↓
Require ECG Lead II and PLETH
        ↓
ECG → HR
        ↓
Select 290–300 s HR window
        ↓
Baseline classifications
        ↓
Count target threshold crossings
        ↓
Generate System A decision
        ↓
Calculate persistence
        ↓
Calculate persistence delay
        ↓
Assess HR quality
        ↓
PLETH → PR
        ↓
Select 290–300 s PR window
        ↓
Assess PR quality
        ↓
Calculate HR–PR consistency
        ↓
Generate System B decision
        ↓
Return structured record result
```

The returned result includes:

- record name
- alarm type
- reference label
- number of HR estimates
- number of PR estimates
- threshold crossings
- maximum consecutive target estimates
- persistence status
- first threshold time
- persistence confirmation time
- persistence delay
- HR quality caution
- PR quality caution
- matched HR–PR pairs
- consistency fraction
- System A decision
- System B decision
- System B reason

The script downloads the Challenge 2015 training `RECORDS` list, selects record names beginning with `b` or `t`, evaluates supported records, tracks skipped and failed cases, and writes successful evaluations to:

```text
dataset_evaluation_results.csv
```

Records can be skipped when they are unsupported by the selected simplified pipeline, including missing required signals.

---

# 10. Dataset Results

The completed evaluation reported:

```text
Evaluated records: 183
Skipped records:   46
Failed records:     0
```

Reference-label distribution among the 183 evaluated records:

```text
True alarm:  140
False alarm:  43
```

## System A

```text
ALARM:     153
NO_ALARM:   30
```

System A versus reference label:

```text
False alarm reference: 19 ALARM, 24 NO_ALARM
True alarm reference: 134 ALARM, 6 NO_ALARM
```

## System B

```text
ALARM:      49
REVIEW:    104
NO_ALARM:   30
```

System B versus reference label:

```text
False alarm reference: 0 ALARM, 19 REVIEW, 24 NO_ALARM
True alarm reference: 49 ALARM, 85 REVIEW, 6 NO_ALARM
```

Therefore, compared with System A:

```text
153 immediate ALARM decisions → 49 immediate ALARM decisions
104 decisions redirected from immediate ALARM
67.97% reduction in immediate ALARM decisions
```

### Critical limitation

This must **not** be described as:

> “67.97% false-alarm reduction.”

It is a **67.97% reduction in immediate ALARM decisions under the simulator's logic**.

Of the 104 REVIEW cases:

```text
85 had true-alarm reference labels
19 had false-alarm reference labels
```

Therefore, the result demonstrates a tradeoff. It does not demonstrate improved clinical safety.

---

# 11. Results by Alarm Type

## Bradycardia

```text
Total: 76
True alarm references: 38
False alarm references: 38
```

System A:

```text
False alarm reference: 16 ALARM, 22 NO_ALARM
True alarm reference: 36 ALARM, 2 NO_ALARM
```

System B:

```text
False alarm reference: 0 ALARM, 16 REVIEW, 22 NO_ALARM
True alarm reference: 18 ALARM, 18 REVIEW, 2 NO_ALARM
```

## Tachycardia

```text
Total: 107
True alarm references: 102
False alarm references: 5
```

System A:

```text
False alarm reference: 3 ALARM, 2 NO_ALARM
True alarm reference: 98 ALARM, 4 NO_ALARM
```

System B:

```text
False alarm reference: 0 ALARM, 3 REVIEW, 2 NO_ALARM
True alarm reference: 31 ALARM, 67 REVIEW, 4 NO_ALARM
```

These distributions show why the three-way System B outcome should not be reduced to a conventional binary “correct/incorrect” interpretation without defining how REVIEW is handled.

---

# 12. Persistence-Delay Results

Persistence was reached in:

```text
123 records
```

Overall delay:

```text
Mean:   2.388 s
Median: 1.620 s
Min:    0.544 s
Max:    8.344 s
```

By alarm type:

```text
Bradycardia:
count = 26
mean = 4.335 s
median = 3.508 s
min = 3.020 s
max = 8.344 s

Tachycardia:
count = 97
mean = 1.866 s
median = 0.812 s
min = 0.544 s
max = 7.916 s
```

These values are properties of the selected records, the beat-to-beat parameter timing, and this simplified persistence implementation.

They are **not clinically validated acceptable alarm delays**.

---

# 13. Error-Case Investigation

The project does not stop at aggregate counts. Representative records are inspected to understand *why* the simulator behaves as it does.

The inspection script prints:

- alarm type
- retrospective reference label
- available signals
- sampling frequency
- number of HR estimates
- target threshold crossings
- HR quality
- every HR estimate with its timestamp and classification

This helps distinguish:

```text
Alarm-logic behavior
```

from:

```text
Upstream parameter-extraction behavior
```

## Representative cases

### `b124s`

- Bradycardia
- true-alarm reference label
- 3 target threshold crossings
- maximum consecutive abnormal estimates: 2
- System A: ALARM
- System B: REVIEW

Learning point:

> Threshold crossing and confirmed persistence are not the same thing.

### `b184s`

- Bradycardia
- false-alarm reference label
- threshold evidence exists
- HR and PR quality cautions are present
- System A: ALARM
- System B: REVIEW

Learning point:

> Questionable derived parameters create uncertainty, but quality caution alone does not prove that the original alarm was false.

### `t106s`

- Tachycardia
- true-alarm reference label
- 18 target threshold crossings
- persistence reached
- maximum consecutive abnormal estimates: 10
- System A: ALARM
- System B: ALARM
- example persistence delay: approximately 4.884 s

Learning point:

> Persistence introduces a measurable interval between first threshold evidence and confirmation.

### `t469l`

- Tachycardia
- false-alarm reference label
- no target threshold crossing in the selected evaluation window
- System A: NO_ALARM
- System B: NO_ALARM

Learning point:

> The retrospective dataset label and simulator output answer different questions. The reference label is not an input to either simulated system.

### `b187l`

- Bradycardia
- true-alarm reference label
- no target bradycardia threshold crossing detected by the simplified HR pipeline
- extracted HR behavior does not represent the expected target alarm condition
- System A: NO_ALARM
- System B: NO_ALARM

Learning point:

> Downstream alarm-management logic cannot reliably act on a condition that was not correctly represented in the upstream derived parameter.

The project therefore visualizes raw ECG and extracted HR for this case to investigate the signal-processing pipeline rather than incorrectly attributing the result to contextual alarm logic.

---

# 14. Phase 4 — Streamlit Dashboard

## 14.1 Purpose

Phase 4 translates the engineering implementation into an educational workflow relevant to Clinical Application and Product Specialist roles.

The dashboard is not intended to imitate a commercial bedside monitor exactly.

Its purpose is to help a learner move through:

```text
Waveform
→ derived parameter
→ threshold behavior
→ contextual evidence
→ simulated decision
→ troubleshooting interpretation
```

---

## 14.2 Record selection

The sidebar provides representative cases:

```text
b124s
b184s
t106s
t469l
b187l
```

These cases were selected because they demonstrate different behaviors rather than because they represent a statistically complete validation set.

---

## 14.3 Waveform display

The dashboard loads the selected WFDB record and displays available physiological waveforms, including ECG and PLETH.

The waveform view provides the visual context needed to ask:

> Does the derived parameter appear consistent with the underlying signal?

This is especially important for cases such as `b187l`.

---

## 14.4 Derived parameters

The dashboard runs the same project functions used by the backend analysis:

```text
ECG → extract_heart_rate()
PLETH → extract_pulse_rate()
```

It then displays HR and PR behavior in the evaluation window.

This keeps the dashboard as a **presentation layer over the simulator logic** rather than creating a separate decision engine.

---

## 14.5 System comparison

The dashboard places the two systems side by side conceptually.

### System A — Baseline

```text
HR parameter → threshold → decision
```

It shows:

- target threshold crossings
- `ALARM` or `NO_ALARM`

### System B — Context-Aware

```text
threshold evidence
+ persistence
+ signal-derived quality context
→ decision
```

It shows:

- `ALARM`, `REVIEW`, or `NO_ALARM`
- persistence reached
- maximum consecutive abnormal estimates
- HR quality caution
- PR quality caution

The dashboard also displays HR–PR matched-pair and consistency information as cross-parameter context.

---

# 15. Decision Explanations

The dashboard translates internal reason codes into understandable language.

Examples:

### `PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_HR_QUALITY`

The dashboard explains that threshold evidence persisted for the configured number of consecutive estimates and the ECG-derived HR quality check did not raise a caution.

### `NON_PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_QUALITY`

The dashboard explains that the target threshold was crossed but persistence was not confirmed.

### `THRESHOLD_EVIDENCE_WITH_QUALITY_CAUTION`

The dashboard explains that threshold evidence exists but one or more signal-derived quality checks raised uncertainty.

### `NO_TARGET_THRESHOLD_CROSSING`

The dashboard explains that the simplified derived HR parameter did not cross the target threshold in the evaluation window.

For a no-crossing case, the wording must avoid implying that the patient or waveform is clinically normal.

---

# 16. Clinical Workflow Interpretation

The dashboard adds an educational review sequence:

1. **Verify the waveform** — inspect ECG signal integrity, artifact, baseline disturbance, or unusual morphology.
2. **Verify the derived parameter** — determine whether displayed HR behavior appears consistent with the waveform.
3. **Review threshold evidence** — identify whether the target threshold was crossed and whether the condition persisted.
4. **Compare available parameters** — review ECG-derived HR and PLETH-derived PR when available.
5. **Review signal-quality context** — consider parameter instability or implausible values.
6. **Interpret the simulator decision** — compare System A and System B and understand why they differ.

This is an educational troubleshooting framework.

It is **not** a validated clinical protocol and does not replace institutional alarm-management policies.

---

# 17. Interactive Case Walkthrough

The dashboard uses representative cases as teaching scenarios.

For each case it presents:

```text
Case Summary
What System A Sees
What System B Sees
What to Investigate
Key Learning Point
```

The System A and System B explanations are generated from the actual simulator results where possible, rather than simply repeating the retrospective reference label.

The reference label is displayed only for retrospective educational comparison.

It is not provided to either simulated alarm system when making a decision.

---

# 18. Testing Strategy

The project reached:

```text
50 passing pytest tests
```

The tests cover several layers.

## Baseline logic

Tests verify:

- bradycardia classification
- tachycardia classification
- normal classification
- exact threshold boundaries
- invalid `NaN`
- invalid threshold ordering
- sequence evaluation
- empty sequence handling
- invalid dimensions

## ECG calculations

Tests verify:

```text
1.0 s RR interval → 60 bpm
0.5 s RR interval → 120 bpm
```

They also verify:

- fewer than two QRS detections
- invalid sampling frequency

## PLETH calculations

Equivalent tests verify:

```text
1.0 s pulse interval → 60 bpm
0.5 s pulse interval → 120 bpm
```

plus insufficient peaks and invalid sampling frequency.

## Rate-quality logic

Tests verify:

- stable sequence
- sudden jump
- out-of-range rate
- non-finite rate
- empty sequence
- invalid rate bounds
- invalid maximum jump

## Context-aware logic

Tests verify:

- persistent and non-persistent sequences
- interrupted abnormal runs
- no target classification
- persistence-delay calculation
- no persistence confirmation
- no threshold crossing
- HR–PR consistency
- mixed consistency
- no nearby time match
- empty PR data
- length mismatch
- invalid matching parameters
- System B decision branches
- invalid threshold-crossing counts

A particularly important design behavior is explicitly tested:

> HR–PR disagreement alone should not override persistent, acceptable-quality ECG threshold evidence.

The same applies when no HR–PR matched pairs are available.

---

# 19. File-by-File Mental Model

A new reader can understand the codebase using this map.

```text
src/
│
├── signal_processing/
│   ├── ecg.py
│   │   ECG → QRS → RR → HR
│   │
│   ├── pleth.py
│   │   PLETH → peaks → intervals → PR
│   │
│   └── signal_quality.py
│       Simple quality checks on derived HR/PR sequences
│
├── alarm_systems/
│   ├── baseline.py
│   │   System A threshold classification
│   │
│   └── context_aware.py
│       Persistence
│       Persistence delay
│       HR–PR matching
│       System B decision logic
│
├── run_baseline_example.py
│   Early representative-record System A exploration
│
├── run_context_analysis.py
│   Representative-record System A vs System B analysis
│
├── run_dataset_evaluation.py
│   Runs the complete pipeline across eligible dataset records
│   and creates dataset_evaluation_results.csv
│
├── analyze_dataset_results.py
│   Aggregates System A/System B outcomes, REVIEW context,
│   persistence delay, and decision-reduction results
│
├── inspect_error_cases.py
│   Prints detailed HR sequences for representative cases
│
└── plot_error_case.py
    Visual investigation of waveform vs extracted parameter

dashboard/
└── app.py
    Streamlit educational workflow and case walkthrough

tests/
├── test_baseline.py
├── test_context_aware.py
├── test_ecg.py
├── test_pleth.py
└── test_signal_quality.py
```

---

# 20. Key Engineering Design Decisions

## Decision 1 — Keep System A deliberately simple

System A provides a clear baseline.

Adding context to System A would make it harder to understand what System B changes.

## Decision 2 — Use beat-to-beat derived rates

The project exposes the relationship between detected events, intervals, and rates directly.

This also makes timing and persistence effects visible.

## Decision 3 — Add a three-way System B outcome

`REVIEW` prevents every uncertain case from being forced into `ALARM` or `NO_ALARM`.

It is an educational uncertainty state, not a clinical disposition.

## Decision 4 — Measure persistence delay

Persistence may change alarm behavior, but it can also delay confirmation.

The project therefore quantifies this tradeoff.

## Decision 5 — Do not use HR–PR disagreement as automatic suppression

Cross-parameter disagreement can have multiple causes.

The final implementation treats it as context instead of proof that one parameter or alarm is wrong.

## Decision 6 — Investigate upstream failures separately

Cases such as `b187l` demonstrate that a downstream alarm algorithm cannot solve every upstream measurement problem.

This creates an important troubleshooting hierarchy:

```text
First ask whether the signal is represented correctly.
Then ask whether the derived parameter is credible.
Then interpret threshold and contextual alarm logic.
```

## Decision 7 — Keep the reference label outside the decision path

The dataset reference label is used for retrospective evaluation only.

Neither System A nor System B receives the label as an input.

This avoids circular logic.

---

# 21. What the Project Demonstrates

The project demonstrates the ability to:

- work with retrospective physiological waveform data
- extract beat-to-beat physiological parameters
- build modular signal-processing functions
- implement and test threshold logic
- add persistence and simple quality context
- compare ECG-derived HR with PLETH-derived PR
- evaluate algorithms across a dataset
- inspect aggregate results critically
- investigate representative failure cases
- distinguish upstream signal-processing limitations from downstream decision logic
- build an educational Streamlit interface
- translate technical outputs into workflow-oriented explanations

For Clinical Application/Product Specialist positioning, the strongest story is:

> “I built a simplified end-to-end patient-monitoring simulation to understand how waveform acquisition, parameter extraction, threshold logic, persistence, signal-quality context, and cross-parameter comparison can influence alarm behavior. I then built a dashboard that translates those engineering concepts into a structured troubleshooting workflow.”

---

# 22. What the Project Does NOT Prove

This section is essential.

The project does **not** prove that:

- System B is safer than System A.
- System B is clinically superior.
- 67.97% of false alarms can be eliminated.
- REVIEW cases can safely be suppressed.
- REVIEW means false alarm.
- NO_ALARM means the patient is clinically normal.
- HR–PR disagreement proves an alarm is false.
- The selected quality checks are clinically validated SQIs.
- Three consecutive estimates are an optimal persistence rule.
- The measured persistence delays are clinically acceptable.
- The thresholds of 40 and 140 bpm are universally appropriate.
- The simplified PLETH detector is suitable for clinical monitoring.
- The ECG QRS/HR pipeline reproduces a commercial monitor.
- The 183 evaluated records represent all alarm types or all patient populations.
- The dashboard is a medical device.

The results are properties of:

- the selected retrospective records
- the selected evaluation window
- the selected signal-processing methods
- the simplified thresholds
- the persistence rule
- the simplified quality logic
- the implemented System B decision policy

---

# 23. Known Limitations

Important limitations include:

1. Only Bradycardia and Tachycardia are evaluated by the main simplified dataset pipeline.
2. The evaluation requires ECG Lead II and PLETH, causing unsupported records to be skipped.
3. The evaluation uses a fixed 290–300 second window.
4. HR depends on XQRS detection performance.
5. PR uses a simple `find_peaks` configuration.
6. Rate-quality checks operate on derived rates rather than validated raw-signal SQIs.
7. Thresholds are simplified project settings.
8. Persistence is defined as three consecutive target classifications.
9. Beat-to-beat estimate timing means persistence delay depends partly on heart rate and detection timing.
10. HR–PR matching is simplified.
11. The three-way System B output complicates direct binary performance comparison.
12. The retrospective reference label is not equivalent to a full clinical interpretation of each waveform.
13. Representative case analysis demonstrates limitations that aggregate counts alone can hide.

---

# 24. How to Explain the Project in an Interview

## 30-second version

> I built an educational Clinical Alarm Management Simulator using retrospective physiological waveform data. I created an ECG-to-heart-rate pipeline and a PLETH-to-pulse-rate pipeline, then compared a simple threshold-based alarm system with a contextual system that considers persistence and parameter-quality checks. I evaluated the systems across 183 eligible Bradycardia and Tachycardia records, investigated representative error cases, and built a Streamlit dashboard that explains the results as a clinical troubleshooting workflow. The project is educational and not clinically validated.

## 90-second technical version

> The project starts with ECG and PLETH waveforms. For ECG, I use WFDB XQRS detection, calculate RR intervals, and convert them to beat-to-beat heart rate. For PLETH, I use simplified peak detection and calculate pulse rate. I then apply simple rate-quality checks for non-finite values, implausible ranges, and sudden jumps.
>
> System A is deliberately simple: if the ECG-derived heart rate crosses the target Bradycardia or Tachycardia threshold in the evaluation window, it generates an ALARM. System B adds persistence and quality context and can output ALARM, REVIEW, or NO_ALARM. I also calculate HR–PR agreement, but I deliberately do not use disagreement as an automatic suppression rule.
>
> Across 183 evaluated records, System A produced 153 immediate ALARM decisions, while System B produced 49 ALARM, 104 REVIEW, and 30 NO_ALARM decisions. I describe that as a 67.97% reduction in immediate ALARM decisions—not false-alarm reduction—because 85 of the REVIEW cases had true-alarm reference labels. I also measured persistence delay and investigated cases where upstream HR extraction limited downstream alarm detection.
>
> Finally, I built a Streamlit dashboard that lets a user inspect the waveform, derived parameters, System A and B decisions, and a structured troubleshooting interpretation.

---

# 25. Clinical Application Specialist Perspective

A useful way to frame the project is not:

> “I created a better alarm algorithm.”

A more defensible framing is:

> “I created an educational simulator to study how the monitoring chain influences alarm behavior and to practice explaining that chain in a troubleshooting workflow.”

The troubleshooting chain is:

```text
Patient / physiological source
        ↓
Electrode or sensor
        ↓
Raw waveform
        ↓
Signal detection
        ↓
Derived parameter
        ↓
Threshold evidence
        ↓
Persistence / contextual logic
        ↓
Alarm decision
        ↓
User interpretation and response
```

When a user reports an unexpected alarm, the project encourages asking:

1. What does the waveform show?
2. Is the signal technically usable?
3. Does the derived parameter make sense relative to the waveform?
4. Did the parameter actually cross the configured threshold?
5. Was the condition isolated or persistent?
6. What does another available parameter show?
7. Is disagreement evidence of uncertainty rather than proof?
8. Is the issue likely upstream measurement, parameter extraction, configuration, alarm logic, or something requiring escalation?

This is the bridge between the project's engineering work and the workflow reasoning expected in Clinical Applications and Product Support roles.

---

# 26. Phase 2 → Phase 3 → Phase 4 Summary

## Phase 2

Built the measurement foundation:

```text
ECG → QRS → RR → HR
PLETH → peaks → intervals → PR
HR/PR → simple quality flags
```

## Phase 3

Built and evaluated alarm logic:

```text
System A:
HR → threshold crossing → ALARM / NO_ALARM

System B:
threshold evidence
+ persistence
+ quality context
→ ALARM / REVIEW / NO_ALARM
```

Added:

- persistence delay
- HR–PR contextual comparison
- dataset evaluation
- aggregate analysis
- representative error-case investigation
- automated tests

## Phase 4

Translated the engineering into an educational workflow:

```text
Select case
→ inspect ECG/PLETH
→ inspect HR/PR
→ compare System A and B
→ understand decision reason
→ follow troubleshooting workflow
→ study case-specific learning point
```

The dashboard was then frozen after auditing five representative cases.

---

# 27. Final Takeaway

The most important lesson from the project is that alarm behavior should be understood as part of a **measurement and decision pipeline**.

A threshold alarm does not begin at the threshold.

It begins upstream:

```text
waveform quality
→ event detection
→ parameter calculation
→ parameter credibility
→ threshold crossing
→ persistence
→ contextual evidence
→ alarm decision
```

The simulator demonstrates why troubleshooting should follow that chain.

It also demonstrates why algorithm results must be communicated carefully. Redirecting immediate alarms to REVIEW is not automatically equivalent to eliminating false alarms, and adding persistence can introduce measurable delay.

That combination—engineering implementation, critical evaluation, limitation awareness, and workflow explanation—is the central portfolio value of Phases 2 through 4.
