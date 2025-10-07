"""
Streaming processing for papers to reduce memory usage.
"""

from typing import Dict, List, Generator
from .services.translation_service import TranslationService
from .utils import log


def process_papers_streaming(paper_ids: List[str]) -> Generator[Dict, None, None]:
    """Process papers one at a time to reduce memory usage."""
    for paper_id in paper_ids:
        try:
            # Process single paper
            result = process_single_paper(paper_id)
            yield result
        except Exception as e:
            log(f"Failed to process {paper_id}: {e}")
            yield {"id": paper_id, "status": "failed", "error": str(e)}


def process_single_paper(paper_id: str) -> Dict:
    """Process a single paper."""
    # Load paper data
    paper = load_paper(paper_id)

    # Translate paper
    translation = translate_paper(paper)

    # Save translation
    save_translation(paper_id, translation)

    return {"id": paper_id, "status": "completed"}


def load_paper(paper_id: str) -> Dict:
    """Load paper data."""
    import json
    import os

    paper_file = f"data/selected/{paper_id}.json"
    if os.path.exists(paper_file):
        with open(paper_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"id": paper_id, "title": "", "abstract": "", "body": []}


def translate_paper(paper: Dict) -> Dict:
    """Translate a paper."""
    svc = TranslationService()
    return {
        "id": paper["id"],
        "title_en": svc.translate_field(paper.get("title", ""), dry_run=False),
        "abstract_en": svc.translate_field(paper.get("abstract", ""), dry_run=False),
        "body_en": [
            svc.translate_field(p, dry_run=False) for p in paper.get("body", [])
        ],
    }


def save_translation(paper_id: str, translation: Dict):
    """Save translation."""
    import json
    import os

    os.makedirs("data/translated", exist_ok=True)
    translation_file = f"data/translated/{paper_id}.json"
    with open(translation_file, "w", encoding="utf-8") as f:
        json.dump(translation, f, indent=2, ensure_ascii=False)
