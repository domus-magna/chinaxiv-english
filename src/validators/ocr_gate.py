from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class OCRGateSummary:
    flagged: int
    improved: int
    pass_rate: float
    pass_threshold_met: bool


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

    flagged = sum(1 for v in det.values() if v.get("need_ocr"))
    improved = 0
    results: Dict[str, Any] = {}

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
        if need and improved_flag:
            improved += 1
        results[pid] = {
            "need": need,
            "ran": ran,
            "pre": pre,
            "post": post,
            "improved": improved_flag,
        }

    pass_rate = (improved / max(flagged, 1)) * 100.0 if flagged else 100.0
    pass_ok = pass_rate >= 98.0  # Threshold from plan

    summary = {
        "flagged": flagged,
        "improved": improved,
        "pass_rate": round(pass_rate, 2),
        "pass": pass_ok,
    }
    os.makedirs(report_dir, exist_ok=True)
    with open(os.path.join(report_dir, "ocr_gate_report.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)
    with open(os.path.join(report_dir, "ocr_gate_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join([
            "# OCR Gate Report",
            "",
            f"Flagged: {flagged}",
            f"Improved: {improved}",
            f"Pass rate: {summary['pass_rate']}%",
            f"Status: {'PASS' if pass_ok else 'FAIL'}",
            "",
        ]))

    try:
        os.makedirs(os.path.join("site", "stats", "validation"), exist_ok=True)
        with open(os.path.join("site", "stats", "validation", "ocr_gate_report.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return OCRGateSummary(flagged=flagged, improved=improved, pass_rate=pass_rate, pass_threshold_met=pass_ok)


if __name__ == "__main__":
    s = run_ocr_gate()
    print(json.dumps({"flagged": s.flagged, "improved": s.improved, "pass_rate": s.pass_rate, "pass": s.pass_threshold_met}))


