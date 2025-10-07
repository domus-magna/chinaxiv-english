from __future__ import annotations

import argparse
import sys

from .utils import http_get, log, openrouter_headers, get_config, load_dotenv


def check_oai(base_url: str) -> bool:
    try:
        r = http_get(base_url, params={"verb": "Identify"})
        ok = r.ok and "<Identify>" in r.text
        log(f"OAI Identify: {'OK' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        log(f"OAI Identify failed: {e}")
        return False


def check_openrouter(connect_only: bool = True) -> bool:
    # Basic check: API key present (from env or .env) and model list endpoint reachable
    try:
        # ensure .env is loaded inside header helper
        headers = openrouter_headers()
    except Exception:
        # try loading .env explicitly and retry once
        try:
            load_dotenv()
            headers = openrouter_headers()
        except Exception as e:
            log(f"OPENROUTER_API_KEY not set or invalid: {e}")
            return False
    try:
        # models endpoint is inexpensive and avoids billable completions
        r = http_get("https://openrouter.ai/api/v1/models", headers=headers)
        ok = r.ok
        log(f"OpenRouter models: {'OK' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        log(f"OpenRouter check failed: {e}")
        return False


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Health checks for OAI and OpenRouter."
    )
    parser.add_argument("--skip-oai", action="store_true")
    parser.add_argument("--skip-openrouter", action="store_true")
    args = parser.parse_args()

    cfg = get_config()
    oai_ok = True
    or_ok = True

    if not args.skip_oai:
        base = (cfg.get("oai") or {}).get("base_url", "https://www.chinaxiv.org/oai2")
        oai_ok = check_oai(base)
    if not args.skip_openrouter:
        or_ok = check_openrouter()

    ok = oai_ok and or_ok
    log(f"HEALTH: {'OK' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    run_cli()
