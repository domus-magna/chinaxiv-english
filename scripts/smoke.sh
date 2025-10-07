#!/usr/bin/env bash
set -euo pipefail

python3 -m pytest -q
python3 -m src.health --skip-openrouter || true

# Try ChinaXiv harvest via BrightData if credentials present
if [[ -n "$BRIGHTDATA_API_KEY" && -n "$BRIGHTDATA_ZONE" ]]; then
  python3 -m src.harvest_chinaxiv_optimized --month $(date -u +"%Y%m") || true
else
  echo 'Skipping harvest: set BRIGHTDATA_API_KEY and BRIGHTDATA_ZONE to enable'
fi
latest=$(ls -1t data/records/*.json 2>/dev/null | head -n1 || echo '')
if [[ -n "$latest" ]]; then
  python3 -m src.select_and_fetch --records "$latest" --limit 2 --output data/selected.json || true
else
  echo '[]' > data/selected.json
fi
python3 -m src.translate --selected data/selected.json --dry-run
python3 -m src.render
python3 -m src.search_index
python3 -m src.make_pdf || true

echo 'Smoke build complete → site/ (run `make serve` to preview)'
