import math
import pytest
from app.engine.scoring import calculate_risk_score


class TestRiskScoreCalculation:
    """Tests probability to 0-100 deterministic risk score conversion."""

    @pytest.mark.parametrize(
        "prob,expected_score",
        [
            (0.0, 0),
            (0.25, 25),
            (0.50, 50),
            (0.999, 100),
            (1.0, 100),
            (0.394, 39),
            (0.395, 40),
            (0.694, 69),
            (0.695, 70),
            (0.004, 0),
            (0.005, 1),
        ],
    )
    def test_valid_probability_mappings(self, prob, expected_score):
        """Verify exact deterministic integer output for valid probabilities."""
        score = calculate_risk_score(prob)
        assert score == expected_score
        assert isinstance(score, int)

    def test_floating_point_edge_clamping(self):
        """Verify that micro floating-point variances are safely clamped."""
        assert calculate_risk_score(1.0000000000000002) == 100
        assert calculate_risk_score(0.9999999999999999) == 100
        assert calculate_risk_score(1e-15) == 0
        assert calculate_risk_score(-1e-15) == 0

    @pytest.mark.parametrize(
        "invalid_prob",
        [
            -0.1,
            -1.0,
            -0.0001,
            1.01,
            1.5,
            100.0,
            float("nan"),
            float("inf"),
            float("-inf"),
        ],
    )
    def test_invalid_probabilities_raise_value_error(self, invalid_prob):
        """Verify ValueError is raised for negative, out-of-range, NaN, and Infinite values."""
        with pytest.raises(ValueError):
            calculate_risk_score(invalid_prob)

    @pytest.mark.parametrize(
        "invalid_type",
        [
            "0.5",
            None,
            [0.5],
            {"prob": 0.5},
            True,
            False,
        ],
    )
    def test_invalid_types_raise_type_error(self, invalid_type):
        """Verify TypeError is raised for non-numeric types."""
        with pytest.raises(TypeError):
            calculate_risk_score(invalid_type)

    def test_deterministic_repeated_execution(self):
        """Verify consistent idempotency across repeated invocations."""
        probabilities = [0.0, 0.1234, 0.5, 0.789, 1.0]
        for p in probabilities:
            scores = [calculate_risk_score(p) for _ in range(100)]
            assert len(set(scores)) == 1, f"Non-deterministic score for probability {p}"
