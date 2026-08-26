import pytest
from app.engine.decision import (
    evaluate_decision,
    Decision,
    RiskLevel,
    ALLOW_THRESHOLD,
    REVIEW_THRESHOLD,
    BLOCK_THRESHOLD,
)


class TestDecisionEngine:
    """Tests deterministic policy threshold evaluation and boundary handling."""

    @pytest.mark.parametrize(
        "score,expected_decision,expected_level",
        [
            # Boundary 0 -> ALLOW
            (0, Decision.ALLOW, RiskLevel.LOW),
            (10, Decision.ALLOW, RiskLevel.LOW),
            # Boundary 39 -> ALLOW
            (39, Decision.ALLOW, RiskLevel.LOW),
            # Boundary 40 -> REVIEW
            (40, Decision.REVIEW, RiskLevel.MEDIUM),
            (55, Decision.REVIEW, RiskLevel.MEDIUM),
            # Boundary 69 -> REVIEW
            (69, Decision.REVIEW, RiskLevel.MEDIUM),
            # Boundary 70 -> BLOCK
            (70, Decision.BLOCK, RiskLevel.HIGH),
            (85, Decision.BLOCK, RiskLevel.HIGH),
            # Boundary 100 -> BLOCK
            (100, Decision.BLOCK, RiskLevel.HIGH),
        ],
    )
    def test_decision_and_risk_level_boundaries(self, score, expected_decision, expected_level):
        """Verify strict decision action and risk level assignment across threshold boundaries."""
        decision, risk_level = evaluate_decision(score)
        assert decision == expected_decision
        assert risk_level == expected_level

    def test_configured_constants_consistency(self):
        """Verify that policy constants match architectural definitions."""
        assert ALLOW_THRESHOLD == 39
        assert REVIEW_THRESHOLD == 69
        assert BLOCK_THRESHOLD == 70

    @pytest.mark.parametrize(
        "invalid_score",
        [
            -1,
            -10,
            101,
            250,
            float("nan"),
            float("inf"),
            float("-inf"),
        ],
    )
    def test_invalid_score_raises_value_error(self, invalid_score):
        """Verify ValueError is raised for scores outside [0, 100], NaN, or infinite."""
        with pytest.raises(ValueError):
            evaluate_decision(invalid_score)

    @pytest.mark.parametrize(
        "invalid_type",
        [
            "50",
            None,
            [50],
            True,
            False,
        ],
    )
    def test_invalid_type_raises_type_error(self, invalid_type):
        """Verify TypeError is raised for non-numeric types."""
        with pytest.raises(TypeError):
            evaluate_decision(invalid_type)

    def test_deterministic_decision_repeatability(self):
        """Verify decision evaluation is purely functional and deterministic."""
        for score in [0, 39, 40, 69, 70, 100]:
            results = [evaluate_decision(score) for _ in range(50)]
            assert len(set(results)) == 1
