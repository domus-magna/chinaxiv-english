Temp: LLM Formatter Samples — Execution Instructions

Goal
- Regenerate before/after formatting samples using the LLM formatter so we can decide whether to enable it by default.

Prereqs
- You must have a valid OpenRouter API key with access to the chosen model (default: deepseek/deepseek-v3.2-exp).

1) Verify Environment Has Key
```bash
# From repo root
echo $OPENROUTER_API_KEY
python3 -c "import os; print(os.getenv('OPENROUTER_API_KEY'))"
```
Expected: Both commands should show a non-empty value. If empty, set the key:
```bash
# Either export in your shell
export OPENROUTER_API_KEY=sk-or-...

# Or create/update .env in the repo root
printf 'OPENROUTER_API_KEY=sk-or-...\n' > .env
```

2) Generate Before/After Samples
```bash
# Install deps if needed
python3 -m pip install -r requirements.txt

# Generate samples for 3 papers (auto-picked with body content)
python3 -m src.tools.formatting_compare --count 3

# Or specify exact IDs
# python3 -m src.tools.formatting_compare --ids paper-202503-00066 paper-202502-00265
```
Notes:
- The tool runs a math-safe LLM formatter and falls back to heuristics if the LLM call fails.
- If LLM succeeds, you won’t see a warning; if it fails, the sample page shows a small note near the top.

3) View Samples Locally
```bash
python3 -m http.server -d site 8001
# Then open in your browser:
# http://localhost:8001/samples/
```

4) Toggle LLM Formatting by Default (optional after review)
Edit `src/config.yaml`:
```yaml
formatting:
  mode: llm  # change from 'heuristic' to 'llm' once you’re satisfied
  # model: deepseek/deepseek-v3.2-exp # optional override
  temperature: 0.1
```

Extra: Few-shot Examples
- If we want even tighter consistency, we can add 2–3 before/after snippets to the formatter prompt in `src/services/formatting_service.py`.
- Good candidates:
  - Numbered headings → ‘## 1. Introduction’
  - Broken lines merged into paragraphs
  - True lists → ‘- ’ prefix, avoid spurious lists

Done
- Once the API key is available and the command above runs, the LLM ‘After’ column on the sample pages will reflect the improved formatting.
