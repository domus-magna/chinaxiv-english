#!/usr/bin/env python3
"""Populate fixture data for validation gates when real artifacts are absent."""
from __future__ import annotations

import shutil
from pathlib import Path

HARVEST_FIXTURE = Path("tests/fixtures/harvest/records_sample.json")
HARVEST_PDF_FIXTURE = Path("tests/fixtures/harvest/sample.pdf")
TRANSLATION_FIXTURE = Path("tests/fixtures/translation/sample_translation.json")


def copy_fixture(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)


def ensure_harvest_fixtures() -> bool:
    dest_dir = Path("data/records")
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = list(dest_dir.glob("*.json"))
    if existing:
        return False

    copy_fixture(HARVEST_FIXTURE, dest_dir / HARVEST_FIXTURE.name)

    pdf_dest = Path("data/pdfs/sample.pdf")
    if not pdf_dest.exists():
        copy_fixture(HARVEST_PDF_FIXTURE, pdf_dest)
    return True


def ensure_translation_fixtures() -> bool:
    dest_dir = Path("data/translated")
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = list(dest_dir.glob("*.json"))
    if existing:
        return False

    copy_fixture(TRANSLATION_FIXTURE, dest_dir / TRANSLATION_FIXTURE.name)
    return True


def main() -> None:
    harvest_created = ensure_harvest_fixtures()
    translation_created = ensure_translation_fixtures()

    if harvest_created:
        print("Seeded harvest fixtures for validation gate")
    if translation_created:
        print("Seeded translation fixtures for validation gate")
    if not harvest_created and not translation_created:
        print("Existing data detected; no fixtures copied")


if __name__ == "__main__":
    main()
