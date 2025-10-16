from __future__ import annotations

import glob
import json
import os
import sys
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from src.config import get_config
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
    thresholds = get_config().get("validation_thresholds", {}).get("translation", {})
    max_flagged_ratio = float(thresholds.get("max_flagged_ratio", 0.0))
    max_flagged_absolute = int(thresholds.get("max_flagged_absolute", 0))

    reasons = []
    if total == 0:
        reasons.append("no_translations")
    flagged_ratio = (flagged / total) if total else 0.0
    if flagged_ratio > max_flagged_ratio:
        reasons.append("flagged_ratio_exceeds_threshold")
    if flagged > max_flagged_absolute >= 0:
        reasons.append("flagged_count_exceeds_threshold")

    pass_ok = total > 0 and flagged_ratio <= max_flagged_ratio and not (flagged > max_flagged_absolute >= 0)

    summary = {
        "total": total,
        "passed": passed,
        "flagged": flagged,
        "flagged_ratio": round(flagged_ratio, 4),
        "reasons": reasons,
        "thresholds": {
            "max_flagged_ratio": max_flagged_ratio,
            "max_flagged_absolute": max_flagged_absolute,
        },
    }
    payload = {"summary": summary, "results": results}
    report_path = Path(output_path)
    markdown = build_markdown_report(
        "Translation Gate Report",
        [
            ("Total translations", total),
            ("Passed", passed),
            ("Flagged", flagged),
            ("Flagged ratio", f"{flagged_ratio:.2%}"),
            ("Status", "PASS" if pass_ok else "FAIL"),
        ],
        reasons,
    )
    save_validation_report(str(report_path.parent), report_path.stem, payload, markdown, summary)

    return GateSummary(passed=passed, flagged=flagged, total=total)


if __name__ == "__main__":
    summary = run_translation_gate()
    print(f"Summary: total={summary.total} passed={summary.passed} flagged={summary.flagged}")
    # Intentional hard stop: any QA-flagged translation must be reviewed before downstream stages run.
    thresholds = get_config().get("validation_thresholds", {}).get("translation", {})
    max_flagged_ratio = float(thresholds.get("max_flagged_ratio", 0.0))
    max_flagged_absolute = int(thresholds.get("max_flagged_absolute", 0))
    flagged_ratio = (summary.flagged / summary.total) if summary.total else 0.0
    exceeds_ratio = flagged_ratio > max_flagged_ratio
    exceeds_absolute = summary.flagged > max_flagged_absolute >= 0
    should_fail = (summary.total == 0) or exceeds_ratio or exceeds_absolute
    if should_fail:
        sys.stderr.write("Translation gate failed: no translations processed or QA flagged items.\n")
        sys.exit(1)
