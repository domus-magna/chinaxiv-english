from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.validators import translation_gate
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


def test_translation_gate_allows_small_flagged_ratio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    translated_dir = Path("data/translated")
    translated_dir.mkdir(parents=True, exist_ok=True)

    # One clean translation
    (translated_dir / "clean.json").write_text(
        json.dumps(
            {
                "id": "paper-clean",
                "title_en": "Clean Sample",
                "abstract_en": "This abstract is entirely English and should pass QA filters easily.",
                "body_en": " ".join(["All content here is valid."] * 10),
            }
        ),
        encoding="utf-8",
    )
    # One flagged translation containing Chinese characters
    (translated_dir / "flagged.json").write_text(
        json.dumps(
            {
                "id": "paper-flagged",
                "title_en": "Flagged Sample",
                "abstract_en": "Contains 中文 characters that should trigger the QA filter.",
                "body_en": " ".join(["Mixing languages 中文 should fail QA."] * 5),
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        translation_gate,
        "get_config",
        lambda: {
            "validation_thresholds": {
                "translation": {
                    "max_flagged_ratio": 0.6,
                    "max_flagged_absolute": 10,
                }
            }
        },
    )

    summary = run_translation_gate(output_path="reports/translation_report.json")
    assert summary.total == 2
    assert summary.flagged == 1
    assert summary.passed == 1
