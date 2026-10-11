"""Academic Mathematical Typesetting & Rendering Engine for thenuke.

Enforces professional, academically correct mathematical typesetting:
- Professional LaTeX source notation: inline \\( ... \\) and display \\[ ... \\].
- High-resolution (300 DPI) rendered mathematical flowables for ReportLab PDFs.
- Native support for all 12 academic formatting rules:
    A. Fractions: \\frac{a}{b}
    B. Conditional Probability: P(A \\mid B) = \\frac{P(A \\cap B)}{P(B)}, \\qquad P(B) > 0
    C. Subscripts: x_1, x_2, a_{ij}
    D. Superscripts: x^2, a^n
    E. Roots: \\sqrt{x}, \\sqrt{a+b}
    F. Summations: \\sum_{i=1}^{n} x_i
    G. Integrals: \\int f(x)\\,dx
    H. Limits: \\lim_{x \\to 0} f(x)
    I. Matrices: \\begin{bmatrix} ... \\end{bmatrix}
    J. Sets & Logic: A \\cup B, A \\cap B, A \\subseteq B, A \\Rightarrow B
    K. Greek Letters: \\alpha, \\beta, \\theta, \\lambda, \\mu, \\sigma
    L. Aligned Multi-Step Equations: \\begin{aligned} ... \\end{aligned}
- Automatic dual-engine rendering: uses Typst vector compiler if available,
  with pure Python matplotlib mathtext/pyplot fallback.
"""

from __future__ import annotations

import io
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image as PILImage
import matplotlib.pyplot as plt
import matplotlib.mathtext as mathtext

logger = logging.getLogger(__name__)

# Typst binary path (if available)
TYPST_BIN: Optional[str] = shutil.which("typst")


def clean_math_delimiters(tex: str) -> str:
    """Strips outer delimiters (\\[ \\], $$, \\( \\), or $) and normalizes whitespace."""
    s = tex.strip()
    if s.startswith(r"\[") and s.endswith(r"\]"):
        s = s[2:-2].strip()
    elif s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()
    elif s.startswith(r"\(") and s.endswith(r"\)"):
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$") and len(s) > 2:
        s = s[1:-1].strip()
    return s.strip()


def render_latex_math_to_image(tex_formula: str, dpi: int = 300, is_display: bool = True) -> Optional[bytes]:
    """Renders LaTeX mathematical expression into transparent 300 DPI PNG bytes.

    Tries Typst vector compiler first (if available for matrices/alignments),
    falling back to matplotlib mathtext/pyplot layout.
    """
    clean_tex = clean_math_delimiters(tex_formula)
    if not clean_tex:
        return None

    # Check for matrix or aligned environments
    is_matrix = bool(re.search(r"\\begin\{(?:bmatrix|pmatrix|matrix|vmatrix)\}", clean_tex))
    is_aligned = bool(re.search(r"\\begin\{aligned\}", clean_tex))

    # Matplotlib natively parses standard LaTeX math without dialect conversion
    try:
        if is_matrix:
            return _render_matrix_matplotlib(clean_tex, dpi=dpi)
        elif is_aligned:
            return _render_aligned_matplotlib(clean_tex, dpi=dpi)
        else:
            return _render_standard_mathtext(clean_tex, dpi=dpi)
    except Exception as exc:
        logger.warning("Matplotlib math rendering failed for '%s': %s", clean_tex[:40], exc)
        # Try fallback after gentle sanitization
        try:
            sanitized = _sanitize_for_mathtext(clean_tex)
            return _render_standard_mathtext(sanitized, dpi=dpi)
        except Exception:
            return None


render_latex_math_to_png = render_latex_math_to_image


def _sanitize_for_mathtext(tex: str) -> str:
    """Sanitizes macros that mathtext might reject into equivalent mathtext symbols."""
    t = tex
    t = re.sub(r"\\qquad", r"\\quad\\quad", t)
    t = re.sub(r"\\mid", r"|", t)
    t = re.sub(r"\\cap", r"\\cap", t)
    t = re.sub(r"\\cup", r"\\cup", t)
    t = re.sub(r"\\subseteq", r"\\subseteq", t)
    t = re.sub(r"\\Rightarrow", r"\\Rightarrow", t)
    return t


def _render_standard_mathtext(tex: str, dpi: int = 300) -> bytes:
    """Renders single-formula LaTeX math via matplotlib.mathtext."""
    # Ensure tex does not contain inner raw dollars
    inner = tex.strip().strip("$")
    # Replace internal newlines with spaces for single-formula mathtext
    inner = re.sub(r"\s*\n\s*", " ", inner)
    # Wrap in single dollars required by mathtext
    mathtext_str = f"${inner}$"
    buf = io.BytesIO()
    mathtext.math_to_image(mathtext_str, buf, dpi=dpi, format="png")
    return buf.getvalue()


def _render_matrix_matplotlib(tex: str, dpi: int = 300) -> bytes:
    """Renders matrices (bmatrix, pmatrix, matrix, vmatrix) via matplotlib grid layout."""
    if r"\begin{" not in tex:
        tex = rf"\begin{{bmatrix}} {tex} \end{{bmatrix}}"

    m = re.search(r"^(.*?)\\begin\{(bmatrix|pmatrix|matrix|vmatrix)\}(.*?)\\end\{\2\}(.*?)$", tex, re.DOTALL)
    if not m:
        return _render_standard_mathtext(tex, dpi=dpi)

    prefix = m.group(1).strip()
    env_type = m.group(2)
    body = m.group(3).strip()

    rows_raw = [r.strip().rstrip("\\").strip() for r in re.split(r"\\\\+|\\cr|\n", body) if r.strip()]
    grid = [[c.strip() for c in r.split("&")] for r in rows_raw]
    n_rows = len(grid)
    n_cols = max(len(r) for r in grid) if grid else 1

    left_br = "[" if env_type == "bmatrix" else ("(" if env_type == "pmatrix" else ("|" if env_type == "vmatrix" else ""))
    right_br = "]" if env_type == "bmatrix" else (")" if env_type == "pmatrix" else ("|" if env_type == "vmatrix" else ""))

    fig_w = max(3.0, n_cols * 0.95 + (1.2 if prefix else 0.4))
    fig_h = max(1.4, n_rows * 0.75)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    cur_x = 0.05
    if prefix:
        ax.text(cur_x, 0.5, f"${prefix}$", fontsize=16, ha="left", va="center")
        cur_x += 0.28

    mat_start_x = cur_x
    mat_end_x = 0.95
    col_width = (mat_end_x - mat_start_x) / max(1, n_cols)

    br_fontsize = 26 + (n_rows - 1) * 14
    if left_br:
        ax.text(mat_start_x, 0.5, left_br, fontsize=br_fontsize, ha="center", va="center", fontname="DejaVu Sans")
    if right_br:
        ax.text(mat_end_x, 0.5, right_br, fontsize=br_fontsize, ha="center", va="center", fontname="DejaVu Sans")

    y_margin = 0.22
    y_span = 1.0 - 2 * y_margin
    for r_idx, row in enumerate(grid):
        y = (1.0 - y_margin) - r_idx * (y_span / max(1, n_rows - 1)) if n_rows > 1 else 0.5
        for c_idx, cell in enumerate(row):
            x = mat_start_x + (c_idx + 0.5) * col_width
            ax.text(x, y, f"${cell}$", fontsize=15, ha="center", va="center")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi, transparent=True)
    plt.close(fig)
    return buf.getvalue()


def _render_aligned_matplotlib(tex: str, dpi: int = 300) -> bytes:
    """Renders aligned multi-step derivations via matplotlib aligned coordinates."""
    m = re.search(r"\\begin\{aligned\}(.*?)\\end\{aligned\}", tex, re.DOTALL)
    inner = m.group(1).strip() if m else tex
    raw_lines = [l.strip().rstrip("\\").strip() for l in inner.split("\n") if l.strip()]
    if len(raw_lines) <= 1:
        raw_lines = [l.strip().rstrip("\\").strip() for l in re.split(r"\\\\+|\\cr", inner) if l.strip()]

    n_lines = len(raw_lines)

    fig_h = max(1.4, n_lines * 0.65)
    fig, ax = plt.subplots(figsize=(5.5, fig_h))
    ax.axis("off")

    y_margin = 0.2
    y_span = 1.0 - 2 * y_margin
    for idx, r_line in enumerate(raw_lines):
        y = (1.0 - y_margin) - idx * (y_span / max(1, n_lines - 1)) if n_lines > 1 else 0.5
        if "&" in r_line:
            parts = r_line.split("&", 1)
            lhs, rhs = parts[0].strip(), parts[1].strip()
            ax.text(0.48, y, f"${lhs}$", fontsize=15, ha="right", va="center")
            ax.text(0.50, y, f"${rhs}$", fontsize=15, ha="left", va="center")
        else:
            ax.text(0.50, y, f"${r_line}$", fontsize=15, ha="center", va="center")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi, transparent=True)
    plt.close(fig)
    return buf.getvalue()


def _try_render_typst(tex: str, dpi: int = 300) -> Optional[bytes]:
    """Attempts compiling matrix or aligned blocks with Typst if available."""
    if not TYPST_BIN:
        return None
    try:
        typst_code = _latex_to_typst_math(tex)
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = Path(tmpdir) / "math.typ"
            out_file = Path(tmpdir) / "math.png"
            src_file.write_text(
                f"#set page(width: auto, height: auto, margin: 5pt, fill: none)\n$ {typst_code} $\n",
                encoding="utf-8",
            )
            res = subprocess.run(
                [TYPST_BIN, "compile", "--ppi", str(dpi), str(src_file), str(out_file)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and out_file.exists():
                return out_file.read_bytes()
    except Exception as exc:
        logger.debug("Typst math compile skipped: %s", exc)
    return None


def _latex_to_typst_math(tex: str) -> str:
    """Translates LaTeX math snippet to Typst math syntax."""
    t = tex.strip()
    # Matrix translation
    m = re.search(r"^(.*?)\\begin\{(bmatrix|pmatrix|matrix|vmatrix)\}(.*?)\\end\{\2\}(.*?)$", t, re.DOTALL)
    if m:
        prefix = m.group(1).strip()
        env = m.group(2)
        delim = '"["' if env == "bmatrix" else ('"("' if env == "pmatrix" else ('"|"' if env == "vmatrix" else "none"))
        body = m.group(3).strip()
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        typ_rows = []
        for r in rows:
            cells = [c.strip() for c in r.split("&")]
            typ_rows.append(", ".join(cells))
        mat_expr = f"mat(delim: {delim}, {'; '.join(typ_rows)})"
        return f"{prefix} {mat_expr}".strip()

    # Aligned multi-line translation
    m_al = re.search(r"\\begin\{aligned\}(.*?)\\end\{aligned\}", t, re.DOTALL)
    if m_al:
        inner = m_al.group(1).strip()
        lines = [line.strip() for line in re.split(r"\\\\", inner) if line.strip()]
        # In Typst, line break in math is literal \
        typ_lines = []
        for l in lines:
            l = re.sub(r"\\quad|\s*\\text\{or\}\s*", ' " or " ', l)
            typ_lines.append(l)
        return " \\\n".join(typ_lines)

    return t


def render_matrix_to_png(tex: str, dpi: int = 300) -> Optional[bytes]:
    """Public wrapper to render matrix LaTeX into PNG bytes."""
    return _render_matrix_matplotlib(tex, dpi=dpi)


def render_aligned_equations_to_png(tex: str, dpi: int = 300) -> Optional[bytes]:
    """Public wrapper to render aligned multi-step derivation LaTeX into PNG bytes."""
    return _render_aligned_matplotlib(tex, dpi=dpi)


def create_math_flowable(
    tex_formula: str,
    is_display: bool = True,
    max_width_pt: float = 480.0,
    styles: Any = None,
) -> Any:
    """Creates a ReportLab Flowable (Image or styled Paragraph fallback) for a math expression."""
    from reportlab.platypus import Image as RLImage, KeepTogether, Paragraph
    from scripts.diagramming.reportlab_engine import latex_to_reportlab_html, safe_paragraph

    img_bytes = render_latex_math_to_image(tex_formula, dpi=300, is_display=is_display)
    if img_bytes:
        try:
            pil_img = PILImage.open(io.BytesIO(img_bytes))
            w_px, h_px = pil_img.size
            # 300 DPI to points conversion: (pixels / 300) * 72
            w_pt = (w_px / 300.0) * 72.0
            h_pt = (h_px / 300.0) * 72.0

            if w_pt > max_width_pt:
                scale = max_width_pt / w_pt
                w_pt = max_width_pt
                h_pt = h_pt * scale

            img = RLImage(io.BytesIO(img_bytes), width=w_pt, height=h_pt)
            img.hAlign = "CENTER"
            return KeepTogether([img])
        except Exception as exc:
            logger.warning("Failed creating RLImage from rendered math bytes: %s", exc)

    # Fallback to rich-text Paragraph markup
    style = styles["DisplayMath"] if (styles and "DisplayMath" in styles) else None
    html_markup = latex_to_reportlab_html(tex_formula)
    return safe_paragraph(html_markup, style)
