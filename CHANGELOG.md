# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `mode: actor_critic` — Actor-Critic iterative refinement loop
- `mode: brainstorm` — Parallel divergence + synthesis convergence
- `mode: tot` — Tree of Thoughts branch generation + voting
- `mode: kalman` — Kalman Convergence Bayesian quality fusion
- `mode: workflow` — Multi-stage pipeline of chained modes
- `agents/actor_critic.py` — ActorCriticOrchestrator with configurable rounds
- `agents/brainstorm.py` — BrainstormOrchestrator with parallel N generators
- `agents/tot.py` — TreeOfThoughtsOrchestrator with branch scoring
- `agents/kalman.py` — KalmanConvergenceLayer with Joseph form KF
- `prompts/brainstorm/` — idea_generator.md, synthesizer.md
- `prompts/tot/` — branch_generator.md, voter.md
- `prompts/kalman/` — scorer.md
- `ACTOR_CRITIC_MAX_ROUNDS` — max iteration rounds (default: 3)
- `BRAINSTORM_MODELS`, `BRAINSTORM_SYNTH_MODEL` — brainstorm config
- `TOT_BRANCH_MODELS`, `TOT_VOTER_MODEL` — ToT config
- `KALMAN_SCORER_MODELS`, `KALMAN_P_THRESHOLD`, `KALMAN_ACCEPT_THRESHOLD` — kalman config
- `MAST_WORKFLOW_STAGES` — workflow pipeline definition
- Tests — `test_actor_critic.py`, `test_brainstorm.py`, `test_tot.py`, `test_kalman.py`
- Docs — updated strategies.md, README with env vars and workflows table

### Changed

- `config.py` — MastMode extended with 5 new modes, 11 new config fields, 4 properties
- `schemas.py` — 10 new Pydantic models, 5 new fields on MastOutput
- `orchestrator.py` — 5 new mode branches in run(), _run_workflow() method
- `_mast_debate_tool.py` — description covers all 7 strategies

## [0.1.0] - 2025-03-27

### Added

- Initial release — drop-in Python replacement for sequential-thinking MCP
- Modes: `passive`, `validate`, `debate`
- Critic agent (mistral:7b-instruct) — identifies reasoning flaws
- Judge agent (deepseek-r1:8b) — synthesizes verdict + suggested revision
- LRU+TLL cache for validation results
- Structured JSON output with Ollama format parameter
- Prompt injection defense via XML data-tags
- Upstream parity — 1:1 port of SequentialThinkingServer from TypeScript
- CI — GitHub Actions with ruff, mypy, pytest
