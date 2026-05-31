"""Unit tests for Kalman Convergence parsing and KF numerical stability."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mast.validation.schemas import KalmanResult, KalmanScoreEntry, Verdict


class TestKalmanScoreEntry:
    def test_minimal(self) -> None:
        entry = KalmanScoreEntry.model_validate({"score": 0.8, "confidence": 0.9})
        assert entry.score == 0.8
        assert entry.confidence == 0.9
        assert entry.rationale == ""

    def test_full(self) -> None:
        entry = KalmanScoreEntry.model_validate(
            {
                "score": 0.5,
                "confidence": 0.6,
                "rationale": "Acceptable but lacks detail",
                "model": "mistral:7b",
                "latencyMs": 800,
            }
        )
        assert entry.rationale == "Acceptable but lacks detail"
        assert entry.latency_ms == 800

    def test_score_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            KalmanScoreEntry.model_validate({"score": 1.5, "confidence": 0.5})

    def test_confidence_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            KalmanScoreEntry.model_validate({"score": 0.5, "confidence": -0.1})

    def test_rationale_max_length(self) -> None:
        with pytest.raises(ValidationError):
            KalmanScoreEntry.model_validate(
                {
                    "score": 0.5,
                    "confidence": 0.5,
                    "rationale": "X" * 81,
                }
            )


class TestKalmanResult:
    def test_minimal(self) -> None:
        result = KalmanResult.model_validate(
            {
                "scorers": [],
                "xFinal": 0.5,
                "PFinal": 1.0,
                "converged": False,
                "triggers": [],
                "verdict": "revise",
                "confidence": 0.5,
            }
        )
        assert result.verdict == Verdict.REVISE
        assert result.converged is False

    def test_accept_verdict(self) -> None:
        result = KalmanResult.model_validate(
            {
                "scorers": [],
                "xFinal": 0.85,
                "PFinal": 0.01,
                "converged": True,
                "triggers": [],
                "verdict": "accept",
                "confidence": 0.99,
            }
        )
        assert result.verdict == Verdict.ACCEPT
        assert result.converged is True

    def test_with_scorers(self) -> None:
        result = KalmanResult.model_validate(
            {
                "scorers": [
                    {"score": 0.9, "confidence": 0.8, "rationale": "good"},
                    {"score": 0.7, "confidence": 0.6, "rationale": "ok"},
                ],
                "xFinal": 0.8,
                "PFinal": 0.03,
                "converged": True,
                "triggers": ["K1:high_divergence"],
                "verdict": "accept",
                "confidence": 0.97,
            }
        )
        assert len(result.scorers) == 2
        assert result.triggers == ["K1:high_divergence"]


class TestKFState:
    def test_kf_joseph_form_positive_definite(self) -> None:
        from mast.agents.kalman import _KFState

        state = _KFState()
        for _ in range(50):
            state.update(z=0.8, confidence=0.99)
        assert state.P >= 0.0
        assert 0.0 <= state.x <= 1.0

    def test_kf_converges_with_high_confidence(self) -> None:
        from mast.agents.kalman import _KFState

        state = _KFState()
        for _ in range(10):
            state.update(z=0.85, confidence=0.95)
        assert state.P < 0.1
        assert abs(state.x - 0.85) < 0.1

    def test_kf_divergence_detected(self) -> None:
        from mast.agents.kalman import _KFState

        state = _KFState()
        state.update(z=0.1, confidence=0.9)
        state.update(z=0.9, confidence=0.9)
        assert any(i > 0.5 for i in state.innovations)

    def test_kf_no_divergence_on_consistent_scores(self) -> None:
        from mast.agents.kalman import _KFState

        state = _KFState()
        for _ in range(5):
            state.update(z=0.6, confidence=0.7)
        assert not any(i > 0.5 for i in state.innovations)

    def test_kf_never_negative_P(self) -> None:
        from mast.agents.kalman import _KFState

        state = _KFState()
        for _ in range(100):
            state.update(z=0.5, confidence=0.1)
        assert state.P >= 0.0
