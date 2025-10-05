import os
import json

from src.render import render_site


def test_render_smoke(tmp_path, monkeypatch):
    items = [
        {
            "id": "2025-12345",
            "title_en": "Example Title",
            "abstract_en": "An abstract.",
            "creators": ["Li, Hua"],
            "subjects": ["cs.AI"],
            "date": "2025-10-02",
            "license": {"badge": "CC BY"},
            "source_url": "https://example.org/abs/2025-12345",
            "pdf_url": "https://example.org/pdf/2025-12345.pdf",
        }
    ]
    # Render into tmp site folder by monkeypatching output location
    monkeypatch.chdir(tmp_path)
    # need templates and assets from project root; create minimal mirrors
    from pathlib import Path
    import shutil

    # Resolve project root by test file position
    root = Path(__file__).resolve().parents[1]
    # Copy templates and assets from repo
    shutil.copytree(str(root / "src" / "templates"), "src/templates")
    shutil.copytree(str(root / "assets"), "assets")
    render_site(items)
    assert (tmp_path / "site" / "index.html").exists()
    assert (tmp_path / "site" / "items" / "2025-12345" / "index.html").exists()
