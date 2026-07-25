import wfdb

from src.signal_processing.ecg import extract_heart_rate
from src.signal_processing.signal_quality import assess_rate_quality
from src.alarm_systems.baseline import evaluate_baseline


RECORDS = [
    "t106s",  # True alarm -> System B ALARM
    "b124s",  # True alarm -> System B REVIEW
    "b184s",  # False alarm -> System B REVIEW
    "b187l",  # True alarm -> System B NO_ALARM
]

PN_DIR = "challenge-2015/training"

WINDOW_START = 290.0
WINDOW_END = 300.0


def inspect_record(record_name):

    print("\n" + "=" * 70)
    print("RECORD:", record_name)
    print("=" * 70)

    # ---------------------------------------------------------
    # Load record
    # ---------------------------------------------------------

    record = wfdb.rdrecord(
        record_name,
        pn_dir=PN_DIR,
    )

    alarm_type = record.comments[0]
    reference_label = record.comments[1]

    print("Alarm type:", alarm_type)
    print("Reference label:", reference_label)
    print("Signals:", record.sig_name)
    print("Sampling frequency:", record.fs)

    # ---------------------------------------------------------
    # Select ECG lead
    # ---------------------------------------------------------

    if "II" not in record.sig_name:
        print("Lead II not available.")
        return

    ecg_index = record.sig_name.index("II")

    ecg = record.p_signal[
        :,
        ecg_index
    ]

    # ---------------------------------------------------------
    # Extract HR
    # ---------------------------------------------------------

    hr_result = extract_heart_rate(
        ecg,
        record.fs,
    )

    heart_rates = hr_result[
        "heart_rates"
    ]

    heart_rate_times = hr_result[
        "heart_rate_times"
    ]

    # ---------------------------------------------------------
    # Evaluation window
    # ---------------------------------------------------------

    window_mask = (
        (heart_rate_times >= WINDOW_START)
        & (heart_rate_times <= WINDOW_END)
    )

    window_hr = heart_rates[
        window_mask
    ]

    window_hr_times = heart_rate_times[
        window_mask
    ]

    # ---------------------------------------------------------
    # Baseline classifications
    # ---------------------------------------------------------

    baseline_results = evaluate_baseline(
        window_hr
    )

    classifications = [
        result["classification"]
        for result in baseline_results
    ]

    # ---------------------------------------------------------
    # Determine target classification
    # ---------------------------------------------------------

    if alarm_type == "Bradycardia":
        target_classification = "BRADYCARDIA"

    elif alarm_type == "Tachycardia":
        target_classification = "TACHYCARDIA"

    else:
        print(
            "Unsupported alarm type for this inspection."
        )
        return

    threshold_crossings = sum(
        classification == target_classification
        for classification in classifications
    )

    # ---------------------------------------------------------
    # HR quality
    # ---------------------------------------------------------

    hr_quality = assess_rate_quality(
        window_hr
    )

    # ---------------------------------------------------------
    # Print detailed HR sequence
    # ---------------------------------------------------------

    print(
        f"\nEvaluation window: "
        f"{WINDOW_START}-{WINDOW_END} seconds"
    )

    print(
        "\nNumber of HR estimates:",
        len(window_hr)
    )

    print(
        "Target classification:",
        target_classification
    )

    print(
        "Target threshold crossings:",
        threshold_crossings
    )

    print(
        "HR quality:",
        hr_quality
    )

    print("\nHR ESTIMATES AND CLASSIFICATIONS")

    print(
        f"{'Time (s)':>10} "
        f"{'HR (bpm)':>10} "
        f"{'Classification':>18}"
    )

    print("-" * 42)

    for time, hr, classification in zip(
        window_hr_times,
        window_hr,
        classifications,
    ):

        print(
            f"{time:10.3f} "
            f"{hr:10.2f} "
            f"{classification:>18}"
        )

    # ---------------------------------------------------------
    # Special diagnostic note
    # ---------------------------------------------------------

    if threshold_crossings == 0:

        print(
            "\nDIAGNOSTIC NOTE:"
        )

        print(
            "No target threshold crossing was detected "
            "by the simplified HR pipeline in the "
            "evaluation window."
        )

        print(
            "This should be investigated as an upstream "
            "parameter-extraction/windowing limitation "
            "before attributing the result to contextual "
            "alarm logic."
        )


def main():

    print("=" * 70)
    print("REPRESENTATIVE ERROR-CASE INSPECTION")
    print("=" * 70)

    for record_name in RECORDS:
        inspect_record(
            record_name
        )


if __name__ == "__main__":
    main()