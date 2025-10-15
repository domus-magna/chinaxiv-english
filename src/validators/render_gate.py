from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class RenderGateSummary:
    translated_docs: int
    indexed_docs: int
    html_items: int
    pass_threshold_met: bool


def run_render_gate(site_dir: str = "site", data_dir: str = "data", out_dir: str = "reports") -> RenderGateSummary:
    # Count translated docs
    translated = len(glob.glob(os.path.join(data_dir, "translated", "*.json")))

    # Load search index
    index_path = os.path.join(site_dir, "search-index.json")
    indexed_docs = 0
    index_ok = False
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)
        # Accept either list or dict with documents key
        if isinstance(idx, list):
            indexed_docs = len(idx)
            index_ok = True
        elif isinstance(idx, dict):
            docs = idx.get("documents") or idx.get("docs") or []
            indexed_docs = len(docs) if isinstance(docs, list) else 0
            index_ok = True
    except Exception:
        index_ok = False

    # Count rendered HTML items
    html_items = len(glob.glob(os.path.join(site_dir, "items", "*", "*.html")))

    # Thresholds: index ok; indexed_docs == translated; html_items >= translated
    pass_ok = index_ok and (indexed_docs == translated) and (html_items >= translated)

    summary = {
        "translated_docs": translated,
        "indexed_docs": indexed_docs,
        "html_items": html_items,
        "pass": pass_ok,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "render_report.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "render_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join([
            "# Render Gate Report",
            "",
            f"Translated docs: {translated}",
            f"Indexed docs: {indexed_docs}",
            f"HTML items: {html_items}",
            f"Status: {'PASS' if pass_ok else 'FAIL'}",
            "",
        ]))

    try:
        os.makedirs(os.path.join("site", "stats", "validation"), exist_ok=True)
        with open(os.path.join("site", "stats", "validation", "render_report.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return RenderGateSummary(translated_docs=translated, indexed_docs=indexed_docs, html_items=html_items, pass_threshold_met=pass_ok)


if __name__ == "__main__":
    s = run_render_gate()
    print(json.dumps({"translated_docs": s.translated_docs, "indexed_docs": s.indexed_docs, "html_items": s.html_items, "pass": s.pass_threshold_met}))


