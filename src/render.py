from __future__ import annotations

import argparse
import glob
import os
import shutil
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape
import time

from .utils import ensure_dir, log, read_json, write_text


def load_translated() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    flagged_count = 0

    # Check for bypass file first, but only use if explicitly enabled
    bypass_file = os.path.join("data", "translated_bypass.json")
    use_bypass = os.environ.get("USE_TRANSLATED_BYPASS", "0").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if os.path.exists(bypass_file):
        if use_bypass:
            log("Using bypassed translations (USE_TRANSLATED_BYPASS=1)")
            return read_json(bypass_file)
        else:
            log(
                "Bypass file present but ignored; set USE_TRANSLATED_BYPASS=1 to enable"
            )

    for path in sorted(glob.glob(os.path.join("data", "translated", "*.json"))):
        item = read_json(path)

        # Skip items flagged by QA filter
        qa_status = item.get("_qa_status", "pass")
        if qa_status != "pass":
            flagged_count += 1
            log(
                f"Skipping flagged translation: {item.get('id', 'unknown')} ({qa_status})"
            )
            continue

        items.append(item)

    if flagged_count > 0:
        log(f"Skipped {flagged_count} flagged translations")

    return items


def render_site(items: List[Dict[str, Any]]) -> None:
    from .format_translation import format_translation_to_markdown

    env = Environment(
        loader=FileSystemLoader(os.path.join("src", "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Add markdown filter
    try:
        import markdown

        def markdown_filter(text):
            return markdown.markdown(text, extensions=["extra", "codehilite"])

        env.filters["markdown"] = markdown_filter
    except ImportError:
        # Fallback: wrap paragraphs and line breaks for valid HTML
        def simple_markdown(text: str) -> str:
            if not text:
                return ""
            paragraphs = [p.strip() for p in str(text).split("\n\n")]
            html = "".join("<p>{}</p>".format(p.replace("\n", "<br>")) for p in paragraphs if p)
            return html

        env.filters["markdown"] = simple_markdown

    base_out = "site"
    ensure_dir(base_out)

    # Copy assets
    assets_src = "assets"
    assets_dst = os.path.join(base_out, "assets")
    if os.path.exists(assets_dst):
        shutil.rmtree(assets_dst)
    if os.path.exists(assets_src):
        shutil.copytree(assets_src, assets_dst)

    build_version = int(time.time())

    # Index page
    tmpl_index = env.get_template("index.html")
    html_index = tmpl_index.render(items=items, root=".", build_version=build_version)
    write_text(os.path.join(base_out, "index.html"), html_index)

    # Monitor page
    tmpl_monitor = env.get_template("monitor.html")
    html_monitor = tmpl_monitor.render(root=".", build_version=build_version)
    write_text(os.path.join(base_out, "monitor.html"), html_monitor)

    # Donations page
    tmpl_donations = env.get_template("donations.html")
    html_donations = tmpl_donations.render(root=".", build_version=build_version)
    write_text(os.path.join(base_out, "donation.html"), html_donations)

    # Item pages
    tmpl_item = env.get_template("item.html")
    site_base = "https://chinaxiv-english.pages.dev"
    for it in items:
        out_dir = os.path.join(base_out, "items", it["id"])
        ensure_dir(out_dir)

        # Compute whether we have meaningful full text content.
        has_full_text = False
        body_md = it.get("body_md")
        if isinstance(body_md, str) and body_md.strip():
            # Consider content meaningful if there is non-heading text beyond trivial length.
            lines = body_md.splitlines()
            non_heading = [ln for ln in lines if not ln.strip().startswith("#")]
            non_heading_text = "\n".join(non_heading).strip()
            title_text = (it.get("title_en") or "").strip()
            # If the only content is a heading matching the title, treat as not meaningful.
            heading_only = (
                len([ln for ln in lines if ln.strip().startswith("#")]) >= 1
                and len(non_heading_text) == 0
            )
            if non_heading_text and len(non_heading_text) > 100:
                has_full_text = True
            elif not heading_only and len(body_md.strip()) > 200:
                has_full_text = True
        # Fallback: treat body_en arrays with sufficient content as full text
        if not has_full_text:
            body_en = it.get("body_en")
            if isinstance(body_en, list) and any((p or "").strip() for p in body_en):
                long_para = any(len((p or "").strip()) > 100 for p in body_en)
                enough_paras = sum(1 for p in body_en if (p or "").strip()) >= 2
                if long_para or enough_paras:
                    has_full_text = True

        it["_has_full_text"] = has_full_text

        # Choose best-available body markdown for preview only if meaningful
        if has_full_text:
            if body_md:
                it["formatted_body_md"] = body_md
            elif it.get("body_en"):
                it["formatted_body_md"] = format_translation_to_markdown(it)

        # Page metadata (arXiv-style polish): use absolute canonical
        title_text = (it.get("title_en") or "")
        canonical_abs = f"{site_base}/items/{it['id']}/"
        html = tmpl_item.render(
            item=it,
            root="../..",
            build_version=build_version,
            title=f"{title_text} — ChinaXiv {it['id']}",
            canonical_url=canonical_abs,
            og_title=title_text,
            og_description=(it.get("abstract_en") or "")[:200],
            og_url=canonical_abs,
        )
        write_text(os.path.join(out_dir, "index.html"), html)
        # Markdown export (prefer formatted body/abstract if present)
        abstract_md = it.get("abstract_md") or (it.get("abstract_en") or "")
        if it.get("body_md"):
            full_body_md = it["body_md"]
        elif it.get("body_en"):
            # fallback: derive from heuristics
            full_body_md = format_translation_to_markdown(it)
        else:
            full_body_md = ""

        md_parts = [
            f"# {it.get('title_en') or ''}",
            f"**Authors:** {', '.join(it.get('creators') or [])}",
            f"**Date:** {it.get('date') or ''}",
            f"## Abstract\n\n{abstract_md}",
        ]
        if full_body_md:
            md_parts.append("## Full Text\n")
            md_parts.append(full_body_md)
        md_parts.append(
            "\n_Source: ChinaXiv — Machine translation. Verify with original._"
        )
        md = "\n\n".join(md_parts) + "\n"
        write_text(os.path.join(out_dir, f"{it['id']}.md"), md)

        # Optional arXiv-style alias: /abs/<id>/ in addition to /items/<id>/
        abs_dir = os.path.join(base_out, "abs", it["id"])
        ensure_dir(abs_dir)
        write_text(os.path.join(abs_dir, "index.html"), html)

    # Generate sitemap including all item and alias pages
    try:
        from datetime import datetime

        lastmod = datetime.utcnow().strftime("%Y-%m-%d")
        urls: List[str] = []
        # Static top-level pages that currently exist
        urls.extend(
            [
                f"{site_base}/",
                f"{site_base}/donation.html",
                f"{site_base}/search/",
                f"{site_base}/browse/",
                f"{site_base}/help/",
                f"{site_base}/contact/",
                f"{site_base}/stats/",
                f"{site_base}/api/",
            ]
        )
        # Item pages and /abs aliases
        for it in items:
            pid = it.get("id")
            if not pid:
                continue
            urls.append(f"{site_base}/items/{pid}/")
            urls.append(f"{site_base}/abs/{pid}/")

        def url_entry(u: str, priority: str = "0.5", changefreq: str = "weekly") -> str:
            return (
                "  <url>\n"
                f"    <loc>{u}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n"
                f"    <changefreq>{changefreq}</changefreq>\n"
                f"    <priority>{priority}</priority>\n"
                "  </url>\n"
            )

        sitemap_xml = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n",
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n",
        ]
        # Home gets higher priority
        sitemap_xml.append(url_entry(f"{site_base}/", priority="1.0", changefreq="daily"))
        # Add the rest (skip duplicate home which we already added)
        for u in urls:
            if u == f"{site_base}/":
                continue
            sitemap_xml.append(url_entry(u))
        sitemap_xml.append("</urlset>\n")
        write_text(os.path.join(base_out, "sitemap.xml"), "".join(sitemap_xml))
    except Exception as e:
        log(f"Failed to generate sitemap: {e}")


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Render static site from translated records."
    )
    args = parser.parse_args()
    items = load_translated()
    render_site(items)
    log(f"Rendered site with {len(items)} items → site/")


if __name__ == "__main__":
    run_cli()
