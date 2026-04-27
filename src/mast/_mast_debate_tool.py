"""MAST-specific tool definition — superset of upstream sequential-thinking."""

from __future__ import annotations

import copy
from typing import Any

from mast._upstream_tool import SEQUENTIAL_THINKING_INPUT_SCHEMA

MAST_DEBATE_TOOL_DESCRIPTION = """\
Forces debate mode (Critic + Judge) regardless of server defaults.
Use when you want maximum validation quality for a critical reasoning step.
The thought is evaluated by two local Ollama models: a Critic identifies flaws,
and a Judge synthesizes a final verdict (accept / revise / reject) with optional
suggested revision.

Accepts optional criticModel and judgeModel to override the default models per call.
All other parameters are identical to the sequentialthinking tool.\
"""

# Superset schema: all upstream fields + MAST-specific overrides
_base: dict[str, Any] = copy.deepcopy(SEQUENTIAL_THINKING_INPUT_SCHEMA)
_props: dict[str, Any] = dict(_base["properties"])
_props["criticModel"] = {
    "type": "string",
    "description": "Override the Critic model for this call (e.g. 'mistral:7b-instruct')",
}
_props["judgeModel"] = {
    "type": "string",
    "description": "Override the Judge model for this call (e.g. 'mistral:7b-instruct')",
}
_base["properties"] = _props

MAST_DEBATE_INPUT_SCHEMA: dict[str, Any] = _base
