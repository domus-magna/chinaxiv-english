from __future__ import annotations

import glob
import gzip
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
    
    # Write uncompressed index
    out_path = os.path.join("site", "search-index.json")
    write_json(out_path, idx)
    
    # Write compressed index
    compressed_path = os.path.join("site", "search-index.json.gz")
    with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, separators=(',', ':'))
    
    # Log compression stats
    uncompressed_size = os.path.getsize(out_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = (1 - compressed_size / uncompressed_size) * 100
    
    log(f"Wrote search index with {len(idx)} entries → {out_path}")
    log(f"Compressed index: {compressed_size:,} bytes ({compression_ratio:.1f}% reduction) → {compressed_path}")


if __name__ == "__main__":
    run_cli()

