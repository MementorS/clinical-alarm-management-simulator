import pytest

from src.alarm_systems.baseline import classify_heart_rate


def test_bradycardia():
    assert classify_heart_rate(39) == "BRADYCARDIA"


def test_tachycardia():
    assert classify_heart_rate(141) == "TACHYCARDIA"


def test_normal_heart_rate():
    assert classify_heart_rate(80) == "NORMAL"


def test_bradycardia_boundary():
    # Current simplified rule is HR < 40
    assert classify_heart_rate(40) == "NORMAL"


def test_tachycardia_boundary():
    # Current simplified rule is HR > 140
    assert classify_heart_rate(140) == "NORMAL"


def test_invalid_nan():
    with pytest.raises(ValueError):
        classify_heart_rate(float("nan"))


def test_invalid_threshold_order():
    with pytest.raises(ValueError):
        classify_heart_rate(
            80,
            brady_threshold=150,
            tachy_threshold=140
        )


from src.alarm_systems.baseline import evaluate_baseline


def test_evaluate_baseline_sequence():
    heart_rates = [80, 82, 145, 150, 90, 35]

    results = evaluate_baseline(heart_rates)

    classifications = [
        result["classification"]
        for result in results
    ]

    alarms = [
        result["alarm"]
        for result in results
    ]

    assert classifications == [
        "NORMAL",
        "NORMAL",
        "TACHYCARDIA",
        "TACHYCARDIA",
        "NORMAL",
        "BRADYCARDIA",
    ]

    assert alarms == [
        False,
        False,
        True,
        True,
        False,
        True,
    ]


def test_evaluate_baseline_empty_sequence():
    results = evaluate_baseline([])

    assert results == []


def test_evaluate_baseline_invalid_dimensions():
    heart_rates = [
        [80, 90],
        [100, 110]
    ]

    with pytest.raises(ValueError):
        evaluate_baseline(heart_rates)