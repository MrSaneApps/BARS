#!/usr/bin/env python3
"""
Convert inline LaTeX math ($...$) and unrendered TeX escapes (\%, \text{...}, \mu, etc.)
in BARS review Markdown files into clean GitHub-rendered Unicode so that all characters
render natively in GitHub Issue comments and Markdown viewers without MathJax breakage.
"""

import re
import sys
from pathlib import Path

SUP_MAP = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")


def _to_sup(m: re.Match) -> str:
    return m.group(1).translate(SUP_MAP)


def clean_github_markdown(txt: str) -> str:
    def repl_math(m: re.Match) -> str:
        s = m.group(1)
        s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
        s = s.replace(r"\%", "%")
        s = s.replace(r"\{", "{").replace(r"\}", "}")
        s = s.replace(r"\ ", " ")
        s = s.replace(r"\mu", "µ")
        s = s.replace(r"\varepsilon", "ε")
        s = s.replace(r"\epsilon", "ε")
        s = s.replace(r"\lambda", "λ")
        s = s.replace(r"\Lambda", "Λ")
        s = s.replace(r"\alpha", "α")
        s = s.replace(r"\beta", "β")
        s = s.replace(r"\gamma", "γ")
        s = s.replace(r"\delta", "δ")
        s = s.replace(r"\Delta", "Δ")
        s = s.replace(r"\omega", "ω")
        s = s.replace(r"\rho", "ρ")
        s = s.replace(r"\sigma", "σ")
        s = s.replace(r"\psi", "ψ")
        s = s.replace(r"\kappa", "κ")
        s = s.replace(r"\tau", "τ")
        s = s.replace(r"\chi", "χ")
        s = s.replace(r"\ln", "ln")
        s = s.replace(r"\log", "log")
        s = s.replace(r"\exp", "exp")
        s = s.replace(r"\max", "max")
        s = s.replace(r"\min", "min")
        s = s.replace(r"\sum", "∑")
        s = s.replace(r"\times", "×")
        s = s.replace(r"\pm", "±")
        s = s.replace(r"\le", "≤")
        s = s.replace(r"\leq", "≤")
        s = s.replace(r"\ge", "≥")
        s = s.replace(r"\geq", "≥")
        s = s.replace(r"\neq", "≠")
        s = s.replace(r"\approx", "≈")
        s = s.replace(r"\sim", "~")
        s = s.replace(r"\in", "∈")
        s = s.replace(r"\to", "→")
        s = s.replace(r"\rightarrow", "→")
        s = s.replace(r"\mid", "|")
        s = s.replace(r"\dots", "…")
        s = s.replace(r"\cdots", "⋯")
        s = s.replace(r"^\circ", "°")
        s = s.replace("--", "–")
        s = re.sub(r"\^\{([0-9+-]+)\}", _to_sup, s)
        s = re.sub(r"\^([0-9+-])\b", _to_sup, s)
        s = re.sub(r"\^([0-9+-])", _to_sup, s)
        s = re.sub(r"_\{([^}]*)\}", r"_\1", s)
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"~\s+(?=\d)", "~", s)
        return s

    out = re.sub(r"\$([^$]+)\$", repl_math, txt)
    out = out.replace(r"\%", "%")
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        content = p.read_text(encoding="utf-8")
        cleaned = clean_github_markdown(content)
        p.write_text(cleaned, encoding="utf-8")
        print(f"Cleaned {p} (remaining $: {cleaned.count('$')})")
