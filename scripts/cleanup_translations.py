#!/usr/bin/env python3
"""
Clean up poor quality translations from the site.
Remove abstract-only and poorly formatted translations.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

def is_abstract_only(translation: Dict[str, Any]) -> bool:
    """Check if translation is abstract-only (no body content)."""
    return translation.get('body_en') is None or translation.get('body_en') == []

def is_poor_format(translation: Dict[str, Any]) -> bool:
    """Check if translation has poor formatting."""
    abstract = translation.get('abstract_en', '')
    
    # Check for common poor formatting indicators
    poor_indicators = [
        # Chinese text not translated
        '作者：', '提交时间：', '摘要:', '分类：', '引用：', 'DOI:', 'CSTR:',
        '推荐引用方式：', '版本历史', '下载全文', '来自：', '关键词',
        # Malformed formatting
        '&gt;&gt;', '&lt;', '&amp;',
        # Very short abstracts (likely incomplete)
        len(abstract) < 100,
        # Abstract contains mostly metadata
        abstract.count('：') > 5,
        # Contains raw Chinese characters mixed with English
        any(ord(char) > 127 for char in abstract[:200]) and 'Abstract:' not in abstract[:200]
    ]
    
    return any(poor_indicators)

def is_low_quality(translation: Dict[str, Any]) -> bool:
    """Check if translation is low quality."""
    abstract = translation.get('abstract_en', '')
    
    # Very short content
    if len(abstract) < 50:
        return True
    
    # Mostly Chinese characters (not translated)
    chinese_chars = sum(1 for char in abstract if ord(char) > 127)
    if chinese_chars > len(abstract) * 0.7:
        return True
    
    # Contains raw metadata formatting
    if 'ChinaXiv:' in abstract and 'Abstract:' not in abstract:
        return True
    
    return False

def analyze_translations() -> Dict[str, List[str]]:
    """Analyze all translations and categorize them."""
    translated_dir = Path("data/translated")
    
    categories = {
        'abstract_only': [],
        'poor_format': [],
        'low_quality': [],
        'good': []
    }
    
    for json_file in translated_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                translation = json.load(f)
            
            paper_id = translation.get('id', json_file.stem)
            
            if is_abstract_only(translation):
                categories['abstract_only'].append(paper_id)
            elif is_poor_format(translation):
                categories['poor_format'].append(paper_id)
            elif is_low_quality(translation):
                categories['low_quality'].append(paper_id)
            else:
                categories['good'].append(paper_id)
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    return categories

def remove_translations(paper_ids: List[str], dry_run: bool = True) -> None:
    """Remove specified translations from filesystem and site."""
    removed_count = 0
    
    for paper_id in paper_ids:
        # Remove from data/translated/
        translated_file = Path(f"data/translated/{paper_id}.json")
        if translated_file.exists():
            if not dry_run:
                translated_file.unlink()
            print(f"{'Would remove' if dry_run else 'Removed'}: {translated_file}")
            removed_count += 1
        
        # Remove from site/items/
        site_dir = Path(f"site/items/{paper_id}")
        if site_dir.exists():
            if not dry_run:
                import shutil
                shutil.rmtree(site_dir)
            print(f"{'Would remove' if dry_run else 'Removed'}: {site_dir}")
    
    return removed_count

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up poor quality translations")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would be removed without actually removing")
    parser.add_argument("--execute", action="store_true", help="Actually remove the files (overrides --dry-run)")
    parser.add_argument("--category", choices=['abstract_only', 'poor_format', 'low_quality', 'all'], 
                       default='all', help="Which category to remove")
    
    args = parser.parse_args()
    
    if args.execute:
        args.dry_run = False
    
    print("Analyzing translations...")
    categories = analyze_translations()
    
    print("\nTranslation Analysis:")
    print("=" * 50)
    for category, papers in categories.items():
        print(f"{category.replace('_', ' ').title()}: {len(papers)} papers")
    
    # Determine which papers to remove
    papers_to_remove = []
    if args.category == 'all':
        papers_to_remove = (categories['abstract_only'] + 
                           categories['poor_format'] + 
                           categories['low_quality'])
    else:
        papers_to_remove = categories[args.category]
    
    print(f"\nPapers to remove ({args.category}): {len(papers_to_remove)}")
    
    if papers_to_remove:
        print("\nFirst 10 papers that would be removed:")
        for paper_id in papers_to_remove[:10]:
            print(f"  - {paper_id}")
        if len(papers_to_remove) > 10:
            print(f"  ... and {len(papers_to_remove) - 10} more")
        
        if not args.dry_run:
            print(f"\nRemoving {len(papers_to_remove)} papers...")
            removed_count = remove_translations(papers_to_remove, dry_run=False)
            print(f"Removed {removed_count} translation files")
            
            # Regenerate site
            print("Regenerating site...")
            os.system("python3 -m src.render")
            os.system("python3 -m src.search_index")
            print("Site regenerated!")
        else:
            print(f"\nDry run - no files removed. Use --execute to actually remove them.")
    else:
        print("No papers to remove!")

if __name__ == "__main__":
    main()
