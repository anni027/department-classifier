from app.core.classifier import check_stopping


def test_never_finishes_below_minimum():
    confident_probs = {"a": 0.99, "b": 0.005, "c": 0.005}
    for answered in range(0, 8):
        assert check_stopping(confident_probs, answered) is False


def test_finishes_at_or_after_minimum_when_confident():
    probs = {"a": 0.70, "b": 0.50, "c": 0.0}  # not softmax-normalized on purpose, just needs gap math
    probs = {"a": 0.70, "b": 0.20, "c": 0.10}
    assert check_stopping(probs, 8) is True


def test_continues_after_minimum_without_confidence():
    probs = {"a": 0.5, "b": 0.45, "c": 0.05}  # gap too small
    assert check_stopping(probs, 8) is False
    probs = {"a": 0.66, "b": 0.60, "c": 0.0}  # gap too small even though top is high (not >=0.65 gap>=0.15)
    assert check_stopping(probs, 9) is False


def test_always_finishes_at_maximum_regardless_of_confidence():
    hopeless_probs = {"a": 0.34, "b": 0.33, "c": 0.33}
    assert check_stopping(hopeless_probs, 12) is True
    assert check_stopping(hopeless_probs, 15) is True


def test_boundary_exactly_65_and_gap_15():
    probs = {"a": 0.65, "b": 0.50, "c": 0.0}
    assert check_stopping(probs, 8) is True
    probs = {"a": 0.64, "b": 0.50, "c": 0.0}
    assert check_stopping(probs, 8) is False
