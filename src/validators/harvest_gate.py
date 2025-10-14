from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


REQUIRED_FIELDS = ["id", "title", "abstract", "pdf_url"]


@dataclass
class HarvestGateSummary:
    total: int
    schema_pass: int
    pdf_ok: int
    dup_ids: int
    pass_threshold_met: bool


def _find_latest_records() -> Optional[str]:
    files = sorted(glob.glob(os.path.join("data", "records", "*.json")))
    return files[-1] if files else None


def _load_records(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _check_schema(rec: Dict[str, Any]) -> bool:
    for k in REQUIRED_FIELDS:
        if k not in rec or rec[k] in (None, ""):
            return False
    # Basic type sanity
    if not isinstance(rec["id"], str):
        return False
    if not isinstance(rec["title"], str):
        return False
    if not isinstance(rec["abstract"], str):
        return False
    if not isinstance(rec["pdf_url"], str) or not rec["pdf_url"].startswith("http"):
        return False
    return True


def _check_pdf_head(url: str, timeout: int = 15) -> bool:
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        if r.status_code >= 400:
            return False
        ctype = r.headers.get("content-type", "").lower()
        # Some servers omit type; allow by size fallback using GET if needed
        if "pdf" in ctype:
            return True
        # Fallback: tiny ranged GET to confirm
        r2 = requests.get(url, headers={"Range": "bytes=0-0"}, timeout=timeout)
        if r2.status_code in (200, 206):
            return True
    except Exception:
        return False
    return False


def run_harvest_gate(records_path: Optional[str] = None, out_dir: str = "reports") -> HarvestGateSummary:
    records_path = records_path or _find_latest_records()
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "harvest_report.json")
    report_md = os.path.join(out_dir, "harvest_report.md")

    if not records_path:
        data = {"error": "No records found"}
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        with open(report_md, "w", encoding="utf-8") as f:
            f.write("# Harvest Report\n\nNo records found.\n")
        return HarvestGateSummary(total=0, schema_pass=0, pdf_ok=0, dup_ids=0, pass_threshold_met=False)

    recs = _load_records(records_path)
    total = len(recs)
    schema_pass = 0
    pdf_ok = 0
    seen_ids: set[str] = set()
    dup_ids = 0
    per_rec: Dict[str, Any] = {}

    for rec in recs:
        rid = str(rec.get("id", ""))
        schema_ok = _check_schema(rec)
        pdf_ok_flag = False
        if schema_ok and rec.get("pdf_url"):
            pdf_ok_flag = _check_pdf_head(rec["pdf_url"])  # network optional
        if schema_ok:
            schema_pass += 1
        if pdf_ok_flag:
            pdf_ok += 1
        if rid in seen_ids:
            dup_ids += 1
        else:
            seen_ids.add(rid)
        per_rec[rid or f"idx_{len(per_rec)}"] = {
            "schema": schema_ok,
            "pdf_ok": pdf_ok_flag,
        }

    # Thresholds: schema >= 95%, pdf_ok >= 98% of those with schema_ok
    schema_rate = (schema_pass / total) * 100 if total else 0.0
    pdf_rate = (pdf_ok / max(schema_pass, 1)) * 100 if total else 0.0
    pass_threshold = (schema_rate >= 95.0) and (pdf_rate >= 98.0) and (dup_ids == 0)

    summary = {
        "records_path": records_path,
        "total": total,
        "schema_pass": schema_pass,
        "pdf_ok": pdf_ok,
        "dup_ids": dup_ids,
        "schema_rate": round(schema_rate, 2),
        "pdf_rate": round(pdf_rate, 2),
        "pass": pass_threshold,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": per_rec}, f, indent=2, ensure_ascii=False)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("\n".join([
            "# Harvest Report",
            "",
            f"Total: {total}",
            f"Schema pass: {schema_pass} ({summary['schema_rate']}%)",
            f"PDF OK: {pdf_ok} ({summary['pdf_rate']}% of schema-pass)",
            f"Duplicate IDs: {dup_ids}",
            f"Status: {'PASS' if pass_threshold else 'FAIL'}",
            "",
        ]))

    # Mirror JSON for site
    try:
        os.makedirs(os.path.join("site", "stats", "validation"), exist_ok=True)
        with open(os.path.join("site", "stats", "validation", "harvest_report.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return HarvestGateSummary(total=total, schema_pass=schema_pass, pdf_ok=pdf_ok, dup_ids=dup_ids, pass_threshold_met=pass_threshold)


if __name__ == "__main__":
    s = run_harvest_gate()
    print(json.dumps({"total": s.total, "schema_pass": s.schema_pass, "pdf_ok": s.pdf_ok, "dup_ids": s.dup_ids, "pass": s.pass_threshold_met}))


