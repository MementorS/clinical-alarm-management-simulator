import pytest

from src.alarm_systems.context_aware import check_persistence

from src.alarm_systems.context_aware import (
    check_persistence,
    make_context_aware_decision,
    calculate_persistence_delay,
)

def test_persistence_delay_three_consecutive():
    result = calculate_persistence_delay(
        classifications=[
            "NORMAL",
            "TACHYCARDIA",
            "TACHYCARDIA",
            "TACHYCARDIA",
        ],
        classification_times=[
            290.0,
            291.0,
            292.0,
            293.0,
        ],
        target_classification="TACHYCARDIA",
        required_consecutive=3,
    )

    assert result["first_threshold_time"] == 291.0
    assert result["persistence_confirmation_time"] == 293.0
    assert result["persistence_delay_seconds"] == 2.0


def test_persistence_delay_not_reached():
    result = calculate_persistence_delay(
        classifications=[
            "BRADYCARDIA",
            "NORMAL",
            "BRADYCARDIA",
        ],
        classification_times=[
            290.0,
            291.0,
            292.0,
        ],
        target_classification="BRADYCARDIA",
        required_consecutive=3,
    )

    assert result["first_threshold_time"] == 290.0
    assert result["persistence_confirmation_time"] is None
    assert result["persistence_delay_seconds"] is None


def test_persistence_delay_no_threshold_crossing():
    result = calculate_persistence_delay(
        classifications=[
            "NORMAL",
            "NORMAL",
        ],
        classification_times=[
            290.0,
            291.0,
        ],
        target_classification="TACHYCARDIA",
        required_consecutive=3,
    )

    assert result["first_threshold_time"] is None
    assert result["persistence_confirmation_time"] is None
    assert result["persistence_delay_seconds"] is None

def test_persistent_bradycardia():
    classifications = [
        "NORMAL",
        "BRADYCARDIA",
        "BRADYCARDIA",
        "BRADYCARDIA",
        "NORMAL",
    ]

    result = check_persistence(
        classifications,
        "BRADYCARDIA",
        required_consecutive=3
    )

    assert result["persistent"] is True
    assert result["max_consecutive"] == 3


def test_isolated_bradycardia_not_persistent():
    classifications = [
        "NORMAL",
        "BRADYCARDIA",
        "NORMAL",
        "BRADYCARDIA",
        "NORMAL",
    ]

    result = check_persistence(
        classifications,
        "BRADYCARDIA",
        required_consecutive=3
    )

    assert result["persistent"] is False
    assert result["max_consecutive"] == 1


def test_interrupted_tachycardia_not_persistent():
    classifications = [
        "TACHYCARDIA",
        "TACHYCARDIA",
        "NORMAL",
        "TACHYCARDIA",
        "TACHYCARDIA",
    ]

    result = check_persistence(
        classifications,
        "TACHYCARDIA",
        required_consecutive=3
    )

    assert result["persistent"] is False
    assert result["max_consecutive"] == 2


def test_long_persistent_tachycardia():
    classifications = [
        "NORMAL",
        "TACHYCARDIA",
        "TACHYCARDIA",
        "TACHYCARDIA",
        "TACHYCARDIA",
    ]

    result = check_persistence(
        classifications,
        "TACHYCARDIA",
        required_consecutive=3
    )

    assert result["persistent"] is True
    assert result["max_consecutive"] == 4


def test_no_target_classification():
    classifications = [
        "NORMAL",
        "NORMAL",
        "NORMAL",
    ]

    result = check_persistence(
        classifications,
        "BRADYCARDIA",
        required_consecutive=3
    )

    assert result["persistent"] is False
    assert result["max_consecutive"] == 0


def test_invalid_required_consecutive():
    with pytest.raises(ValueError):
        check_persistence(
            ["NORMAL"],
            "BRADYCARDIA",
            required_consecutive=0
        )


def test_empty_target_classification():
    with pytest.raises(ValueError):
        check_persistence(
            ["NORMAL"],
            "",
            required_consecutive=3
        )

def test_hr_pr_all_consistent():
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    result = check_hr_pr_consistency(
        heart_rates=[80, 100],
        heart_rate_times=[1.0, 2.0],
        pulse_rates=[82, 97],
        pulse_rate_times=[1.1, 2.1]
    )

    assert result["matched_pairs"] == 2
    assert result["consistent_pairs"] == 2
    assert result["inconsistent_pairs"] == 0
    assert result["consistency_fraction"] == 1.0


def test_hr_pr_mixed_consistency():
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    result = check_hr_pr_consistency(
        heart_rates=[80, 120],
        heart_rate_times=[1.0, 2.0],
        pulse_rates=[82, 150],
        pulse_rate_times=[1.1, 2.1]
    )

    assert result["matched_pairs"] == 2
    assert result["consistent_pairs"] == 1
    assert result["inconsistent_pairs"] == 1
    assert result["consistency_fraction"] == 0.5


def test_hr_pr_no_nearby_match():
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    result = check_hr_pr_consistency(
        heart_rates=[80],
        heart_rate_times=[1.0],
        pulse_rates=[82],
        pulse_rate_times=[5.0],
        max_time_difference=0.5
    )

    assert result["matched_pairs"] == 0
    assert result["consistency_fraction"] is None


def test_hr_pr_empty_pulse_rates():
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    result = check_hr_pr_consistency(
        heart_rates=[80],
        heart_rate_times=[1.0],
        pulse_rates=[],
        pulse_rate_times=[]
    )

    assert result["matched_pairs"] == 0
    assert result["consistency_fraction"] is None


def test_hr_pr_length_mismatch():
    import pytest
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    with pytest.raises(ValueError):
        check_hr_pr_consistency(
            heart_rates=[80, 90],
            heart_rate_times=[1.0],
            pulse_rates=[82],
            pulse_rate_times=[1.1]
        )


def test_invalid_max_time_difference():
    import pytest
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    with pytest.raises(ValueError):
        check_hr_pr_consistency(
            heart_rates=[80],
            heart_rate_times=[1.0],
            pulse_rates=[82],
            pulse_rate_times=[1.1],
            max_time_difference=0
        )


def test_invalid_max_rate_difference():
    import pytest
    from src.alarm_systems.context_aware import check_hr_pr_consistency

    with pytest.raises(ValueError):
        check_hr_pr_consistency(
            heart_rates=[80],
            heart_rate_times=[1.0],
            pulse_rates=[82],
            pulse_rate_times=[1.1],
            max_rate_difference=-1
        )


from src.alarm_systems.context_aware import make_context_aware_decision


def test_context_decision_no_threshold_crossing():
    result = make_context_aware_decision(
        threshold_crossings=0,
        persistence_result={"persistent": False},
        hr_quality={"caution": True},
        pr_quality={"caution": True},
        consistency_result={"consistency_fraction": None},
    )

    assert result["decision"] == "NO_ALARM"


def test_context_decision_persistent_good_hr():
    result = make_context_aware_decision(
        threshold_crossings=10,
        persistence_result={"persistent": True},
        hr_quality={"caution": False},
        pr_quality={"caution": False},
        consistency_result={"consistency_fraction": 0.8},
    )

    assert result["decision"] == "ALARM"


def test_context_decision_nonpersistent_good_quality():
    result = make_context_aware_decision(
        threshold_crossings=3,
        persistence_result={"persistent": False},
        hr_quality={"caution": False},
        pr_quality={"caution": False},
        consistency_result={"consistency_fraction": 0.8},
    )

    assert result["decision"] == "REVIEW"


def test_context_decision_quality_caution():
    result = make_context_aware_decision(
        threshold_crossings=3,
        persistence_result={"persistent": False},
        hr_quality={"caution": True},
        pr_quality={"caution": True},
        consistency_result={"consistency_fraction": 0.8},
    )

    assert result["decision"] == "REVIEW"


def test_context_decision_invalid_threshold_crossings():
    import pytest

    with pytest.raises(ValueError):
        make_context_aware_decision(
            threshold_crossings=-1,
            persistence_result={"persistent": False},
            hr_quality={"caution": False},
            pr_quality={"caution": False},
            consistency_result={"consistency_fraction": 0.8},
        )


def test_context_decision_persistent_with_hr_pr_disagreement():
    """
    HR-PR disagreement alone should not override persistent,
    acceptable-quality ECG threshold evidence.
    """

    result = make_context_aware_decision(
        threshold_crossings=10,
        persistence_result={"persistent": True},
        hr_quality={"caution": False},
        pr_quality={"caution": False},
        consistency_result={"consistency_fraction": 0.3},
    )

    assert result["decision"] == "ALARM"


def test_context_decision_persistent_with_no_hr_pr_matches():
    """
    Missing HR-PR matches alone should not override persistent,
    acceptable-quality ECG threshold evidence.
    """

    result = make_context_aware_decision(
        threshold_crossings=10,
        persistence_result={"persistent": True},
        hr_quality={"caution": False},
        pr_quality={"caution": False},
        consistency_result={"consistency_fraction": None},
    )

    assert result["decision"] == "ALARM"


def test_context_decision_persistent_with_acceptable_context():
    result = make_context_aware_decision(
        threshold_crossings=10,
        persistence_result={"persistent": True},
        hr_quality={"caution": False},
        pr_quality={"caution": False},
        consistency_result={"consistency_fraction": 0.8},
    )

    assert result["decision"] == "ALARM"