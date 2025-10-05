from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List

from .utils import read_json, write_json, log
from .models import Translation


def build_index(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    idx: List[Dict[str, Any]] = []
    for item_data in items:
        translation = Translation.from_dict(item_data)
        idx.append(translation.get_search_index_entry())
    return idx


def run_cli() -> None:
    items = [read_json(p) for p in sorted(glob.glob(os.path.join("data", "translated", "*.json")))]
    idx = build_index(items)
    out_path = os.path.join("site", "search-index.json")
    write_json(out_path, idx)
    log(f"Wrote search index with {len(idx)} entries → {out_path}")


if __name__ == "__main__":
    run_cli()

