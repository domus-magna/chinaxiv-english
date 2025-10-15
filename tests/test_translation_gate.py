from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.validators.translation_gate import run_translation_gate

ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_FIXTURE = ROOT / "tests/fixtures/translation/sample_translation.json"


def test_translation_gate_fails_with_no_translations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = run_translation_gate(output_path="reports/translation_report.json")
    assert summary.total == 0
    assert summary.flagged == 0


def test_translation_gate_passes_with_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    translated_dir = Path("data/translated")
    translated_dir.mkdir(parents=True, exist_ok=True)

    dest = translated_dir / "sample_translation.json"
    shutil.copy(TRANSLATION_FIXTURE, dest)

    summary = run_translation_gate(output_path="reports/translation_report.json")
    assert summary.total == 1
    assert summary.flagged == 0
    assert summary.passed == 1
