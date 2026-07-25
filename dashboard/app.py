from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import wfdb
from src.signal_processing.ecg import extract_heart_rate
from src.signal_processing.pleth import extract_pulse_rate
from src.alarm_systems.baseline import evaluate_baseline

from src.signal_processing.signal_quality import assess_rate_quality

from src.alarm_systems.context_aware import (
    check_persistence,
    calculate_persistence_delay,
    check_hr_pr_consistency,
    make_context_aware_decision,
)


def get_workflow_interpretation(decision_reason):

    interpretations = {
        "NO_TARGET_THRESHOLD_CROSSING": (
            "The derived heart-rate parameter did not cross the target "
            "alarm threshold during the evaluation window. In this "
            "simplified simulation, no alarm condition was identified. "
            "A clinical workflow would still require interpretation of "
            "the displayed waveform and patient context rather than "
            "relying on a single derived parameter alone."
        ),

        "PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_HR_QUALITY": (
            "The heart-rate parameter crossed the target alarm threshold "
            "and the abnormal condition persisted for the required number "
            "of consecutive estimates. The ECG-derived heart-rate quality "
            "check did not identify a caution condition. The contextual "
            "system therefore classifies this event as an immediate ALARM."
        ),

        "NON_PERSISTENT_THRESHOLD_WITH_ACCEPTABLE_QUALITY": (
            "The heart-rate parameter crossed the configured alarm "
            "threshold, but the abnormal condition was not sustained for "
            "the required number of consecutive estimates. Signal-quality "
            "checks did not identify a caution condition. The event is "
            "therefore routed to REVIEW in this educational simulation "
            "rather than classified as an immediate ALARM."
        ),

        "THRESHOLD_EVIDENCE_WITH_QUALITY_CAUTION": (
            "The heart-rate parameter crossed the target alarm threshold, "
            "but one or more signal-derived quality checks raised a caution. "
            "This creates uncertainty about the reliability of the derived "
            "parameter evidence. The event is therefore routed to REVIEW "
            "in this educational simulation."
        ),
    }

    return interpretations.get(
        decision_reason,
        (
            "The simulator identified a decision pathway that does not "
            "currently have a dedicated workflow interpretation."
        ),
    )

def get_case_walkthrough(record_name):

    walkthroughs = {
        "b124s": {
            "case_summary": (
                "This example represents a bradycardia record with a "
                "true-alarm dataset reference label."
            ),
            "what_system_a_sees": (
                "The ECG-derived heart-rate estimates cross the "
                "bradycardia threshold. Because System A uses simplified "
                "threshold-based logic, the presence of target threshold "
                "crossings produces an ALARM decision."
            ),
            "what_system_b_sees": (
                "System B evaluates the same threshold evidence together "
                "with persistence and signal-quality context. In this case, "
                "the abnormal estimates do not reach the required number "
                "of consecutive threshold crossings."
            ),
            "investigation": (
                "Compare the individual HR estimates with the ECG waveform, "
                "examine why the low-rate estimates are interrupted by "
                "normal estimates, and compare ECG-derived HR with "
                "PLETH-derived PR."
            ),
            "learning_point": (
                "A threshold crossing and a persistent threshold condition "
                "are not necessarily the same event. Contextual logic can "
                "therefore produce a different decision from simple "
                "threshold-based logic."
            ),
        },

        "b184s": {
            "case_summary": (
                "This example represents a bradycardia record with a "
                "false-alarm dataset reference label."
            ),
            "what_system_a_sees": (
                "The ECG-derived heart-rate parameter crosses the "
                "bradycardia threshold, causing the simplified baseline "
                "system to generate an ALARM decision."
            ),
            "what_system_b_sees": (
                "The contextual system identifies threshold evidence but "
                "also evaluates persistence and signal-quality information. "
                "The quality context introduces uncertainty, so the event "
                "is routed to REVIEW rather than immediate ALARM."
            ),
            "investigation": (
                "Inspect the ECG waveform and derived HR estimates for "
                "possible parameter-extraction instability. Compare the "
                "ECG-derived HR with the available PLETH waveform and "
                "PLETH-derived PR."
            ),
            "learning_point": (
                "When signal-derived parameters are questionable, a "
                "threshold violation alone may not provide sufficient "
                "context to interpret why an alarm condition occurred."
            ),
        },

        "t106s": {
            "case_summary": (
                "This example represents a tachycardia record with a "
                "true-alarm dataset reference label."
            ),
            "what_system_a_sees": (
                "Multiple ECG-derived heart-rate estimates cross the "
                "tachycardia threshold, producing an ALARM decision."
            ),
            "what_system_b_sees": (
                "The tachycardia threshold condition reaches the required "
                "persistence criterion and the ECG-derived HR quality check "
                "does not raise a caution. System B therefore also produces "
                "an ALARM decision."
            ),
            "investigation": (
                "Review the sequence of tachycardic HR estimates and observe "
                "how persistence develops over time. Compare the time of the "
                "first threshold crossing with the time at which persistence "
                "is confirmed."
            ),
            "learning_point": (
                "Persistence introduces a confirmation interval between "
                "initial threshold evidence and a contextual alarm decision."
            ),
        },

        "t469l": {
            "case_summary": (
                "This example represents a tachycardia record with a "
                "false-alarm dataset reference label."
            ),
            "what_system_a_sees": (
                "The simplified ECG-derived HR pipeline does not detect a "
                "target tachycardia threshold crossing during the evaluation "
                "window, so System A produces NO_ALARM."
            ),
            "what_system_b_sees": (
                "Because no target threshold evidence is present, the "
                "contextual system also produces NO_ALARM."
            ),
            "investigation": (
                "Review the waveform and derived HR trend to understand why "
                "the target threshold was not crossed during the selected "
                "evaluation window."
            ),
            "learning_point": (
                "Contextual alarm logic cannot compensate for every upstream "
                "signal-processing or parameter-extraction limitation. The "
                "quality of the input parameter remains important."
            ),
        },

        "b187l": {
            "case_summary": (
                "This example demonstrates an upstream heart-rate extraction "
                "limitation in the simplified simulator."
            ),
            "what_system_a_sees": (
                "The derived HR parameter does not produce the expected "
                "bradycardia threshold evidence during the evaluation window."
            ),
            "what_system_b_sees": (
                "Without target threshold evidence from the upstream HR "
                "pipeline, the contextual decision layer cannot identify "
                "the expected bradycardia condition."
            ),
            "investigation": (
                "Compare the raw ECG waveform with the extracted HR trend. "
                "Investigate whether QRS detection or beat-interval estimation "
                "is producing parameter values that do not accurately "
                "represent the waveform behavior."
            ),
            "learning_point": (
                "Alarm-management logic depends on upstream signal processing. "
                "A downstream contextual algorithm cannot reliably correct "
                "a condition that was not represented correctly in the "
                "derived parameter."
            ),
        },
    }

    return walkthroughs.get(record_name)


def get_dynamic_system_explanation(
    threshold_crossings,
    system_a_decision,
    persistence_result,
    hr_quality,
    pr_quality,
    system_b_result,
):

    system_a_text = (
        f"The ECG-derived heart-rate parameter produced "
        f"{threshold_crossings} target threshold crossing(s) "
        f"during the evaluation window. Under the simplified "
        f"threshold-based logic, System A therefore produced "
        f"a {system_a_decision} decision."
    )

    system_b_text = (
        f"System B evaluated the same threshold evidence together "
        f"with contextual checks. Persistence reached: "
        f"{persistence_result['persistent']}. "
        f"Maximum consecutive abnormal estimates: "
        f"{persistence_result['max_consecutive']}. "
        f"HR quality caution: {hr_quality['caution']}. "
        f"PR quality caution: {pr_quality['caution']}. "
        f"The resulting System B decision was "
        f"{system_b_result['decision']}."
    )

    return system_a_text, system_b_text


def get_case_learning_content(record_name):

    case_content = {
        "b124s": {
            "case_title": "Threshold Evidence Without Confirmed Persistence",
            "case_focus": (
                "This case demonstrates how isolated or interrupted "
                "bradycardia threshold crossings may produce different "
                "decisions under baseline and context-aware logic."
            ),
            "what_to_investigate": (
                "Review the ECG waveform and derived HR estimates. "
                "Identify where the bradycardia threshold is crossed and "
                "check whether the abnormal estimates occur consecutively."
            ),
            "learning_point": (
                "Threshold crossing and persistence represent different "
                "types of alarm evidence. A parameter may cross an alarm "
                "threshold without satisfying a persistence requirement."
            ),
        },

        "b184s": {
            "case_title": "Threshold Evidence With Signal-Quality Caution",
            "case_focus": (
                "This case demonstrates how threshold evidence can occur "
                "when the derived physiological parameters also show "
                "signal-quality caution indicators."
            ),
            "what_to_investigate": (
                "Inspect the ECG and PLETH waveforms, then compare the "
                "derived HR and PR estimates. Look for implausible values, "
                "instability, or disagreement that may reduce confidence "
                "in the parameter estimates."
            ),
            "learning_point": (
                "Alarm troubleshooting should include assessment of the "
                "source waveform and derived parameter quality rather than "
                "interpreting threshold crossings in isolation."
            ),
        },

        "t106s": {
            "case_title": "Persistent Tachycardia Threshold Evidence",
            "case_focus": (
                "This case demonstrates sustained tachycardia threshold "
                "evidence that reaches the simulator's persistence "
                "requirement."
            ),
            "what_to_investigate": (
                "Review the ECG-derived HR trend and identify the sequence "
                "of consecutive tachycardia classifications. Compare the "
                "time of the first threshold crossing with the time at "
                "which persistence is confirmed."
            ),
            "learning_point": (
                "Persistence logic introduces a temporal requirement into "
                "alarm evaluation. This can distinguish sustained threshold "
                "evidence from isolated abnormal parameter estimates."
            ),
        },

        "t469l": {
            "case_title": "No Target Threshold Crossing",
            "case_focus": (
                "This case demonstrates a record in which the simplified "
                "HR pipeline does not produce target tachycardia threshold "
                "evidence within the evaluation window."
            ),
            "what_to_investigate": (
                "Inspect the ECG waveform and derived HR estimates and "
                "confirm whether the tachycardia threshold is crossed. "
                "Compare this result with the retrospective dataset label."
            ),
            "learning_point": (
                "The dataset reference label and the simulator decision "
                "serve different purposes. The reference label supports "
                "retrospective evaluation and is not an input to the "
                "simulated alarm decision."
            ),
        },

        "b187l": {
            "case_title": "Upstream Parameter-Extraction Limitation",
            "case_focus": (
                "This case demonstrates why alarm troubleshooting must "
                "consider the complete signal-processing chain."
            ),
            "what_to_investigate": (
                "Compare the ECG waveform directly with the extracted HR "
                "estimates. Determine whether the derived parameter appears "
                "physiologically consistent with the waveform before "
                "interpreting the downstream alarm decision."
            ),
            "learning_point": (
                "Context-aware alarm logic cannot correct every upstream "
                "signal-processing or parameter-extraction error. Reliable "
                "alarm interpretation depends on the quality of the "
                "information entering the decision logic."
            ),
        },
    }

    return case_content.get(
        record_name,
        {
            "case_title": "Case Review",
            "case_focus": (
                "Review the selected waveform record and simulator results."
            ),
            "what_to_investigate": (
                "Inspect the waveform, derived parameters, threshold "
                "evidence, persistence, and signal-quality context."
            ),
            "learning_point": (
                "Alarm interpretation should consider the complete workflow "
                "from waveform acquisition to decision explanation."
            ),
        },
    )



# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Clinical Alarm Management Simulator",
    layout="wide",
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title(
    "Clinical Alarm Management Simulator"
)

st.caption(
    "Educational comparison of baseline threshold-based "
    "alarm logic and simplified context-aware alarm logic."
)

st.warning(
    "Educational biomedical engineering project only. "
    "Not a medical device, not clinically validated, "
    "and not intended for diagnosis, treatment, "
    "or clinical deployment."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.header(
    "Simulation Controls"
)

record_name = st.sidebar.selectbox(
    "Select a waveform record",
    [
        "b124s",
        "b184s",
        "t106s",
        "t469l",
        "b187l",
    ],
)

st.sidebar.markdown(
    """
    **Example cases**

    - `b124s` — Bradycardia, true-alarm label
    - `b184s` — Bradycardia, false-alarm label
    - `t106s` — Tachycardia, true-alarm label
    - `t469l` — Tachycardia, false-alarm label
    - `b187l` — Example upstream HR-extraction limitation
    """
)


# ---------------------------------------------------------
# Load selected record
# ---------------------------------------------------------

@st.cache_data
def load_record(name):

    return wfdb.rdrecord(
        name,
        pn_dir="challenge-2015/training",
    )


try:

    record = load_record(
        record_name
    )

except Exception as error:

    st.error(
        f"Could not load record {record_name}."
    )

    st.exception(
        error
    )

    st.stop()


# ---------------------------------------------------------
# Record information
# ---------------------------------------------------------

alarm_type = record.comments[0]
reference_label = record.comments[1]

st.header(
    "Clinical Monitor View"
)

col1, col2, col3 = st.columns(
    3
)

with col1:

    st.metric(
        "Selected Record",
        record_name,
    )

with col2:

    st.metric(
        "Alarm Type",
        alarm_type,
    )

with col3:

    st.metric(
        "Dataset Reference Label",
        reference_label,
    )


# ---------------------------------------------------------
# Available signals
# ---------------------------------------------------------

st.subheader(
    "Available Waveform Signals"
)

st.write(
    ", ".join(
        record.sig_name
    )
)

# ---------------------------------------------------------
# Waveform visualization
# ---------------------------------------------------------

st.divider()

st.subheader("Waveform View")

st.write(
    "The plots below show the physiological waveforms near the "
    "dataset alarm evaluation period. The highlighted region "
    "represents the 290–300 second window used by this simplified "
    "simulator."
)

PLOT_START = 285.0
PLOT_END = 300.0

WINDOW_START = 290.0
WINDOW_END = 300.0

fs = record.fs

start_sample = int(
    PLOT_START * fs
)

end_sample = int(
    PLOT_END * fs
)

time_axis = (
    np.arange(
        start_sample,
        end_sample
    )
    / fs
)


# ---------------------------------------------------------
# ECG waveform
# ---------------------------------------------------------

st.markdown("### ECG Waveform")

if "II" in record.sig_name:

    ecg_index = record.sig_name.index(
        "II"
    )

    ecg_segment = record.p_signal[
        start_sample:end_sample,
        ecg_index
    ]

    fig_ecg, ax_ecg = plt.subplots(
        figsize=(12, 3)
    )

    ax_ecg.plot(
        time_axis,
        ecg_segment
    )

    ax_ecg.axvspan(
        WINDOW_START,
        WINDOW_END,
        alpha=0.15,
        label="Evaluation window"
    )

    ax_ecg.axvline(
        WINDOW_START,
        linestyle="--"
    )

    ax_ecg.set_xlabel(
        "Time (seconds)"
    )

    ax_ecg.set_ylabel(
        "ECG amplitude"
    )

    ax_ecg.set_title(
    f"{record_name} — ECG Lead II"
    )

    ax_ecg.legend()

    st.pyplot(
        fig_ecg
    )

    plt.close(
        fig_ecg
    )

else:

    st.warning(
        "ECG Lead II is not available for this record."
    )


# ---------------------------------------------------------
# PLETH waveform
# ---------------------------------------------------------

st.markdown("### PLETH Waveform")

if "PLETH" in record.sig_name:

    pleth_index = record.sig_name.index(
        "PLETH"
    )

    pleth_segment = record.p_signal[
        start_sample:end_sample,
        pleth_index
    ]

    fig_pleth, ax_pleth = plt.subplots(
        figsize=(12, 3)
    )

    ax_pleth.plot(
        time_axis,
        pleth_segment
    )

    ax_pleth.axvspan(
        WINDOW_START,
        WINDOW_END,
        alpha=0.15,
        label="Evaluation window"
    )

    ax_pleth.axvline(
        WINDOW_START,
        linestyle="--"
    )

    ax_pleth.set_xlabel(
        "Time (seconds)"
    )

    ax_pleth.set_ylabel(
        "PLETH amplitude"
    )

    ax_pleth.set_title(
    f"{record_name} — PLETH"
    )

    ax_pleth.legend()

    st.pyplot(
        fig_pleth
    )

    plt.close(
        fig_pleth
    )

else:

    st.warning(
        "PLETH waveform is not available for this record."
    )


# ---------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------

st.divider()

st.subheader("Parameter Extraction View")

st.write(
    "Heart rate (HR) is derived from the ECG signal, while "
    "pulse rate (PR) is derived from the PLETH waveform. "
    "The values below show estimates within the simulator's "
    "290–300 second evaluation window."
)


# ---------------------------------------------------------
# ECG -> HR
# ---------------------------------------------------------

ecg_index = record.sig_name.index("II")

ecg = record.p_signal[
    :,
    ecg_index
]

hr_result = extract_heart_rate(
    ecg,
    record.fs
)

heart_rates = hr_result[
    "heart_rates"
]

heart_rate_times = hr_result[
    "heart_rate_times"
]

hr_window_mask = (
    (heart_rate_times >= WINDOW_START)
    & (heart_rate_times <= WINDOW_END)
)

window_hr = heart_rates[
    hr_window_mask
]

window_hr_times = heart_rate_times[
    hr_window_mask
]


# ---------------------------------------------------------
# PLETH -> PR
# ---------------------------------------------------------

if "PLETH" in record.sig_name:

    pleth_index = record.sig_name.index(
        "PLETH"
    )

    pleth = record.p_signal[
        :,
        pleth_index
    ]

    pr_result = extract_pulse_rate(
        pleth,
        record.fs
    )

    pulse_rates = pr_result[
        "pulse_rates"
    ]

    pulse_rate_times = pr_result[
        "pulse_rate_times"
    ]

    pr_window_mask = (
        (pulse_rate_times >= WINDOW_START)
        & (pulse_rate_times <= WINDOW_END)
    )

    window_pr = pulse_rates[
        pr_window_mask
    ]

    window_pr_times = pulse_rate_times[
        pr_window_mask
    ]

else:

    window_pr = np.array([])
    window_pr_times = np.array([])



# ---------------------------------------------------------
# Parameter summary
# ---------------------------------------------------------

col_hr, col_pr = st.columns(2)

with col_hr:

    st.markdown("### ECG-derived Heart Rate")

    st.metric(
        "HR estimates in evaluation window",
        len(window_hr)
    )

    if len(window_hr) > 0:

        st.write(
            f"Range: "
            f"{np.min(window_hr):.1f}–"
            f"{np.max(window_hr):.1f} bpm"
        )

    else:

        st.warning(
            "No HR estimates were available "
            "in the evaluation window."
        )


with col_pr:

    st.markdown("### PLETH-derived Pulse Rate")

    st.metric(
        "PR estimates in evaluation window",
        len(window_pr)
    )

    if len(window_pr) > 0:

        st.write(
            f"Range: "
            f"{np.min(window_pr):.1f}–"
            f"{np.max(window_pr):.1f} bpm"
        )

    else:

        st.warning(
            "No PR estimates were available "
            "in the evaluation window."
        )

# ---------------------------------------------------------
# HR and PR trend
# ---------------------------------------------------------

st.markdown(
    "### HR and PR Estimates"
)

fig_rates, ax_rates = plt.subplots(
    figsize=(12, 4)
)

if len(window_hr) > 0:

    ax_rates.plot(
        window_hr_times,
        window_hr,
        marker="o",
        label="ECG-derived HR"
    )

if len(window_pr) > 0:

    ax_rates.plot(
        window_pr_times,
        window_pr,
        marker="x",
        label="PLETH-derived PR"
    )

ax_rates.set_xlim(
    WINDOW_START,
    WINDOW_END
)

ax_rates.set_xlabel(
    "Time (seconds)"
)

ax_rates.set_ylabel(
    "Rate (bpm)"
)

ax_rates.set_title(
    f"{record_name} — Derived HR and PR"
)

ax_rates.legend()

ax_rates.grid(
    True,
    alpha=0.3
)

st.pyplot(
    fig_rates
)

plt.close(
    fig_rates
)


# ---------------------------------------------------------
# Alarm system comparison
# ---------------------------------------------------------

st.divider()

st.subheader("Alarm System Comparison")

st.write(
    "The same ECG-derived heart-rate estimates are evaluated by "
    "two simplified alarm-management approaches."
)

# ---------------------------------------------------------
# Determine target alarm classification
# ---------------------------------------------------------

if alarm_type == "Bradycardia":
    target_classification = "BRADYCARDIA"

elif alarm_type == "Tachycardia":
    target_classification = "TACHYCARDIA"

else:
    target_classification = None


# ---------------------------------------------------------
# System A: baseline threshold evaluation
# ---------------------------------------------------------

baseline_results = evaluate_baseline(
    window_hr
)

classifications = [
    result["classification"]
    for result in baseline_results
]

threshold_crossings = sum(
    classification == target_classification
    for classification in classifications
)

if threshold_crossings > 0:
    system_a_decision = "ALARM"
else:
    system_a_decision = "NO_ALARM"



# ---------------------------------------------------------
# System B: contextual evidence
# ---------------------------------------------------------

REQUIRED_CONSECUTIVE = 3

persistence_result = check_persistence(
    classifications,
    target_classification,
    required_consecutive=REQUIRED_CONSECUTIVE,
)

persistence_delay_result = calculate_persistence_delay(
    classifications,
    window_hr_times,
    target_classification,
    required_consecutive=REQUIRED_CONSECUTIVE,
)

hr_quality = assess_rate_quality(
    window_hr
)

pr_quality = assess_rate_quality(
    window_pr
)

consistency_result = check_hr_pr_consistency(
    window_hr,
    window_hr_times,
    window_pr,
    window_pr_times,
)


system_b_result = make_context_aware_decision(
    threshold_crossings=threshold_crossings,
    persistence_result=persistence_result,
    hr_quality=hr_quality,
    pr_quality=pr_quality,
    consistency_result=consistency_result,
)


# ---------------------------------------------------------
# Side-by-side comparison
# ---------------------------------------------------------

col_a, col_b = st.columns(2)

with col_a:

    st.markdown(
        "### System A — Baseline"
    )

    st.write(
        "Simplified logic: "
        "**HR parameter → threshold → alarm decision**"
    )

    st.metric(
        "Target threshold crossings",
        threshold_crossings
    )

    st.metric(
        "Decision",
        system_a_decision
    )


with col_b:

    st.markdown(
        "### System B — Context-Aware"
    )

    st.write(
        "Simplified logic: "
        "**threshold evidence + persistence + "
        "signal-quality context → decision**"
    )

    st.metric(
        "Decision",
        system_b_result["decision"]
    )

    st.write(
        "**Persistence reached:**",
        persistence_result["persistent"]
    )

    st.write(
        "**Maximum consecutive abnormal estimates:**",
        persistence_result["max_consecutive"]
    )

    st.write(
        "**HR quality caution:**",
        hr_quality["caution"]
    )

    st.write(
        "**PR quality caution:**",
        pr_quality["caution"]
    )



# ---------------------------------------------------------
# Cross-parameter context
# ---------------------------------------------------------

st.markdown(
    "### Cross-Parameter Context"
)

cross_col_1, cross_col_2 = st.columns(2)

with cross_col_1:

    st.metric(
        "Matched HR–PR pairs",
        consistency_result["matched_pairs"]
    )


with cross_col_2:

    consistency_fraction = consistency_result[
        "consistency_fraction"
    ]

    if consistency_fraction is not None:

        st.metric(
            "HR–PR consistency",
            f"{consistency_fraction:.2f}"
        )

    else:

        st.metric(
            "HR–PR consistency",
            "N/A"
        )

st.caption(
    "HR–PR agreement is displayed as contextual information. "
    "Disagreement alone does not prove that an alarm is false."
)


# ---------------------------------------------------------
# Decision explanation
# ---------------------------------------------------------

st.markdown(
    "### System B Decision Explanation"
)

st.write(
    "**Decision reason:**",
    system_b_result["reason"]
)


delay = persistence_delay_result[
    "persistence_delay_seconds"
]

if delay is not None:

    st.write(
        f"Persistence was confirmed approximately "
        f"**{delay:.2f} seconds** after the first "
        f"target threshold crossing."
    )

else:

    st.write(
        "Persistence was not confirmed within the "
        "evaluation window."
    )

if system_b_result["decision"] == "ALARM":

    st.success(
        "An ALARM decision means that the simplified contextual system "
        "found sufficient threshold evidence and the configured contextual "
        "conditions for an immediate alarm decision were satisfied."
    )

elif system_b_result["decision"] == "REVIEW":

    st.info(
        "A REVIEW decision means that the simplified simulator found "
        "threshold evidence but did not classify the case as an immediate "
        "ALARM under its contextual rules. REVIEW does not mean that the "
        "dataset alarm was false, clinically unimportant, or safely suppressible."
    )

elif system_b_result["decision"] == "NO_ALARM":

    st.info(
        "A NO_ALARM decision means that the simplified simulator did not "
        "identify target threshold evidence within the evaluation window. "
        "This simulator decision should not be interpreted as evidence that "
        "the patient or waveform is clinically normal."
    )





# ---------------------------------------------------------
# Clinical workflow interpretation
# ---------------------------------------------------------

st.markdown(
    "### Clinical Workflow Interpretation"
)

workflow_interpretation = get_workflow_interpretation(
    system_b_result["reason"]
)

st.info(
    workflow_interpretation
)

st.markdown(
    "### Suggested Review Workflow"
)

st.markdown(
    """
    1. **Verify the waveform** — Inspect the ECG waveform for signal
       integrity, artifact, baseline disturbance, or unusual morphology.

    2. **Verify the derived parameter** — Determine whether the displayed
       heart-rate estimate appears consistent with the underlying waveform.

    3. **Review threshold evidence** — Check whether the derived parameter
       crossed the configured alarm threshold and whether the condition
       persisted.

    4. **Compare available parameters** — Review ECG-derived HR alongside
       PLETH-derived PR when both signals are available.

    5. **Review signal-quality context** — Consider whether parameter
       instability or implausible values may affect confidence in the
       derived measurements.

    6. **Interpret the simulator decision** — Compare System A with
       System B and examine why their decisions differ.
    """
)

st.caption(
    "This workflow is an educational troubleshooting framework for the "
    "simulator. It does not represent a validated clinical protocol or "
    "replace institutional alarm-management policies."
)

system_a_explanation, system_b_explanation = (
    get_dynamic_system_explanation(
        threshold_crossings=threshold_crossings,
        system_a_decision=system_a_decision,
        persistence_result=persistence_result,
        hr_quality=hr_quality,
        pr_quality=pr_quality,
        system_b_result=system_b_result,
    )
)

case_learning = get_case_learning_content(
    record_name
)


# ---------------------------------------------------------
# Interactive case walkthrough
# ---------------------------------------------------------

st.divider()

st.header(
    "Interactive Case Walkthrough"
)

case_walkthrough = get_case_walkthrough(
    record_name
)

if case_walkthrough is not None:

    st.markdown(
        "#### Case Summary"
    )

    st.write(
        case_walkthrough["case_summary"]
    )

    # Generate explanations from the actual simulator results
    system_a_explanation, system_b_explanation = (
        get_dynamic_system_explanation(
            threshold_crossings=threshold_crossings,
            system_a_decision=system_a_decision,
            persistence_result=persistence_result,
            hr_quality=hr_quality,
            pr_quality=pr_quality,
            system_b_result=system_b_result,
        )
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "#### What System A Sees"
        )

        st.write(
            system_a_explanation
        )

    with col2:

        st.markdown(
            "#### What System B Sees"
        )

        st.write(
            system_b_explanation
        )

    st.markdown(
        "#### What to Investigate"
    )

    st.info(
        case_walkthrough[
            "investigation"
        ]
    )

    st.markdown(
        "#### Key Learning Point"
    )

    st.success(
        case_walkthrough[
            "learning_point"
        ]
    )

    st.caption(
        "The dataset reference label is used only for retrospective "
        "educational comparison and is not provided to either simulated "
        "alarm system when generating its decision."
    )


# ---------------------------------------------------------
# Workflow explanation
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Simulator Workflow"
)

st.markdown(
    """
    **Waveform acquisition**
    → **Parameter extraction**
    → **Threshold evaluation**
    → **Context checks**
    → **Alarm decision**
    → **Decision explanation**
    """
)

st.info(
    "The dataset reference label is shown for retrospective "
    "comparison. It is not used by either simulated alarm "
    "system to make its decision."
)