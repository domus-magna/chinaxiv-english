from src.translate import translate_field


def test_translate_field_dry_run_preserves_math():
    zh = "标题 $x+y$ 和 $$E=mc^2$$"
    out = translate_field(zh, model="ignored", glossary=[], dry_run=True)
    assert "$x+y$" in out
    assert "$$E=mc^2$$" in out

