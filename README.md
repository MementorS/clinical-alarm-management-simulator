 ## Clinical Alarm Management Simulator

An educational biomedical engineering project demonstrating ECG signal processing,
heart-rate extraction, contextual alarm management, and clinical alarm
troubleshooting using the PhysioNet/Computing in Cardiology Challenge 2015 dataset.

Built as a portfolio project for Clinical Application Specialist,
Clinical Product Specialist, and Biomedical Engineering roles.


 ## Project Overview

Patient monitoring systems generate alarms to notify clinicians when a measured
physiological parameter exceeds predefined limits. While threshold-based alarm
systems are straightforward to implement, they may also generate alarms that
require additional investigation because of transient events, signal quality
issues, or differences between physiological parameters.

This project explores how a simplified threshold-based alarm system can be
extended with contextual information such as persistence, signal-quality
assessment, and comparison between ECG-derived heart rate (HR) and
PLETH-derived pulse rate (PR).

The project was inspired by the PhysioNet/Computing in Cardiology Challenge 2015
and was developed as an educational simulator rather than a reproduction of the
official challenge algorithm or a clinical decision-support system.

In addition to implementing the signal-processing and alarm-decision pipeline,
the project includes an interactive Streamlit dashboard, troubleshooting case
studies, automated testing, and technical documentation to demonstrate the
workflow from physiological signal acquisition to alarm interpretation.


## Why I Built This Project

As I prepared for roles in Clinical Application Specialist, Clinical Product
Specialist, and Biomedical Engineering, I wanted to better understand how
patient-monitoring systems transform physiological signals into clinically
meaningful parameters and ultimately into alarm decisions.

Rather than focusing only on programming, I wanted to explore the complete
engineering workflow:

- physiological signal acquisition
- parameter extraction
- alarm generation
- contextual alarm evaluation
- troubleshooting
- clinical workflow interpretation

Developing this simulator helped me connect biomedical signal processing with
real-world monitoring workflows and strengthened my understanding of how
technical and clinical perspectives intersect during alarm investigation.


## Features

### Biomedical Signal Processing

- ECG signal processing using the WFDB library
- QRS complex detection from ECG waveforms
- RR interval calculation
- Heart-rate (HR) estimation from detected QRS complexes
- PLETH waveform processing
- Pulse-rate (PR) estimation from pulse intervals

---

### Baseline Alarm System (System A)

Implements a simplified threshold-based alarm workflow.

Features include:

- Heart-rate threshold classification
- Bradycardia detection
- Tachycardia detection
- Per-sample alarm evaluation
- Threshold-based ALARM / NO_ALARM decisions

This system demonstrates how conventional parameter-threshold alarms can be
implemented using derived physiological parameters.

---

### Context-Aware Alarm System (System B)

Extends the baseline alarm workflow by incorporating additional contextual
information before producing an alarm recommendation.

Implemented components include:

- Threshold-crossing analysis
- Persistence evaluation
- Persistence-delay calculation
- Heart-rate quality assessment
- Pulse-rate quality assessment
- HR–PR comparison
- Context-aware decision generation

Possible outputs include:

- ALARM
- REVIEW
- NO_ALARM

The REVIEW state indicates that additional context should be considered before
an immediate alarm decision. It is not equivalent to classifying an alarm as
false.

---

### Dataset Evaluation

The simulator evaluates representative Bradycardia and Tachycardia records from
the PhysioNet/Computing in Cardiology Challenge 2015 dataset.

The evaluation pipeline:

1. Extracts ECG-derived HR
2. Extracts PLETH-derived PR (when available)
3. Applies System A
4. Applies System B
5. Produces summary statistics
6. Stores results for later analysis

---

### Interactive Dashboard

The Streamlit dashboard provides an educational visualization of the complete
alarm-management workflow.

Features include:

- ECG waveform visualization
- PLETH waveform visualization
- HR trend display
- System A decision
- System B decision
- Decision explanation
- Clinical workflow interpretation
- Interactive representative cases

---

### Testing

Automated unit tests validate:

- ECG processing
- PLETH processing
- Heart-rate extraction
- Pulse-rate extraction
- Signal-quality assessment
- Baseline alarm logic
- Context-aware alarm logic
- Dataset evaluation support functions



                           ECG
                            │
                    QRS Detection
                            │
                      RR Intervals
                            │
                      Heart Rate (HR)
                            │
                    Threshold Detection
                            │
                 ┌──────────┴──────────┐
                 │                     │
             System A             System B
                 │                     │
          ALARM / NO_ALARM      Persistence
                                      │
                               Signal Quality
                                      │
                     ┌────────────────┴──────────────┐
                     │                               │
                  PLETH                         Pulse Rate
                     │                               │
                     └──────── HR–PR Comparison ─────┘
                                      │
                               Context Decision
                                      │
                          ALARM / REVIEW / NO_ALARM
                                      │
                           Streamlit Dashboard



                           ## System Workflow

The simulator follows the same high-level sequence used by many patient-monitoring systems:

1. Physiological signals are acquired.
2. ECG and PLETH signals are processed independently.
3. HR and PR are derived from their respective signals.
4. A baseline threshold-based alarm decision is produced (System A).
5. Contextual information such as persistence, signal quality, and HR–PR comparison is evaluated (System B).
6. Results are presented through an interactive dashboard for educational interpretation.

The project emphasizes understanding the engineering pathway from physiological signal acquisition to alarm interpretation rather than reproducing a commercial patient-monitor algorithm.



## Repository Structure

clinical-alarm-management-simulator/
│
├── dashboard/
│   └── app.py(Streamlit application for interactive visualization)
│
├── docs/
│   ├── images
│   ├── PROJECT_TECHNICAL_WALKTHROUGH.md
│   ├── case_studies/
│
├── notebooks/
│   ├──01_dataset_exploration.ipnyb
│
├── src/
│   ├──alarm_systems
│           ├──baseline.py
│           ├──context_aware.py
│   ├──signal_processing
│            ├── ecg.py
│            ├── pleth.py
│            ├── signal_quality.py
│   ├── analyze_dataset_results.py
│   ├── environment_check.py
│   ├── inspect_error_cases.py
│   ├── plot_error_case.py 
│   ├── run_baseline_experiment.py
│   ├── run_context_analysis.py
│   ├── run_dataset_evaluation.py
│
├── tests/
│   ├──test_baseline.py
│   ├── test_context_aware.py
│   ├── test_ecg.py
│   ├── test_pleth.py
│   └── test_signal_quality.py
│
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore




## Dataset

This project uses representative Bradycardia and Tachycardia records from the
PhysioNet / Computing in Cardiology Challenge 2015 dataset.

The original challenge focused on reducing false arrhythmia alarms in intensive
care monitoring environments.

This simulator does **not** reproduce the official challenge algorithm.
Instead, the dataset is used as an educational resource for exploring:

- ECG signal processing
- Heart-rate extraction
- Pulse-rate extraction
- Threshold-based alarm generation
- Context-aware alarm evaluation
- Clinical troubleshooting workflows

Representative records were selected to demonstrate different alarm behaviors,
including true alarms, false alarms, transient events, and edge cases.


## Representative Case Studies

The dashboard includes representative clinical scenarios demonstrating different
alarm behaviors.

| Record | Educational Focus |
|---------|-------------------|
| **b124s** | Bradycardia with insufficient persistence |
| **b184s** | Bradycardia with signal-quality considerations |
| **t106s** | Persistent tachycardia |
| **t469l** | No threshold crossing during evaluation window |
| **b187l** | Upstream parameter-extraction limitation |

Each case explains:

- waveform observations
- parameter behavior
- System A decision
- System B decision
- engineering interpretation
- troubleshooting workflow


## Results

A representative evaluation was performed on 183 Bradycardia and Tachycardia
records.

### System A

| Decision | Count |
|----------|------:|
| ALARM | 153 |
| NO_ALARM | 30 |

### System B

| Decision | Count |
|----------|------:|
| ALARM | 49 |
| REVIEW | 104 |
| NO_ALARM | 30 |

Compared with the baseline threshold-only workflow, the context-aware system
redirected 104 immediate alarm decisions to **REVIEW**, representing a
67.97% reduction in immediate ALARM decisions.

The REVIEW decision indicates that additional contextual information should be
considered before producing an immediate alarm response. It should **not** be
interpreted as identifying a false alarm or replacing clinical judgment.

### Persistence Analysis

Records reaching persistence: 123

Median persistence delay:

- Overall: 1.620 seconds
- Bradycardia: 3.508 seconds
- Tachycardia: 0.812 seconds

These observations illustrate how persistence can distinguish transient
threshold crossings from sustained parameter abnormalities within the simulator.


## Interactive Dashboard

The Streamlit dashboard provides an educational visualization of the complete
alarm-management workflow.

The dashboard includes:

- ECG waveform visualization
- PLETH waveform visualization
- Heart-rate trend
- Pulse-rate trend
- System A decision
- System B decision
- Decision explanations
- Clinical workflow interpretation
- Interactive representative case walkthroughs

The dashboard is intended to demonstrate engineering concepts rather than serve
as a clinical decision-support application.



## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/clinical-alarm-management-simulator.git
cd clinical-alarm-management-simulator
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```


## Running the Project

### Run the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard allows users to:

- Explore representative ECG and PLETH waveforms
- Compare System A and System B decisions
- Review alarm explanations
- Follow the troubleshooting workflow
- Interact with representative case studies





## Testing

The project includes automated unit tests covering the major components of the simulator.

To run the test suite:

```bash
pytest
```

The tests validate:

- ECG signal-processing functions
- PLETH signal-processing functions
- Heart-rate extraction
- Pulse-rate extraction
- Signal-quality assessment
- Baseline alarm logic
- Context-aware alarm logic
- Dataset evaluation support functions

The objective of the test suite is to verify that individual components behave
consistently during development and future modifications.



## Limitations

This project was developed as an educational biomedical engineering simulator.

It has several important limitations:

- It does not reproduce the official PhysioNet Challenge 2015 algorithm.
- The alarm logic is intentionally simplified for educational purposes.
- Evaluation is retrospective using an existing dataset.
- The simulator is not clinically validated.
- It is not intended for diagnosis or patient management.
- Alarm decisions are illustrative and should not replace clinical judgment.
- Commercial patient monitors use additional proprietary signal-processing,
  quality assessment, and safety mechanisms that are beyond the scope of this
  project.



  ## Skills Demonstrated

### Biomedical Engineering

- ECG signal processing
- PLETH signal processing
- Physiological parameter extraction
- Clinical alarm workflow analysis
- Biomedical data interpretation

### Software Engineering

- Python
- NumPy
- SciPy
- WFDB
- Streamlit
- Pytest
- Modular software design
- Technical documentation

### Professional Skills

- Technical troubleshooting
- Clinical workflow analysis
- Data interpretation
- Scientific communication
- Documentation


## References

- PhysioNet / Computing in Cardiology Challenge 2015
- WFDB Python Library
- PhysioNet WaveForm Database tools

This project is an independent educational implementation inspired by publicly
available research resources.


## License

This project is released under the MIT License.

The PhysioNet dataset is subject to its own licensing and citation
requirements. Please refer to the original dataset documentation before using
the data independently.


