from __future__ import annotations

import argparse
import glob
import os
import shutil
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils import ensure_dir, log, read_json, write_text


def load_translated() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    flagged_count = 0

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
        # Fallback: simple newline to <br> conversion
        def simple_markdown(text):
            return text.replace("\n\n", "</p><p>").replace("\n", "<br>")

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

    # Index page
    tmpl_index = env.get_template("index.html")
    html_index = tmpl_index.render(items=items, root=".")
    write_text(os.path.join(base_out, "index.html"), html_index)

    # Monitor page
    tmpl_monitor = env.get_template("monitor.html")
    html_monitor = tmpl_monitor.render(root=".")
    write_text(os.path.join(base_out, "monitor.html"), html_monitor)

    # Item pages
    tmpl_item = env.get_template("item.html")
    for it in items:
        out_dir = os.path.join(base_out, "items", it["id"])
        ensure_dir(out_dir)

        # Choose best-available body markdown for preview
        if it.get("body_md"):
            it["formatted_body_md"] = it["body_md"]
        elif it.get("body_en"):
            it["formatted_body_md"] = format_translation_to_markdown(it)

        html = tmpl_item.render(item=it, root="../..")
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
