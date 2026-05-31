"""Actor-Critic iterative refinement orchestrator."""

from __future__ import annotations

import structlog

from mast.agents.base import OllamaClient
from mast.agents.critic import CriticAgent
from mast.agents.judge import JudgeAgent
from mast.config import config
from mast.validation.schemas import (
    ActorCriticResult,
    ActorCriticRound,
    IssueSeverity,
    Verdict,
)

log = structlog.get_logger(__name__)

_ESCALATE_SEVERITIES = {IssueSeverity.HIGH, IssueSeverity.MEDIUM}


class ActorCriticOrchestrator:
    def __init__(self, client: OllamaClient) -> None:
        self._critic = CriticAgent(client)
        self._judge = JudgeAgent(client)

    async def run(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        history_summary: str,
        *,
        max_rounds: int | None = None,
        critic_model: str | None = None,
        judge_model: str | None = None,
    ) -> ActorCriticResult:
        effective_max = max_rounds or config.actor_critic_max_rounds
        rounds: list[ActorCriticRound] = []
        current_thought = thought

        for round_idx in range(1, effective_max + 1):
            critic_resp, c_lat = await self._critic.critique(
                thought=current_thought,
                thought_number=thought_number,
                total_thoughts=total_thoughts,
                history_summary=history_summary,
                model=critic_model,
            )

            needs_revision = any(i.severity in _ESCALATE_SEVERITIES for i in critic_resp.issues)

            if not needs_revision:
                rounds.append(
                    ActorCriticRound.model_validate(
                        {
                            "round": round_idx,
                            "thought": current_thought,
                            "critic": critic_resp,
                            "verdict": "accept",
                            "criticLatencyMs": c_lat,
                            "judgeLatencyMs": 0,
                        }
                    )
                )
                break

            judge_resp, j_lat = await self._judge.judge(
                thought=current_thought,
                thought_number=thought_number,
                total_thoughts=total_thoughts,
                history_summary=history_summary,
                critique=critic_resp,
                mode="actor_critic",
                model=judge_model,
            )

            rounds.append(
                ActorCriticRound.model_validate(
                    {
                        "round": round_idx,
                        "thought": current_thought,
                        "critic": critic_resp,
                        "verdict": judge_resp.verdict.value,
                        "suggestedRevision": judge_resp.suggested_revision,
                        "criticLatencyMs": c_lat,
                        "judgeLatencyMs": j_lat,
                    }
                )
            )

            if judge_resp.suggested_revision and judge_resp.verdict != Verdict.REJECT:
                current_thought = judge_resp.suggested_revision
            else:
                break

        final = rounds[-1]
        return ActorCriticResult.model_validate(
            {
                "rounds": rounds,
                "totalRounds": len(rounds),
                "finalThought": final.suggested_revision or final.thought,
                "converged": final.verdict == Verdict.ACCEPT,
            }
        )
