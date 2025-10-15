from __future__ import annotations

import glob
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class GateSummary:
    passed: int
    flagged: int
    total: int


def run_translation_gate(output_path: str = "reports/translation_report.json") -> GateSummary:
    from src.qa_filter import TranslationQAFilter

    qa = TranslationQAFilter()
    results: Dict[str, Any] = {}
    passed = 0
    flagged = 0
    total = 0

    files = sorted(glob.glob("data/translated/*.json"))

    for fp in files:
        total += 1
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = qa.check_translation(data)
            results[os.path.basename(fp)] = {
                "status": res.status.value,
                "score": res.score,
                "issues": res.issues,
                "chinese_ratio": res.chinese_ratio,
                "flagged_fields": res.flagged_fields,
            }
                if res.status.value == "pass":
                    passed += 1
                else:
                    flagged += 1
        except Exception as e:
            results[os.path.basename(fp)] = {"error": str(e)}
            flagged += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary = {"total": total, "passed": passed, "flagged": flagged}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)

    return GateSummary(passed=passed, flagged=flagged, total=total)


if __name__ == "__main__":
    summary = run_translation_gate()
    print(f"Summary: total={summary.total} passed={summary.passed} flagged={summary.flagged}")
    should_fail = (summary.total == 0) or (summary.flagged > 0)
    if should_fail:
        sys.stderr.write("Translation gate failed: no translations processed or QA flagged items.\n")
        sys.exit(1)

