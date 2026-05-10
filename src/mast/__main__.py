"""Entry point: python -m mast or mast-server CLI command."""

from __future__ import annotations

import asyncio
import sys

import structlog

from mast.config import config


def _configure_logging() -> None:
    import logging

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    logging.basicConfig(
        level=getattr(logging, config.mast_log_level.upper(), logging.INFO),
        stream=sys.stderr,
    )


def _collect_configured_models() -> list[str]:
    """Return all configured model names based on current MAST_MODE."""
    configured: list[str] = [config.critic_model, config.judge_model]
    if config.mast_mode == "debono":
        configured.extend(
            [
                config.debono_blue_open_model,
                config.debono_white_model,
                config.debono_green_model,
                config.debono_yellow_model,
                config.debono_black_model,
            ]
        )
        if not config.debono_skip_red:
            configured.append(config.debono_red_model)
        configured.append(config.debono_blue_close_model)
    return configured


def _print_model_list(models: list[str]) -> None:
    """Print available models with role tags (CRITIC, JUDGE, DEBONO)."""
    print(f"✅ Reachable. Available models ({len(models)}):", flush=True)
    for m in models:
        tags = []
        if m == config.critic_model:
            tags.append("CRITIC")
        if m == config.judge_model:
            tags.append("JUDGE")
        debono_models = {
            config.debono_blue_open_model,
            config.debono_white_model,
            config.debono_green_model,
            config.debono_yellow_model,
            config.debono_black_model,
        }
        if not config.debono_skip_red:
            debono_models.add(config.debono_red_model)
        debono_models.add(config.debono_blue_close_model)
        if m in debono_models:
            tags.append("DEBONO")
        suffix = f" ← {' | '.join(tags)}" if tags else ""
        print(f"  • {m}{suffix}", flush=True)


async def _doctor() -> None:
    """Validate Ollama connectivity and model availability."""
    from mast.agents.base import OllamaClient

    client = OllamaClient()
    is_cloud = config.ollama_cloud_api_key is not None
    env_label = "☁️  Cloud" if is_cloud else "🏠 Local"

    print("🩺 MAST Doctor", flush=True)
    print(f"  Environment : {env_label}", flush=True)
    print(f"  Ollama URL  : {config.ollama_base_url}", flush=True)
    print(f"  Mode        : {config.mast_mode}", flush=True)
    print("", flush=True)

    models = await client.list_models()
    await client.aclose()

    if not models:
        if is_cloud:
            print("❌ Cannot reach Ollama Cloud — check OLLAMA_BASE_URL and API key", flush=True)
        else:
            print("❌ Cannot reach Ollama — is it running?", flush=True)
        sys.exit(1)

    _print_model_list(models)

    configured = _collect_configured_models()
    missing = [m for m in set(configured) if m not in models]

    if missing:
        print("", flush=True)
        if is_cloud:
            print(
                "⚠️  Models not found on cloud. Check ollama.com/search?c=cloud:",
                flush=True,
            )
        else:
            print("⚠️  Missing models. Pull them with:", flush=True)
        for m in missing:
            print(f"  {m}", flush=True)
        sys.exit(1)
    print("", flush=True)
    print("✅ All required models available. Ready to run!", flush=True)


def main() -> None:
    _configure_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "--doctor":
        asyncio.run(_doctor())
        return

    from mast.server import run_server

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
