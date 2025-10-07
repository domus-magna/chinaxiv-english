import json
import os
import shutil
import tempfile
from pathlib import Path

from src.pipeline import run_cli as pipeline_run


def _chdir_tmp():
    tmp = tempfile.mkdtemp(prefix="chinaxiv_pipeline_test_")
    cwd = os.getcwd()
    os.chdir(tmp)
    return tmp, cwd


def _restore_tmp(tmp: str, cwd: str):
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)


def test_pipeline_dry_run_skip_selection(monkeypatch):
    tmp, cwd = _chdir_tmp()
    try:
        # Prepare minimal selected item
        os.makedirs("data", exist_ok=True)
        selected = [
            {
                "id": "test-1",
                "title": "Title",
                "abstract": "Abstract",
                "license": {"raw": "", "derivatives_allowed": True},
                "source_url": "",
            }
        ]
        with open("data/selected.json", "w", encoding="utf-8") as f:
            json.dump(selected, f, ensure_ascii=False)

        # Stub os.system calls for render/index/pdf to avoid spawning module subprocesses
        import os as _os
        def _fake_system(cmd: str) -> int:
            # Simulate successful render/index/pdf and create minimal site output
            if "src.render" in cmd or "src.search_index" in cmd or "src.make_pdf" in cmd:
                Path("site").mkdir(parents=True, exist_ok=True)
                (Path("site")/"index.html").write_text("<html></html>", encoding="utf-8")
                return 0
            # Allow select_and_fetch if called (should not be for skip-selection)
            if "src.select_and_fetch" in cmd:
                return 0
            return 0
        monkeypatch.setattr(_os, "system", _fake_system)

        # Invoke pipeline with skip-selection and dry-run so no external calls happen
        import sys
        sys.argv = [
            "pipeline",
            "--skip-selection",
            "--workers",
            "2",
            "--dry-run",
        ]
        pipeline_run()

        # Expect translation artifact and site output
        assert Path("data/translated/test-1.json").exists()
        assert Path("site/index.html").exists()
    finally:
        _restore_tmp(tmp, cwd)


def test_pipeline_records_merge_and_limit(monkeypatch):
    tmp, cwd = _chdir_tmp()
    try:
        # Prepare two small records files
        os.makedirs("data/records", exist_ok=True)
        rec_a = [
            {"id": "test-1", "title": "A1", "abstract": "a", "license": {"raw": ""}},
        ]
        rec_b = [
            {"id": "test-2", "title": "B1", "abstract": "b", "license": {"raw": ""}},
        ]
        with open("data/records/a.json", "w", encoding="utf-8") as f:
            json.dump(rec_a, f, ensure_ascii=False)
        with open("data/records/b.json", "w", encoding="utf-8") as f:
            json.dump(rec_b, f, ensure_ascii=False)

        # Stub os.system to short-circuit render/index/pdf
        import os as _os
        def _fake_system(cmd: str) -> int:
            if "src.render" in cmd or "src.search_index" in cmd or "src.make_pdf" in cmd:
                Path("site").mkdir(parents=True, exist_ok=True)
                (Path("site")/"index.html").write_text("<html></html>", encoding="utf-8")
                return 0
            if "src.select_and_fetch" in cmd:
                return 0
            return 0
        monkeypatch.setattr(_os, "system", _fake_system)

        # Run pipeline with explicit records merge and limit 1
        import sys
        sys.argv = [
            "pipeline",
            "--records",
            "data/records/a.json,data/records/b.json",
            "--limit",
            "1",
            "--workers",
            "1",
            "--dry-run",
        ]
        pipeline_run()

        # Should have at least one translated file
        out_dir = Path("data/translated")
        files = list(out_dir.glob("*.json")) if out_dir.exists() else []
        assert len(files) == 1
        assert Path("site/index.html").exists()
    finally:
        _restore_tmp(tmp, cwd)
