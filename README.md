# 🧠 MAST-Ollama

**Multi-Agent Sequential Thinking with Ollama** — Active validation layer for the [MCP sequential-thinking](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) server.

Drop-in Python replacement that challenges each reasoning step with local Ollama models before returning the result to the calling LLM.

Available validation modes:
- **Critic + Judge** (debate mode): a Critic identifies flaws, a Judge synthesizes a verdict
- **De Bono Six Thinking Hats** (debono mode): 7 sequential hats refine a working document through facts, creativity, benefits, risks, and intuition into a final verdict

## Why

The upstream `sequential-thinking` MCP server is passive — it only persists thoughts. If the main LLM hallucinates or anchors on a bad assumption, nothing corrects it. MAST adds an active validation loop using small local models (3B–8B), keeping reasoning private and cost-free.

## Quick Start

### Prerequisites

- [Ollama](https://ollama.com) running locally
- Pull the required models:
  ```bash
  ollama pull mistral:7b-instruct
  ollama pull deepseek-r1:8b
  ```

### Run with uvx (recommended)

```bash
uvx --from git+https://github.com/<user>/mast-ollama.git mast-server
```

### Verify setup

```bash
mast-server --doctor
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mast-ollama": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/<user>/mast-ollama.git",
        "mast-server"
      ],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "CRITIC_MODEL": "mistral:7b-instruct",
        "JUDGE_MODEL": "deepseek-r1:8b",
        "MAST_MODE": "debate"
      }
    }
  }
}
```

## Modes

| Mode | Behavior | Extra latency |
|---|---|---|
| `passive` | Identical to upstream sequential-thinking | 0 ms |
| `validate` | Critic only — issues + strengths | ~1× critic model |
| `debate` | Critic + Judge — verdict + suggested revision | ~2× |
| `debono` | De Bono Six Hats pipeline (Blue → White → Green → Yellow → Black → Red → Blue) — progressive document refinement + verdict | ~5s (7 sequential hats) |

## Tools

### `sequentialthinking` (drop-in compatible)

Same as upstream + optional MAST fields:
- `mode`: `"passive" | "validate" | "debate" | "debono"` — overrides server default for this step
- `skipValidation`: bypass Critic/Judge for this specific step

### `mast_debate` (extended)

Forces debate mode by default. Accepts per-call model overrides:
- `criticModel`, `judgeModel` — debate mode
- `debonoPrimaryModel`, `debonoCreativeModel` — debono mode (overrides the env defaults)

## De Bono Six Hats Mode

When `MAST_MODE=debono`, each reasoning step passes through 7 sequential hats:

| Step | Hat | Role | Default Model |
|---|---|---|---|
| 1 | 🔵 Blue Open | Define problem, set objective | `qwen2.5:3b` |
| 2 | ⚪ White | Facts, data, unknowns | `qwen2.5:3b` |
| 3 | 🟢 Green | Creative alternatives, lateral thinking | `qwen2.5:1.5b` |
| 4 | 🟡 Yellow | Benefits, value, prune weak ideas | `qwen2.5:3b` |
| 5 | ⚫ Black | Risks, mitigations, harden plan | `qwen2.5:3b` |
| 6 | 🔴 Red | Gut feeling, intuition (30s) | `qwen2.5:1.5b` |
| 7 | 🔵 Blue Close | Synthesize, verdict, suggested revision | `qwen2.5:3b` |

Each hat receives and transforms a progressive working document. Red hat can be disabled via `DEBONO_SKIP_RED=true`.

## Environment Variables

| Environment variable | Default | Description |
|---|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server endpoint |
| `CRITIC_MODEL` | `mistral:7b-instruct` | Critic model (debate mode) |
| `JUDGE_MODEL` | `deepseek-r1:8b` | Judge model (debate mode) |
| `MAST_MODE` | `debate` | Default mode |
| `MAST_TIMEOUT_MS` | `15000` | Per-call Ollama timeout |
| `MAST_CACHE_TTL_S` | `300` | Validation cache TTL (seconds) |
| `MAST_LOG_LEVEL` | `INFO` | Log level |
| `DEBONO_BLUE_OPEN_MODEL` | `qwen2.5:3b` | Blue Open hat model |
| `DEBONO_WHITE_MODEL` | `qwen2.5:3b` | White hat model |
| `DEBONO_GREEN_MODEL` | `qwen2.5:1.5b` | Green hat model |
| `DEBONO_YELLOW_MODEL` | `qwen2.5:3b` | Yellow hat model |
| `DEBONO_BLACK_MODEL` | `qwen2.5:3b` | Black hat model |
| `DEBONO_RED_MODEL` | `qwen2.5:1.5b` | Red hat model |
| `DEBONO_BLUE_CLOSE_MODEL` | `qwen2.5:3b` | Blue Close hat model |
| `DEBONO_SKIP_RED` | `false` | Skip Red hat for technical tasks |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/unit/ tests/integration/ -v

# Lint
ruff check src/ tests/
mypy src/
```

## Architecture

```
LLM Client → MCP sequentialthinking tool
                    ↓
              MAST Server
              ├── _upstream.py  (1:1 port of lib.ts)
              ├── agents/
              │   ├── critic.py  → Ollama (Critic)   [debate mode]
              │   ├── judge.py   → Ollama (Judge)     [debate mode]
              │   └── debono.py  → Ollama x7 hats     [debono mode]
              ├── validation/
              │   ├── orchestrator.py
              │   ├── cache.py
              │   └── schemas.py
              └── prompts/
                  ├── debate/
                  │   ├── critic.md
                  │   └── judge.md
                  └── debono/
                      ├── blue_open.md
                      ├── white.md
                      ├── green.md
                      ├── yellow.md
                      ├── black.md
                      ├── red.md
                      └── blue_close.md
```

## License

MIT — based on [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) (MIT).
