from __future__ import annotations

import glob
import json
import os
import sys
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from src.reporting import build_markdown_report, save_validation_report

logger = logging.getLogger(__name__)


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
            logger.exception("Failed to validate translation %s", fp)
            results[os.path.basename(fp)] = {"error": str(e)}
            flagged += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    reasons = []
    if total == 0:
        reasons.append("no_translations")
    if flagged > 0:
        reasons.append("flagged_translations_present")

    summary = {"total": total, "passed": passed, "flagged": flagged, "reasons": reasons}
    payload = {"summary": summary, "results": results}
    report_path = Path(output_path)
    markdown = build_markdown_report(
        "Translation Gate Report",
        [
            ("Total translations", total),
            ("Passed", passed),
            ("Flagged", flagged),
            ("Status", "PASS" if flagged == 0 and total > 0 else "FAIL"),
        ],
        reasons,
    )
    save_validation_report(str(report_path.parent), report_path.stem, payload, markdown, summary)

    return GateSummary(passed=passed, flagged=flagged, total=total)


if __name__ == "__main__":
    summary = run_translation_gate()
    print(f"Summary: total={summary.total} passed={summary.passed} flagged={summary.flagged}")
    # Intentional hard stop: any QA-flagged translation must be reviewed before downstream stages run.
    should_fail = (summary.total == 0) or (summary.flagged > 0)
    if should_fail:
        sys.stderr.write("Translation gate failed: no translations processed or QA flagged items.\n")
        sys.exit(1)
