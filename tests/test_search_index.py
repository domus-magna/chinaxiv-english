from src.search_index import build_index


def test_build_index_fields():
    items = [
        {"id": "1", "title_en": "Title", "creators": ["A"], "abstract_en": "abc", "subjects": ["s"], "date": "2025-01-01"}
    ]
    idx = build_index(items)
    assert idx and set(idx[0].keys()) == {"id", "title", "authors", "abstract", "subjects", "date"}

