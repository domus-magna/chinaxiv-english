from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OCRGateSummary:
    flagged: int
    improved: int
    pass_rate: float
    pass_threshold_met: bool
    missing_execution: int = 0
    unimproved: int = 0
    reasons: List[str] = field(default_factory=list)


def run_ocr_gate(report_dir: str = "reports") -> OCRGateSummary:
    det_path = os.path.join(report_dir, "ocr_detection_report.json")
    exec_path = os.path.join(report_dir, "ocr_execution_report.json")

    try:
        with open(det_path, "r", encoding="utf-8") as f:
            det = json.load(f)
    except Exception:
        det = {}
    try:
        with open(exec_path, "r", encoding="utf-8") as f:
            exe = json.load(f)
    except Exception:
        exe = {}

    if not det:
        detection_missing = True
    else:
        detection_missing = False

    flagged = sum(1 for v in det.values() if v.get("need_ocr"))
    improved = 0
    results: Dict[str, Any] = {}
    missing_exec_ids = []
    unimproved_ids = []

    for pid, meta in det.items():
        need = bool(meta.get("need_ocr"))
        pre = int(meta.get("pre_ocr_chars") or 0)
        post = None
        ran = False
        improved_flag = False
        if pid in exe:
            ran = bool(exe[pid].get("ran_ocr"))
            post = int(exe[pid].get("post_ocr_chars") or 0)
            # Improvement threshold: +500 chars or 5x
            improved_flag = ran and ((post - pre) >= 500 or (pre > 0 and (post / pre) >= 5.0))
        elif need:
            missing_exec_ids.append(pid)
        if need and improved_flag:
            improved += 1
        if need and not ran:
            missing_exec_ids.append(pid)
        if need and ran and not improved_flag:
            unimproved_ids.append(pid)
        results[pid] = {
            "need": need,
            "ran": ran,
            "pre": pre,
            "post": post,
            "improved": improved_flag,
        }

    # Deduplicate ids tracked in multiple branches
    missing_exec_ids = sorted(set(missing_exec_ids))
    unimproved_ids = sorted(set(unimproved_ids))

    pass_rate = (improved / max(flagged, 1)) * 100.0 if flagged else 100.0
    pass_ok = (
        not detection_missing
        and not missing_exec_ids
        and not unimproved_ids
        and (pass_rate >= 98.0 or not flagged)
    )  # Threshold from plan

    summary = {
        "flagged": flagged,
        "improved": improved,
        "pass_rate": round(pass_rate, 2),
        "pass": pass_ok,
        "missing_execution": len(missing_exec_ids),
        "unimproved": len(unimproved_ids),
        "reasons": [],
    }
    if detection_missing:
        summary["reasons"].append("detection_report_missing_or_empty")
    if missing_exec_ids:
        summary["reasons"].append("missing_execution_records")
    if unimproved_ids:
        summary["reasons"].append("insufficient_improvement")

    os.makedirs(report_dir, exist_ok=True)
    with open(os.path.join(report_dir, "ocr_gate_report.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": summary,
                "results": results,
                "missing_execution_ids": missing_exec_ids,
                "unimproved_ids": unimproved_ids,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    with open(os.path.join(report_dir, "ocr_gate_report.md"), "w", encoding="utf-8") as f:
        lines = [
            "# OCR Gate Report",
            "",
            f"Flagged: {flagged}",
            f"Improved: {improved}",
            f"Missing execution records: {len(missing_exec_ids)}",
            f"Unimproved OCR runs: {len(unimproved_ids)}",
            f"Pass rate: {summary['pass_rate']}%",
            f"Status: {'PASS' if pass_ok else 'FAIL'}",
        ]
        if summary["reasons"]:
            lines.append("")
            lines.append("Reasons:")
            for reason in summary["reasons"]:
                lines.append(f"- {reason}")
        lines.append("")
        f.write("\n".join(lines))

    try:
        os.makedirs(os.path.join("site", "stats", "validation"), exist_ok=True)
        with open(os.path.join("site", "stats", "validation", "ocr_gate_report.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return OCRGateSummary(
        flagged=flagged,
        improved=improved,
        pass_rate=pass_rate,
        pass_threshold_met=pass_ok,
        missing_execution=len(missing_exec_ids),
        unimproved=len(unimproved_ids),
        reasons=summary["reasons"],
    )


if __name__ == "__main__":
    s = run_ocr_gate()
    print(
        json.dumps(
            {
                "flagged": s.flagged,
                "improved": s.improved,
                "pass_rate": s.pass_rate,
                "pass": s.pass_threshold_met,
                "missing_execution": s.missing_execution,
                "unimproved": s.unimproved,
                "reasons": s.reasons,
            }
        )
    )
    if not s.pass_threshold_met:
        raise SystemExit(1)

