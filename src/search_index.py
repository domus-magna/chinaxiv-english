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
    translated_paths = sorted(glob.glob(os.path.join("data", "translated", "*.json")))
    out_path = os.path.join("site", "search-index.json")

    # Stream-write JSON array to avoid loading everything in memory
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    count = 0
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('[')
        first = True
        for p in translated_paths:
            try:
                item_data = read_json(p)
                entry = Translation.from_dict(item_data).get_search_index_entry()
                if not first:
                    f.write(',')
                json.dump(entry, f, ensure_ascii=False, separators=(',', ':'))
                first = False
                count += 1
            except Exception:
                continue
        f.write(']')

    # Write compressed index
    compressed_path = os.path.join("site", "search-index.json.gz")
    with open(out_path, 'r', encoding='utf-8') as src:
        with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
            f.write(src.read())

    # Log compression stats
    uncompressed_size = os.path.getsize(out_path)
    compressed_size = os.path.getsize(compressed_path)
    compression_ratio = (1 - compressed_size / uncompressed_size) * 100 if uncompressed_size else 0.0

    log(f"Wrote search index with {count} entries → {out_path}")
    log(f"Compressed index: {compressed_size:,} bytes ({compression_ratio:.1f}% reduction) → {compressed_path}")


if __name__ == "__main__":
    run_cli()
