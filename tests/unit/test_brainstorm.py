"""Unit tests for Brainstorm response parsing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mast.validation.schemas import BrainstormIdea, BrainstormResult


class TestBrainstormIdea:
    def test_minimal(self) -> None:
        idea = BrainstormIdea.model_validate({"idea": "Use caching layer"})
        assert idea.idea == "Use caching layer"
        assert idea.rationale == ""
        assert idea.angle == ""

    def test_full(self) -> None:
        idea = BrainstormIdea.model_validate(
            {
                "idea": "Circuit breaker pattern",
                "rationale": "Handles failure gracefully",
                "angle": "technical",
                "model": "llama3:8b",
                "latencyMs": 1500,
            }
        )
        assert idea.angle == "technical"
        assert idea.latency_ms == 1500

    def test_idea_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BrainstormIdea.model_validate({"idea": "X" * 401})

    def test_rationale_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BrainstormIdea.model_validate({"idea": "test", "rationale": "X" * 121})


class TestBrainstormResult:
    def test_minimal(self) -> None:
        result = BrainstormResult.model_validate({"ideas": [], "synthesis": "no ideas"})
        assert result.synthesis == "no ideas"
        assert result.top_ideas == []

    def test_with_ideas(self) -> None:
        result = BrainstormResult.model_validate(
            {
                "ideas": [
                    {"idea": "Use Redis cache", "rationale": "fast", "angle": "performance"},
                    {"idea": "Use CDN", "rationale": "global reach", "angle": "scalability"},
                ],
                "synthesis": "Combine Redis + CDN",
                "topIdeas": ["Redis cache", "CDN"],
                "synthLatencyMs": 2000,
            }
        )
        assert len(result.ideas) == 2
        assert result.top_ideas == ["Redis cache", "CDN"]
        assert result.synth_latency_ms == 2000
