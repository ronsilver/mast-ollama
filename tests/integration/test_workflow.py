"""Integration tests for Workflow stage chaining."""

from __future__ import annotations

from mast.validation.schemas import Verdict, WorkflowResult, WorkflowStageResult


class TestWorkflowStageResult:
    def test_minimal(self) -> None:
        r = WorkflowStageResult.model_validate(
            {
                "stage": "debate",
                "verdict": "accept",
                "confidence": 0.8,
                "inputThought": "in",
                "outputThought": "out",
            }
        )
        assert r.stage == "debate"
        assert r.verdict == Verdict.ACCEPT
        assert r.input_thought == "in"

    def test_with_error(self) -> None:
        r = WorkflowStageResult.model_validate(
            {
                "stage": "brainstorm",
                "verdict": "accept",
                "confidence": 0.0,
                "inputThought": "in",
                "outputThought": "in",
                "error": "Model not available",
            }
        )
        assert r.error == "Model not available"

    def test_with_revision(self) -> None:
        r = WorkflowStageResult.model_validate(
            {
                "stage": "kalman",
                "verdict": "revise",
                "confidence": 0.6,
                "suggestedRevision": "revised thought",
                "inputThought": "original",
                "outputThought": "revised thought",
            }
        )
        assert r.suggested_revision == "revised thought"


class TestWorkflowResult:
    def test_single_stage(self) -> None:
        stage = {
            "stage": "debate",
            "verdict": "accept",
            "confidence": 0.9,
            "inputThought": "in",
            "outputThought": "out",
        }
        wf = WorkflowResult.model_validate(
            {
                "stages": [stage],
                "finalThought": "out",
                "totalStages": 1,
            }
        )
        assert wf.total_stages == 1
        assert wf.final_thought == "out"

    def test_multi_stage(self) -> None:
        stages = [
            {
                "stage": "brainstorm",
                "verdict": "revise",
                "confidence": 0.7,
                "inputThought": "t1",
                "outputThought": "t2",
                "suggestedRevision": "t2",
            },
            {
                "stage": "actor_critic",
                "verdict": "accept",
                "confidence": 1.0,
                "inputThought": "t2",
                "outputThought": "t3",
            },
            {
                "stage": "kalman",
                "verdict": "accept",
                "confidence": 0.95,
                "inputThought": "t3",
                "outputThought": "t4",
            },
        ]
        wf = WorkflowResult.model_validate(
            {
                "stages": stages,
                "finalThought": "t4",
                "totalStages": 3,
            }
        )
        assert len(wf.stages) == 3
        assert wf.stages[1].stage == "actor_critic"
        assert wf.stages[2].output_thought == "t4"
