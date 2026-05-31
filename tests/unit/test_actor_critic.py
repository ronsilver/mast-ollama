"""Unit tests for Actor-Critic response parsing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mast.validation.schemas import (
    ActorCriticResult,
    ActorCriticRound,
    CriticResponse,
    Verdict,
)


class TestActorCriticRound:
    def _make_critic(self) -> CriticResponse:
        return CriticResponse.model_validate(
            {
                "issues": [{"severity": "high", "type": "logic", "detail": "Bad step"}],
                "strengths": ["good context"],
                "summary": "found issue",
            }
        )

    def test_minimal(self) -> None:
        r = ActorCriticRound.model_validate(
            {
                "round": 1,
                "thought": "test thought",
                "critic": self._make_critic(),
                "verdict": "accept",
                "criticLatencyMs": 500,
                "judgeLatencyMs": 0,
            }
        )
        assert r.round == 1
        assert r.thought == "test thought"
        assert r.verdict == Verdict.ACCEPT

    def test_with_revision(self) -> None:
        r = ActorCriticRound.model_validate(
            {
                "round": 2,
                "thought": "original",
                "critic": self._make_critic(),
                "verdict": "revise",
                "suggestedRevision": "revised thought",
                "criticLatencyMs": 400,
                "judgeLatencyMs": 600,
            }
        )
        assert r.suggested_revision == "revised thought"
        assert r.judge_latency_ms == 600

    def test_invalid_verdict_raises(self) -> None:
        with pytest.raises(ValidationError):
            ActorCriticRound.model_validate(
                {
                    "round": 1,
                    "thought": "t",
                    "critic": {"issues": [], "summary": ""},
                    "verdict": "invalid",
                    "criticLatencyMs": 0,
                    "judgeLatencyMs": 0,
                }
            )


class TestActorCriticResult:
    def _make_round(self, verdict: str = "accept") -> dict[str, object]:
        return {
            "round": 1,
            "thought": "t",
            "critic": {"issues": [], "strengths": [], "summary": ""},
            "verdict": verdict,
            "criticLatencyMs": 100,
            "judgeLatencyMs": 0,
        }

    def test_minimal(self) -> None:
        r = ActorCriticResult.model_validate(
            {
                "rounds": [self._make_round()],
                "totalRounds": 1,
                "finalThought": "final",
                "converged": True,
            }
        )
        assert r.total_rounds == 1
        assert r.final_thought == "final"
        assert r.converged is True

    def test_not_converged(self) -> None:
        r = ActorCriticResult.model_validate(
            {
                "rounds": [self._make_round("revise")],
                "totalRounds": 3,
                "finalThought": "best effort",
                "converged": False,
            }
        )
        assert r.converged is False
        assert r.total_rounds == 3

    def test_empty_rounds_is_valid(self) -> None:
        r = ActorCriticResult.model_validate(
            {
                "rounds": [],
                "totalRounds": 0,
                "finalThought": "",
                "converged": False,
            }
        )
        assert r.total_rounds == 0
