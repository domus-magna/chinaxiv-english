# Proxy/VPN Support — Review and Next Steps

This document summarizes the proxy/VPN implementation, the resilience improvements just applied, and concrete next steps to fully validate and operate behind geo-blocks.

## Summary
- Proxies can be supplied via environment variables (`HTTP(S)_PROXY`, `SOCKS5_PROXY`) or via `src/config.yaml` (`proxy.enabled: true`).
- All outbound HTTP requests (OAI harvest, landing-page scrapes, OpenRouter translation) support routing via proxy.
- We improved NO_PROXY handling, added SOCKS support via `PySocks`, increased timeouts when proxied, and updated docs for `socks5h` and NO_PROXY.

## What’s Good
- Centralized proxy logic in `get_proxies()` with clear precedence: env → config.
- Consistent application to `http_get()` (harvest, scraping) and OpenRouter POST (translation).
- Correct OAI endpoint in config: `https://chinaxiv.org/oai/OAIHandler`.
- Documentation added (`docs/PROXY_SETUP.md`) with concrete examples and troubleshooting.

## Gaps & Risks (Before Patch)
- SOCKS required extra dependency; not guaranteed installed.
- Passing `proxies=` directly bypassed `NO_PROXY`, so "bypass hosts" didn’t work as expected.
- Preferable to use `socks5h://` for DNS-over-proxy (avoid leaks); docs didn’t say so.
- Uniform (shorter) timeouts may be too aggressive for proxied routes.

## Changes Just Applied (Resilience)
- Requirements: added `PySocks==1.7.1` for SOCKS support.
- NO_PROXY honored for env proxies:
  - When proxies come from env/.env, we do NOT pass `proxies=` to `requests`.
  - We rely on `requests` trust_env, which respects `NO_PROXY`.
- Explicit proxies only when enabled in config.yaml:
  - If `proxy.enabled: true`, we pass `proxies=` explicitly (overriding env and NO_PROXY by design).
- Timeouts with proxies:
  - If any proxy is active (env or config), increase connect/read timeouts from `(10, 60)` → `(15, 90)`.
- Docs (`docs/PROXY_SETUP.md`):
  - Recommend `socks5h://` for SOCKS (DNS over proxy).
  - Added `NO_PROXY` usage example.
  - Clarified that `PySocks` is included.

## Code Pointers
- `src/utils.py`:
  - `get_proxies() -> (proxies, source)`: returns proxies and source one of `env|config|none`.
  - `http_get(...)`: uses explicit `proxies=` only for `source=='config'`; otherwise relies on trust_env. Applies longer timeouts when proxied.
- `src/translate.py`:
  - `openrouter_translate(...)`: matches `http_get` behavior for proxies and timeouts.
- `src/config.yaml`:
  - `oai.base_url: https://chinaxiv.org/oai/OAIHandler`
  - `proxy:` section present but disabled by default.
- `requirements.txt`: 
  - `PySocks==1.7.1` added.

## How to Use
- Env-based (recommended): add to `.env` at repo root
  ```bash
  # HTTP/S proxy
  HTTPS_PROXY=http://127.0.0.1:1087
  # SOCKS proxy (DNS via proxy)
  SOCKS5_PROXY=socks5h://127.0.0.1:1080
  # Optional: bypass proxy for these hosts
  NO_PROXY=localhost,127.0.0.1,openrouter.ai
  ```
  Run normally: `make dev`, `python -m src.harvest_oai ...`, etc.

- Config-based (explicit override): in `src/config.yaml`
  ```yaml
  proxy:
    enabled: true
    http:  "http://127.0.0.1:1087"
    https: "http://127.0.0.1:1087"
  ```
  This forces all requests through the proxy (bypassing NO_PROXY) and is useful in tightly controlled networks.

## Test Plan (Proxy Focus)
- Env-only HTTP proxy
  - Set `HTTPS_PROXY=http://127.0.0.1:PORT`; leave `proxy.enabled=false`.
  - `curl 'https://chinaxiv.org/oai/OAIHandler?verb=Identify'` works.
  - `NO_PROXY=localhost,openrouter.ai` keeps OpenRouter direct if desired.
- Env-only SOCKS proxy
  - Set `SOCKS5_PROXY=socks5h://127.0.0.1:PORT`.
  - Verify Identify works and translation POST succeeds.
- Config-only proxy
  - Set `proxy.enabled=true` with http/https values.
  - Confirm requests route via config proxy regardless of env/NO_PROXY.
- Timeout behavior
  - Simulate slower proxy; confirm operations succeed with increased timeouts.

## Suggested Follow-ups
- Add small unit tests:
  - Env-only proxies: ensure `http_get`/`openrouter_translate` do NOT pass `proxies=`.
  - Config-only proxies: ensure `proxies=` is passed explicitly.
  - SOCKS precedence over HTTP/HTTPS when both present.
- Configurable timeouts per environment in `config.yaml` (optional).
- OAI base URL fallback list in config (try https → http → alternate host).

## Quick Commands
- Health with proxy from `.env`:
  ```bash
  make health
  # or
  HTTPS_PROXY=http://127.0.0.1:1087 python -m src.health
  ```
- Harvest with explicit base URL:
  ```bash
  python -m src.harvest_oai --base-url https://chinaxiv.org/oai/OAIHandler --from 2024-11-01 --until 2024-11-01
  ```
- Full local run (serves site):
  ```bash
  make dev DEV_LIMIT=5 PORT=8001
  # or specify alternate model
  make dev DEV_LIMIT=5 MODEL=z-ai/glm-4.5-air PORT=8001
  ```

## Acceptance Criteria (Proxy)
- Identify succeeds via proxy when direct access is blocked.
- Translation requests succeed via proxy, or pipeline falls back to dry-run and still renders site.
- NO_PROXY works with env-defined proxies; config proxies override NO_PROXY by design.
- SOCKS proxies work out-of-the-box (PySocks present); `socks5h://` resolves via proxy.
