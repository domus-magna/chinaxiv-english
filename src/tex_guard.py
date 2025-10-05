from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


MATH_TOKEN_FMT = "⟪MATH_{:04d}⟫"


MATH_PATTERNS = [
    # Display $$...$$ (greedy but non-nesting)
    re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
    # Inline $...$
    re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$", re.DOTALL),
    # \[ ... \]
    re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
    # \( ... \)
    re.compile(r"\\\((.+?)\\\)", re.DOTALL),
    # Environments: equation, align, gather, etc.
    re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.+?)\\end\{\1\}", re.DOTALL),
    # Citation commands - preserve exactly
    re.compile(r"\\cite\{[^}]*\}", re.DOTALL),
    re.compile(r"\\ref\{[^}]*\}", re.DOTALL),
    re.compile(r"\\eqref\{[^}]*\}", re.DOTALL),
    re.compile(r"\\label\{[^}]*\}", re.DOTALL),
    # Other common LaTeX commands that should be preserved
    re.compile(r"\\textbf\{[^}]*\}", re.DOTALL),
    re.compile(r"\\textit\{[^}]*\}", re.DOTALL),
    re.compile(r"\\emph\{[^}]*\}", re.DOTALL),
    re.compile(r"\\section\{[^}]*\}", re.DOTALL),
    re.compile(r"\\subsection\{[^}]*\}", re.DOTALL),
    re.compile(r"\\subsubsection\{[^}]*\}", re.DOTALL),
]


@dataclass
class Masking:
    token: str
    content: str


def mask_math(text: str) -> Tuple[str, List[Masking]]:
    mappings: List[Masking] = []
    out = text

    # Apply patterns sequentially; replace matches with stable tokens
    for pat in MATH_PATTERNS:
        def _repl(m: re.Match) -> str:
            token = MATH_TOKEN_FMT.format(len(mappings) + 1)
            mappings.append(Masking(token=token, content=m.group(0)))
            return token

        out = pat.sub(_repl, out)
    return out, mappings


def unmask_math(text: str, mappings: List[Masking]) -> str:
    out = text
    for m in mappings:
        out = out.replace(m.token, m.content)
    return out


def verify_token_parity(source_mappings: List[Masking], translated_text: str) -> bool:
    # Ensure each token appears exactly once in translation
    ok = True
    for m in source_mappings:
        count = translated_text.count(m.token)
        if count != 1:
            ok = False
            break
    return ok

