from pathlib import Path
import io
import tarfile

from src.translate import translate_record


def make_tex_tar(tmp_path: Path, content: str) -> str:
    tar_path = tmp_path / "paper.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        info = tarfile.TarInfo("main.tex")
        data = content.encode("utf-8")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return str(tar_path)


def test_translate_record_with_latex_body_dry_run(tmp_path, monkeypatch):
    tex = r"""
\\documentclass{article}
\\begin{document}
这是一段，含有公式 $a^2+b^2=c^2$。

还有一段。
\\end{document}
""".strip()
    tar_path = make_tex_tar(tmp_path, tex)
    rec = {
        "id": "X2",
        "title": "测试标题",
        "abstract": "测试摘要",
        "license": {"raw": "CC BY"},
        "oai_identifier": "oai:chinaxiv.org:2025-0002",
        "files": {"latex_source_path": tar_path, "pdf_path": None},
    }
    out = translate_record(rec, model="deepseek/deepseek-v3.2-exp", glossary=[], dry_run=True)
    assert out["body_en"] is not None and len(out["body_en"]) >= 1
    # math preserved in dry-run
    assert "$a^2+b^2=c^2$" in "\n".join(out["body_en"]) 

