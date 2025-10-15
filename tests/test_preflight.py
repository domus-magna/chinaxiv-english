from __future__ import annotations

import os


def test_env_diagnose_imports():
    # Just ensure module imports and main symbols exist
    from src.tools import env_diagnose  # noqa: F401


def test_preflight_offline(tmp_path, monkeypatch):
    # Simulate missing binaries and keys to ensure preflight can run and fail cleanly
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("BRIGHTDATA_API_KEY", raising=False)
    monkeypatch.delenv("BRIGHTDATA_ZONE", raising=False)

    # Ensure site dirs exist so writer doesn't fail
    (tmp_path / "site/stats/validation").mkdir(parents=True, exist_ok=True)
    os.chdir(tmp_path)

    from src.tools.env_diagnose import write_preflight_report

    report = {
        "pass": False,
        "checks": {
            "env_vars": {
                "OPENROUTER_API_KEY": False,
                "BRIGHTDATA_API_KEY": False,
                "BRIGHTDATA_ZONE": False,
            },
            "openrouter_api": {"ok": False},
            "brightdata": {"available": False, "status_code": None, "error": "no creds"},
            "binaries": {"ocrmypdf": {"ok": False}, "tesseract": {"ok": False}},
            "disk": {"ok": True, "free_gb": 2.0, "min_gb": 1.0},
        },
    }
    write_preflight_report(report)

    assert os.path.exists("reports/preflight_report.json")
    assert os.path.exists("reports/preflight_report.md")

