import pandas as pd


RESULTS_FILE = "dataset_evaluation_results.csv"


def main():

    df = pd.read_csv(
        RESULTS_FILE
    )

    print("=" * 70)
    print("DATASET RESULTS ANALYSIS")
    print("=" * 70)

    print(
        "\nTotal evaluated records:",
        len(df)
    )

    print("\nReference labels")

    print(
        df["reference_label"]
        .value_counts()
        .sort_index()
    )

    # ---------------------------------------------------------
    # System A
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SYSTEM A")
    print("=" * 70)

    system_a = pd.crosstab(
        df["reference_label"],
        df["system_a_decision"]
    )

    print(
        system_a
    )

    # ---------------------------------------------------------
    # System B
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SYSTEM B")
    print("=" * 70)

    system_b = pd.crosstab(
        df["reference_label"],
        df["system_b_decision"]
    )

    print(
        system_b
    )

    # ---------------------------------------------------------
    # REVIEW analysis
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SYSTEM B REVIEW CASES")
    print("=" * 70)

    review_df = df[
        df["system_b_decision"] == "REVIEW"
    ]

    print(
        review_df["reference_label"]
        .value_counts()
    )

    # ---------------------------------------------------------
    # Results by alarm type
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("RESULTS BY ALARM TYPE")
    print("=" * 70)

    for alarm_type in [
        "Bradycardia",
        "Tachycardia",
    ]:

        subset = df[
            df["alarm_type"] == alarm_type
        ]

        print("\n" + "-" * 70)
        print(
            alarm_type.upper()
        )
        print("-" * 70)

        print(
            "\nTotal evaluated records:",
            len(subset)
        )

        print(
            "\nReference labels"
        )

        print(
            subset["reference_label"]
            .value_counts()
            .sort_index()
        )

        print(
            "\nSYSTEM A"
        )

        print(
            pd.crosstab(
                subset["reference_label"],
                subset["system_a_decision"]
            )
        )

        print(
            "\nSYSTEM B"
        )

        print(
            pd.crosstab(
                subset["reference_label"],
                subset["system_b_decision"]
            )
        )

        print(
            "\nSYSTEM B REVIEW CASES"
        )

        review_cases = subset[
            subset["system_b_decision"] == "REVIEW"
        ]

        print(
            review_cases["reference_label"]
            .value_counts()
        )

    # ---------------------------------------------------------
    # System B decision reason analysis
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SYSTEM B DECISION REASONS")
    print("=" * 70)

    print("\nOverall")

    print(
        df["system_b_reason"]
        .value_counts()
    )

    print("\nBy reference label")

    print(
        pd.crosstab(
            df["reference_label"],
            df["system_b_reason"]
        )
    )

    print("\nBy alarm type")

    print(
        pd.crosstab(
            df["alarm_type"],
            df["system_b_reason"]
        )
    )

    print("\nBy alarm type and reference label")

    for alarm_type in [
        "Bradycardia",
        "Tachycardia",
    ]:

        subset = df[
            df["alarm_type"] == alarm_type
        ]

        print("\n" + "-" * 70)
        print(alarm_type.upper())
        print("-" * 70)

        print(
            pd.crosstab(
                subset["reference_label"],
                subset["system_b_reason"]
            )
        )


    # ---------------------------------------------------------
    # REVIEW case context breakdown
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SYSTEM B REVIEW CONTEXT BREAKDOWN")
    print("=" * 70)

    review_df = df[
        df["system_b_decision"] == "REVIEW"
    ]

    print("\nPersistence in REVIEW cases")

    print(
        pd.crosstab(
            review_df["reference_label"],
            review_df["persistent"]
        )
    )

    print("\nHR quality caution in REVIEW cases")

    print(
        pd.crosstab(
            review_df["reference_label"],
            review_df["hr_quality_caution"]
        )
    )

    print("\nPR quality caution in REVIEW cases")

    print(
        pd.crosstab(
            review_df["reference_label"],
            review_df["pr_quality_caution"]
        )
    )

    print("\nCombined context in REVIEW cases")

    print(
        review_df.groupby(
            [
                "reference_label",
                "persistent",
                "hr_quality_caution",
                "pr_quality_caution",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .to_string(
            index=False
        )
    )


    # ---------------------------------------------------------
    # Persistence delay analysis
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERSISTENCE DELAY ANALYSIS")
    print("=" * 70)

    delay_df = df[
        df["persistence_delay_seconds"].notna()
    ].copy()

    print(
        "\nRecords where persistence was reached:",
        len(delay_df)
    )

    if not delay_df.empty:

        print("\nOverall persistence delay (seconds)")

        print(
            delay_df["persistence_delay_seconds"]
            .describe()
        )

        print("\nPersistence delay by alarm type")

        print(
            delay_df.groupby(
                "alarm_type"
            )["persistence_delay_seconds"]
            .agg([
                "count",
                "mean",
                "median",
                "min",
                "max",
            ])
        )

        print(
            "\nPersistence delay by reference label"
        )

        print(
            delay_df.groupby(
                "reference_label"
            )["persistence_delay_seconds"]
            .agg([
                "count",
                "mean",
                "median",
                "min",
                "max",
            ])
        )

        print(
            "\nPersistence delay by alarm type "
            "and reference label"
        )

        print(
            delay_df.groupby(
                [
                    "alarm_type",
                    "reference_label",
                ]
            )["persistence_delay_seconds"]
            .agg([
                "count",
                "mean",
                "median",
                "min",
                "max",
            ])
        )


    # ---------------------------------------------------------
    # Representative error / behavior cases
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("REPRESENTATIVE CASES FOR ERROR ANALYSIS")
    print("=" * 70)

    case_groups = {
        "True alarm -> System B ALARM": (
            (df["reference_label"] == "True alarm")
            & (df["system_b_decision"] == "ALARM")
        ),
        "True alarm -> System B REVIEW": (
            (df["reference_label"] == "True alarm")
            & (df["system_b_decision"] == "REVIEW")
        ),
        "False alarm -> System B REVIEW": (
            (df["reference_label"] == "False alarm")
            & (df["system_b_decision"] == "REVIEW")
        ),
        "True alarm -> System B NO_ALARM": (
            (df["reference_label"] == "True alarm")
            & (df["system_b_decision"] == "NO_ALARM")
        ),
    }

    columns_to_show = [
        "record",
        "alarm_type",
        "reference_label",
        "threshold_crossings",
        "max_consecutive",
        "persistent",
        "hr_quality_caution",
        "pr_quality_caution",
        "matched_pairs",
        "consistency_fraction",
        "persistence_delay_seconds",
        "system_b_decision",
        "system_b_reason",
    ]

    for group_name, condition in case_groups.items():

        print("\n" + "-" * 70)
        print(group_name)
        print("-" * 70)

        cases = df.loc[
            condition,
            columns_to_show
        ]

        print(
            cases.head(5).to_string(
                index=False
            )
        )




    # ---------------------------------------------------------
    # Immediate ALARM decision reduction
    # ---------------------------------------------------------

    system_a_alarm = (
        df["system_a_decision"] == "ALARM"
    ).sum()

    system_b_alarm = (
        df["system_b_decision"] == "ALARM"
    ).sum()

    reduction = (
        system_a_alarm
        - system_b_alarm
    )

    reduction_percent = (
        reduction
        / system_a_alarm
    ) * 100

    print("\n" + "=" * 70)
    print("IMMEDIATE ALARM DECISION REDUCTION")
    print("=" * 70)

    print(
        "System A immediate ALARM decisions:",
        system_a_alarm
    )

    print(
        "System B immediate ALARM decisions:",
        system_b_alarm
    )

    print(
        "Decisions redirected from immediate ALARM:",
        reduction
    )

    print(
        f"Reduction in immediate ALARM decisions: "
        f"{reduction_percent:.2f}%"
    )

    print(
        "Note: REVIEW decisions are not equivalent to eliminated "
        "clinical alarms."
    )


if __name__ == "__main__":
    main()