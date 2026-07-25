import csv

import wfdb

from src.signal_processing.ecg import extract_heart_rate
from src.signal_processing.pleth import extract_pulse_rate
from src.signal_processing.signal_quality import assess_rate_quality
from src.alarm_systems.baseline import evaluate_baseline
from src.alarm_systems.context_aware import (
    check_persistence,
    calculate_persistence_delay,
    check_hr_pr_consistency,
    make_context_aware_decision,
)


PN_DIR = "challenge-2015/training"

WINDOW_START = 290.0
WINDOW_END = 300.0

REQUIRED_CONSECUTIVE = 3

OUTPUT_FILE = "dataset_evaluation_results.csv"


def evaluate_record(record_name):
    """
    Evaluate one Bradycardia or Tachycardia record.

    Returns a dictionary containing the reference label,
    System A decision, System B decision, and contextual evidence.

    Returns None for unsupported records or records without PLETH.
    """

    record = wfdb.rdrecord(
        record_name,
        pn_dir=PN_DIR
    )

    if len(record.comments) < 2:
        return None

    alarm_type = record.comments[0]
    reference_label = record.comments[1]

    if alarm_type == "Bradycardia":
        target_classification = "BRADYCARDIA"

    elif alarm_type == "Tachycardia":
        target_classification = "TACHYCARDIA"

    else:
        return None

    if "II" not in record.sig_name:
        return None

    if "PLETH" not in record.sig_name:
        return None

    # ---------------------------------------------------------
    # ECG -> HR
    # ---------------------------------------------------------

    ecg_index = record.sig_name.index("II")
    ecg = record.p_signal[:, ecg_index]

    hr_result = extract_heart_rate(
        ecg,
        record.fs
    )

    heart_rates = hr_result["heart_rates"]
    heart_rate_times = hr_result["heart_rate_times"]

    hr_mask = (
        (heart_rate_times >= WINDOW_START)
        & (heart_rate_times <= WINDOW_END)
    )

    window_hr = heart_rates[hr_mask]
    window_hr_times = heart_rate_times[hr_mask]

    # ---------------------------------------------------------
    # Baseline classification
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

    # ---------------------------------------------------------
    # System A
    # ---------------------------------------------------------

    if threshold_crossings > 0:
        system_a_decision = "ALARM"
    else:
        system_a_decision = "NO_ALARM"

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    persistence_result = check_persistence(
        classifications,
        target_classification,
        required_consecutive=REQUIRED_CONSECUTIVE
    )

    persistence_delay_result = calculate_persistence_delay(
        classifications,
        window_hr_times,
        target_classification,
        required_consecutive=REQUIRED_CONSECUTIVE,
    )   


    # ---------------------------------------------------------
    # HR quality
    # ---------------------------------------------------------

    hr_quality = assess_rate_quality(
        window_hr
    )

    # ---------------------------------------------------------
    # PLETH -> PR
    # ---------------------------------------------------------

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

    pr_mask = (
        (pulse_rate_times >= WINDOW_START)
        & (pulse_rate_times <= WINDOW_END)
    )

    window_pr = pulse_rates[pr_mask]
    window_pr_times = pulse_rate_times[pr_mask]

    # ---------------------------------------------------------
    # PR quality
    # ---------------------------------------------------------

    pr_quality = assess_rate_quality(
        window_pr
    )

    # ---------------------------------------------------------
    # HR/PR consistency
    # ---------------------------------------------------------

    consistency_result = check_hr_pr_consistency(
        window_hr,
        window_hr_times,
        window_pr,
        window_pr_times
    )

    # ---------------------------------------------------------
    # System B
    # ---------------------------------------------------------

    system_b_result = make_context_aware_decision(
        threshold_crossings=threshold_crossings,
        persistence_result=persistence_result,
        hr_quality=hr_quality,
        pr_quality=pr_quality,
        consistency_result=consistency_result,
    )

    return {
        "record": record_name,
        "alarm_type": alarm_type,
        "reference_label": reference_label,
        "hr_estimates": len(window_hr),
        "pr_estimates": len(window_pr),
        "threshold_crossings": threshold_crossings,

        "max_consecutive": persistence_result[
            "max_consecutive"
        ],

        "persistent": persistence_result[
            "persistent"
        ],

        # Persistence delay information
        "first_threshold_time": persistence_delay_result[
            "first_threshold_time"
        ],

        "persistence_confirmation_time": persistence_delay_result[
            "persistence_confirmation_time"
        ],

        "persistence_delay_seconds": persistence_delay_result[
            "persistence_delay_seconds"
        ],

        "hr_quality_caution": hr_quality[
            "caution"
        ],

        "pr_quality_caution": pr_quality[
            "caution"
        ],

        "matched_pairs": consistency_result[
            "matched_pairs"
        ],

        "consistency_fraction": consistency_result[
            "consistency_fraction"
        ],

        "system_a_decision": system_a_decision,

        "system_b_decision": system_b_result[
            "decision"
        ],

        "system_b_reason": system_b_result[
            "reason"
        ],
    }


def main():

    # ---------------------------------------------------------
    # Obtain Challenge 2015 training record list
    # ---------------------------------------------------------

    import requests

    records_url = (
        "https://physionet.org/files/"
        "challenge-2015/1.0.0/training/RECORDS"
    )

    print("Downloading training record list...")

    response = requests.get(
        records_url,
        timeout=30
    )

    response.raise_for_status()

    all_record_names = (
        response.text
        .strip()
        .splitlines()
    )

    print(
        "Total training records found:",
        len(all_record_names)
    )

    # ---------------------------------------------------------
    # Keep Bradycardia and Tachycardia candidates only
    #
    # b = Bradycardia
    # t = Tachycardia
    # ---------------------------------------------------------

    record_names = [
        name
        for name in all_record_names
        if name.startswith(("b", "t"))
    ]

    print(
        "Bradycardia/Tachycardia candidates:",
        len(record_names)
    )

    print(
        "First 20 candidates:",
        record_names[:20]
    )

    # ---------------------------------------------------------
    # Evaluate records
    # ---------------------------------------------------------

    results = []
    skipped = 0
    failed = 0

    for index, record_name in enumerate(
        record_names,
        start=1
    ):

        print(
            f"[{index}/{len(record_names)}] "
            f"Processing {record_name}"
        )

        try:

            result = evaluate_record(
                record_name
            )

            if result is None:
                skipped += 1
                continue

            results.append(
                result
            )

        except Exception as error:

            failed += 1

            print(
                f"FAILED {record_name}: "
                f"{error}"
            )

    # ---------------------------------------------------------
    # Save CSV
    # ---------------------------------------------------------

    if results:

        fieldnames = list(
            results[0].keys()
        )

        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(
                results
            )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATASET EVALUATION COMPLETE")
    print("=" * 70)

    print(
        "Evaluated records:",
        len(results)
    )

    print(
        "Skipped records:",
        skipped
    )

    print(
        "Failed records:",
        failed
    )

    print(
        "Results saved to:",
        OUTPUT_FILE
    )

    if not results:
        return

    # ---------------------------------------------------------
    # System A summary
    # ---------------------------------------------------------

    print("\n--- SYSTEM A ---")

    print(
        "ALARM:",
        sum(
            result["system_a_decision"] == "ALARM"
            for result in results
        )
    )

    print(
        "NO_ALARM:",
        sum(
            result["system_a_decision"] == "NO_ALARM"
            for result in results
        )
    )

    # ---------------------------------------------------------
    # System B summary
    # ---------------------------------------------------------

    print("\n--- SYSTEM B ---")

    for decision in [
        "ALARM",
        "REVIEW",
        "NO_ALARM",
    ]:

        count = sum(
            result["system_b_decision"] == decision
            for result in results
        )

        print(
            f"{decision}:",
            count
        )


if __name__ == "__main__":
    main()