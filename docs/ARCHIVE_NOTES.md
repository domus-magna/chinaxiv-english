Archived and Reorganized Documents

- Moved Cloudflare setup checklists to `docs/archive/old/`:
  - `CLOUDFLARE_CHECKLIST.md` → `docs/archive/old/CLOUDFLARE_CHECKLIST.md`
  - `CLOUDFLARE_QUICK_START.md` → `docs/archive/old/CLOUDFLARE_QUICK_START.md`
  - `CLOUDFLARE_SETUP_GUIDE.md` → `docs/archive/old/CLOUDFLARE_SETUP_GUIDE.md` (secrets redacted)

- Moved parallelization notes to archive:
  - `PARALLELIZATION_COMPARISON.md` → `docs/archive/old/PARALLELIZATION_COMPARISON.md`

- Consolidated developer guides under `docs/`:
  - `DEVELOPMENT.md` → `docs/DEVELOPMENT.md`
  - `claude.md` → `docs/CLAUDE.md`

- Organized temporary instructions:
  - `temp_openrouter_samples_instructions.md` → `docs/todo/openrouter_samples.md`

- Moved temp error log:
  - `pytest_err.txt` → `docs/archive/tmp/pytest_err.txt`

Notes
- Internet Archive approach has been removed from the active plan. Harvesting is external/manual for now.
- Any leaked secrets in historical docs have been redacted here, but consider rotating keys if not already done.
- Archived code:
  - `src/harvest_ia.py` → `src/archive/harvest_ia.py`
  - Real E2E workflow and tests moved under `.github/workflows_archive/` and `docs/archive/tests/`
