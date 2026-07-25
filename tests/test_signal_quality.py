import pytest

from src.signal_processing.signal_quality import assess_rate_quality


def test_stable_rate_sequence():
    result = assess_rate_quality(
        [80, 82, 81, 83, 82]
    )

    assert result["empty"] is False
    assert result["non_finite"] is False
    assert result["out_of_range"] is False
    assert result["sudden_jump"] is False
    assert result["caution"] is False


def test_sudden_rate_jump():
    result = assess_rate_quality(
        [125, 126, 127, 63, 127]
    )

    assert result["sudden_jump"] is True
    assert result["caution"] is True


def test_out_of_range_rate():
    result = assess_rate_quality(
        [80, 82, 250, 81]
    )

    assert result["out_of_range"] is True
    assert result["caution"] is True


def test_non_finite_rate():
    result = assess_rate_quality(
        [80, float("nan"), 82]
    )

    assert result["non_finite"] is True
    assert result["caution"] is True


def test_empty_rate_sequence():
    result = assess_rate_quality([])

    assert result["empty"] is True
    assert result["caution"] is True


def test_invalid_rate_range():
    with pytest.raises(ValueError):
        assess_rate_quality(
            [80, 90],
            min_valid_rate=220,
            max_valid_rate=20
        )


def test_invalid_max_rate_jump():
    with pytest.raises(ValueError):
        assess_rate_quality(
            [80, 90],
            max_rate_jump=0
        )