from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional

from lxml import etree

import time

from .utils import (
    http_get,
    load_yaml,
    log,
    save_raw_xml,
    stable_id_from_oai,
    write_json,
    ensure_dir,
)


NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def oai_request(base_url: str, **params: str) -> str:
    resp = http_get(base_url, params=params)
    return resp.text


def parse_identify(xml: str) -> Dict[str, str]:
    root = etree.fromstring(xml.encode("utf-8"))
    repo_name = root.findtext(".//{http://www.openarchives.org/OAI/2.0/}repositoryName")
    earliest = root.findtext(
        ".//{http://www.openarchives.org/OAI/2.0/}earliestDatestamp"
    )
    granularity = root.findtext(".//{http://www.openarchives.org/OAI/2.0/}granularity")
    return {
        "repositoryName": repo_name or "",
        "earliestDatestamp": earliest or "",
        "granularity": granularity or "",
    }


def extract_first_url(texts: List[str], suffix: Optional[str] = None) -> Optional[str]:
    for t in texts:
        t = t.strip()
        if t.startswith("http://") or t.startswith("https://"):
            if suffix is None or t.lower().endswith(suffix.lower()):
                return t
    return None


def normalize_record(rec_el: etree._Element) -> Optional[Dict[str, Any]]:
    header = rec_el.find("oai:header", namespaces=NS)
    if header is None:
        return None
    deleted = header.get("status") == "deleted"
    oai_identifier = header.findtext("oai:identifier", namespaces=NS) or ""
    datestamp = header.findtext("oai:datestamp", namespaces=NS) or ""
    sets = [e.text for e in header.findall("oai:setSpec", namespaces=NS)]
    meta = rec_el.find("oai:metadata", namespaces=NS)
    if meta is None or deleted:
        return None

    # Try oai_eprint first; if absent, use dc
    # We don't know the namespace for eprint here; fallback to dc for portable behavior
    # Extract common DC-like fields
    titles = [e.text for e in meta.findall(".//dc:title", namespaces=NS) if e.text]
    creators = [e.text for e in meta.findall(".//dc:creator", namespaces=NS) if e.text]
    subjects = [e.text for e in meta.findall(".//dc:subject", namespaces=NS) if e.text]
    descriptions = [
        e.text for e in meta.findall(".//dc:description", namespaces=NS) if e.text
    ]
    dates = [e.text for e in meta.findall(".//dc:date", namespaces=NS) if e.text]
    identifiers = [
        e.text for e in meta.findall(".//dc:identifier", namespaces=NS) if e.text
    ]
    rights = [e.text for e in meta.findall(".//dc:rights", namespaces=NS) if e.text]

    title = titles[0] if titles else ""
    abstract = descriptions[0] if descriptions else ""
    date_val = dates[0] if dates else datestamp[:10]
    pdf_url = extract_first_url(identifiers, suffix=".pdf")
    source_url = extract_first_url(identifiers)
    license_raw = rights[0] if rights else ""

    if not oai_identifier:
        return None
    local_id = stable_id_from_oai(oai_identifier)

    return {
        "id": local_id,
        "oai_identifier": oai_identifier,
        "title": title,
        "creators": creators,
        "abstract": abstract,
        "subjects": subjects,
        "date": date_val,
        "pdf_url": pdf_url,
        "source_url": source_url,
        "license": {"raw": license_raw, "derivatives_allowed": None},
        "setSpec": ",".join(sets) if sets else None,
    }


def harvest(
    base_url: str,
    metadata_prefix: str,
    day_from: str,
    day_until: str,
    set_spec: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, str] = {
        "verb": "ListRecords",
        "metadataPrefix": metadata_prefix,
        "from": day_from,
        "until": day_until,
    }
    if set_spec:
        params["set"] = set_spec

    part = 1
    day = day_from
    out: List[Dict[str, Any]] = []
    while True:
        xml = oai_request(base_url, **params)
        save_raw_xml(xml, day, part)
        root = etree.fromstring(xml.encode("utf-8"))
        records = root.findall(".//oai:ListRecords/oai:record", namespaces=NS)
        for rec in records:
            item = normalize_record(rec)
            if item:
                out.append(item)
        # resumptionToken handling
        token_el = root.find(".//oai:ListRecords/oai:resumptionToken", namespaces=NS)
        token = (
            token_el.text.strip() if token_el is not None and token_el.text else None
        )
        if token:
            params = {"verb": "ListRecords", "resumptionToken": token}
            part += 1
            # Polite pacing to avoid hammering the endpoint
            time.sleep(1.0)
        else:
            break
    return out


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest ChinaXiv via OAI-PMH and normalize records."
    )
    parser.add_argument("--from", dest="from_day", help="YYYY-MM-DD start date (UTC)")
    parser.add_argument("--until", dest="until_day", help="YYYY-MM-DD end date (UTC)")
    parser.add_argument("--base-url", dest="base_url", help="OAI base URL override")
    parser.add_argument(
        "--metadata-prefix",
        dest="metadata_prefix",
        help="Override metadataPrefix (default from config)",
    )
    parser.add_argument("--set", dest="set_spec", help="Harvest specific setSpec")
    args = parser.parse_args()

    cfg = load_yaml(os.path.join("src", "config.yaml"))
    base_url = args.base_url or cfg["oai"]["base_url"]
    metadata_prefix = args.metadata_prefix or cfg["oai"].get(
        "metadata_prefix", "oai_eprint"
    )

    if args.from_day and args.until_day:
        day_from, day_until = args.from_day, args.until_day
    else:
        from .utils import utc_date_range_str

        day_from, day_until = utc_date_range_str(cfg["oai"].get("date_window_days", 1))

    log("Identify endpoint liveness…")
    ident_xml = oai_request(base_url, verb="Identify")
    info = parse_identify(ident_xml)
    log(
        f"OAI: {info['repositoryName']} earliest={info['earliestDatestamp']} granularity={info['granularity']}"
    )

    sets = [args.set_spec] if args.set_spec else (cfg["oai"].get("sets", []) or [None])
    all_items: List[Dict[str, Any]] = []
    for s in sets:
        log(f"Harvesting {day_from}..{day_until} set={s or '-'}")
        items = harvest(base_url, metadata_prefix, day_from, day_until, s)
        log(f"Fetched {len(items)} records from set={s or '-'}")
        all_items.extend(items)

    # Save normalized JSON for the window
    ensure_dir(os.path.join("data", "records"))
    out_path = os.path.join("data", "records", f"{day_from}_to_{day_until}.json")
    write_json(out_path, all_items)
    log(f"Wrote normalized records → {out_path}")


if __name__ == "__main__":
    run_cli()
