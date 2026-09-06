from app.core.classifier import MAXIMUM_QUESTIONS, MINIMUM_QUESTIONS, check_stopping


def test_never_finishes_below_minimum():
    confident_probs = {"a": 0.99, "b": 0.005, "c": 0.005}
    for answered in range(0, MINIMUM_QUESTIONS):
        assert check_stopping(confident_probs, answered) is False


def test_finishes_at_or_after_minimum_when_confident():
    probs = {"a": 0.70, "b": 0.20, "c": 0.10}
    assert check_stopping(probs, MINIMUM_QUESTIONS) is True


def test_continues_at_minimum_without_confidence():
    """Both failure modes checked at the minimum itself.

    MINIMUM_QUESTIONS + 1 would be wrong here: the band is currently one
    question wide (14/15), so that is the cap, where the rule stops
    unconditionally regardless of confidence.
    """
    probs = {"a": 0.5, "b": 0.45, "c": 0.05}  # top below 0.65 and gap too small
    assert check_stopping(probs, MINIMUM_QUESTIONS) is False
    probs = {"a": 0.66, "b": 0.60, "c": 0.0}  # top high enough, gap too small
    assert check_stopping(probs, MINIMUM_QUESTIONS) is False


def test_minimum_is_below_maximum():
    """A band of zero would make the early-stop branch dead code."""
    assert MINIMUM_QUESTIONS < MAXIMUM_QUESTIONS


def test_always_finishes_at_maximum_regardless_of_confidence():
    hopeless_probs = {"a": 0.34, "b": 0.33, "c": 0.33}
    assert check_stopping(hopeless_probs, MAXIMUM_QUESTIONS) is True
    assert check_stopping(hopeless_probs, MAXIMUM_QUESTIONS + 3) is True


def test_boundary_exactly_65_and_gap_15():
    probs = {"a": 0.65, "b": 0.50, "c": 0.0}
    assert check_stopping(probs, MINIMUM_QUESTIONS) is True
    probs = {"a": 0.64, "b": 0.50, "c": 0.0}
    assert check_stopping(probs, MINIMUM_QUESTIONS) is False
