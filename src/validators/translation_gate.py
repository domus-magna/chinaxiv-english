from __future__ import annotations

import json
import glob
import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class GateSummary:
    passed: int
    flagged: int


def run_translation_gate(output_path: str = "reports/translation_report.json") -> GateSummary:
    from src.qa_filter import TranslationQAFilter

    qa = TranslationQAFilter()
    results: Dict[str, Any] = {}
    passed = 0
    flagged = 0

    for fp in glob.glob("data/translated/*.json"):
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

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": {"passed": passed, "flagged": flagged}, "results": results}, f, indent=2, ensure_ascii=False)

    return GateSummary(passed=passed, flagged=flagged)


if __name__ == "__main__":
    s = run_translation_gate()
    print(f"Summary: passed={s.passed} flagged={s.flagged}")


