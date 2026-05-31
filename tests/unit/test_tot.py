"""Unit tests for Tree of Thoughts response parsing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mast.validation.schemas import ToTBranch, ToTResult


class TestToTBranch:
    def test_minimal(self) -> None:
        branch = ToTBranch.model_validate({"nextStep": "Analyze edge case"})
        assert branch.next_step == "Analyze edge case"
        assert branch.rationale == ""

    def test_full(self) -> None:
        branch = ToTBranch.model_validate(
            {
                "nextStep": "Check authentication flow",
                "rationale": "Most likely failure point",
                "model": "qwen2.5:7b",
                "voterScore": 0.85,
                "voterRationale": "Well-reasoned approach",
            }
        )
        assert branch.voter_score == 0.85
        assert branch.voter_rationale == "Well-reasoned approach"

    def test_next_step_max_length(self) -> None:
        with pytest.raises(ValidationError):
            ToTBranch.model_validate({"nextStep": "X" * 601})

    def test_rationale_max_length(self) -> None:
        with pytest.raises(ValidationError):
            ToTBranch.model_validate({"nextStep": "t", "rationale": "X" * 121})


class TestToTResult:
    def _make_branch(self, score: float = 0.5) -> dict[str, object]:
        return {"nextStep": f"Branch {score}", "rationale": "test", "voterScore": score}

    def test_no_branches(self) -> None:
        result = ToTResult.model_validate(
            {
                "branches": [],
                "selectedBranch": None,
                "voterScores": [],
            }
        )
        assert result.selected_branch is None
        assert result.voter_scores == []

    def test_with_branches(self) -> None:
        branches = [self._make_branch(0.3), self._make_branch(0.9)]
        result = ToTResult.model_validate(
            {
                "branches": branches,
                "selectedBranch": branches[1],
                "voterScores": [{"index": 0, "score": 0.3}, {"index": 1, "score": 0.9}],
            }
        )
        assert len(result.branches) == 2
        assert result.selected_branch is not None
        assert result.selected_branch.voter_score == 0.9
