from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


REQUIRED_FIELDS = [
    "id",
    "title",
    "abstract",
    "creators",
    "subjects",
    "date",
    "source_url",
    "pdf_url",
]
USER_AGENT = "chinaxiv-harvest-gate/1.0"


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


def _check_schema(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    for k in REQUIRED_FIELDS:
        if k not in rec or rec[k] in (None, ""):
            errors.append(f"Missing field: {k}")

    rid = rec.get("id")
    if not isinstance(rid, str) or not re.match(r"^chinaxiv-\d{6}\.\d{5}$", rid or ""):
        errors.append("Invalid id format")

    if not isinstance(rec.get("title"), str):
        errors.append("Title must be string")

    if not isinstance(rec.get("abstract"), str) or len(rec.get("abstract", "")) < 50:
        errors.append("Abstract too short")

    creators = rec.get("creators")
    if not isinstance(creators, list) or not creators:
        errors.append("Creators must be non-empty list")

    subjects = rec.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        errors.append("Subjects must be non-empty list")

    if not isinstance(rec.get("date"), str):
        errors.append("Date must be string")

    pdf_url = rec.get("pdf_url")
    if not isinstance(pdf_url, str) or not pdf_url.startswith("http"):
        errors.append("Invalid pdf_url")

    source_url = rec.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("http"):
        errors.append("Invalid source_url")

    return (len(errors) == 0, errors)


def _discover_pdf_url(source_url: str) -> Optional[str]:
    try:
        resp = requests.get(source_url, timeout=30, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("a", href=re.compile(r"\.(pdf|PDF)(?:$|\?)"))
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("http"):
                return href
            return requests.compat.urljoin(source_url, href)
    except Exception:
        return None
    return None


def _check_pdf_access(url: str, timeout: int = 30) -> bool:
    try:
        with requests.get(
            url,
            stream=True,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            if "pdf" in content_type:
                return True
            chunk = next(resp.iter_content(chunk_size=1024), b"")
            return chunk.startswith(b"%PDF-")
    except StopIteration:
        return False
    except Exception:
        return False


def _resolve_pdf(rec: Dict[str, Any]) -> Tuple[Optional[str], List[str], bool]:
    issues: List[str] = []
    pdf_url = rec.get("pdf_url")
    source_url = rec.get("source_url")
    if pdf_url and _check_pdf_access(pdf_url):
        return pdf_url, issues, True
    if source_url:
        resolved = _discover_pdf_url(source_url)
        if resolved and _check_pdf_access(resolved):
            return resolved, issues, True
        issues.append("Could not resolve PDF via source page")
    if pdf_url:
        issues.append(f"PDF inaccessible: {pdf_url}")
    else:
        issues.append("Missing pdf_url")
    return None, issues, False


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

    for idx, rec in enumerate(recs):
        rid = rec.get("id") or f"idx_{idx}"
        schema_ok, schema_errors = _check_schema(rec)
        resolved_url, pdf_issues, pdf_ok_flag = _resolve_pdf(rec)
        if schema_ok:
            schema_pass += 1
        else:
            pdf_issues.extend(schema_errors)
        if pdf_ok_flag:
            pdf_ok += 1
        else:
            pdf_issues.extend(schema_errors)
        if rid in seen_ids:
            dup_ids += 1
            pdf_issues.append("Duplicate ID")
        else:
            seen_ids.add(rid)
        per_rec[rid] = {
            "schema": schema_ok,
            "schema_errors": schema_errors,
            "pdf": {
                "pdf_ok": pdf_ok_flag,
                "resolved_url": resolved_url,
                "issues": pdf_issues,
            },
        }

    # Thresholds: schema >= 95%, pdf_ok >= 98% of those with schema_ok
    schema_rate = (schema_pass / total) * 100 if total else 0.0
    pdf_rate = (pdf_ok / max(schema_pass, 1)) * 100 if schema_pass else 0.0
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
    detail = {
        "summary": summary,
        "results": per_rec,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=2, ensure_ascii=False)
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
    summary = run_harvest_gate()
    print(json.dumps({
        "total": summary.total,
        "schema_pass": summary.schema_pass,
        "pdf_ok": summary.pdf_ok,
        "dup_ids": summary.dup_ids,
        "pass": summary.pass_threshold_met,
    }))
    should_fail = (summary.total == 0) or not summary.pass_threshold_met
    if should_fail:
        sys.stderr.write("Harvest gate failed: no records processed or thresholds not met.\n")
        sys.exit(1)

