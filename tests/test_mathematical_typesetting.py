"""Test Suite for Professional Academic Mathematical Typesetting & LaTeX Rendering.

Validates:
1. Core Requirement: Proper mathematical notation in LaTeX (inline \\( ... \\), display \\[ ... \\]).
2. Rules A through L:
   - A. Fractions (\\frac{a}{b})
   - B. Conditional Probability (P(A \\mid B) = \\frac{P(A \\cap B)}{P(B)}, \\qquad P(B) > 0)
   - C. Subscripts (x_1, x_2, a_{ij})
   - D. Superscripts & Powers (x^2, a^n)
   - E. Roots (\\sqrt{x}, \\sqrt{a+b})
   - F. Summations (\\sum_{i=1}^n x_i)
   - G. Integrals (\\int f(x)\\,dx)
   - H. Limits (\\lim_{x \\to 0} f(x))
   - I. Matrices (\\begin{bmatrix})
   - J. Sets & Logic (\\cup, \\cap, \\subseteq, \\Rightarrow)
   - K. Greek Letters (\\alpha, \\beta, \\theta, \\lambda, \\mu, \\sigma)
   - L. Aligned Multi-Step Derivations (\\begin{aligned})
3. Acceptance Test: Explain conditional probability and formula preserving P(B) > 0.
4. Visual PDF flowable rendering (no raw unrendered macros in output).
5. Pass 2 Textual QA detection of informal linear math approximations.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

from scripts.diagramming.math_renderer import (
    render_latex_math_to_image,
    create_math_flowable,
    render_matrix_to_png,
    render_aligned_equations_to_png,
)
from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
from scripts.qa.qa_audit_engine import run_qa_audit, run_pass2_textual
from scripts.synthesis.math_explainer import (
    explain_conditional_probability,
    explain_math_topic,
)


def test_acceptance_conditional_probability_explanation():
    """Acceptance Test: 'Explain conditional probability and write its formula.'

    Must contain:
    - P(A \\mid B) = \\frac{P(A \\cap B)}{P(B)}, \\qquad P(B) > 0
    - Readable explanation strictly preserving condition P(B) > 0
    - Explicit distinction between P(A \\mid B) and P(A)/P(B)
    - Zero informal approximations like P(A/B) = P(AB)/P(B)
    """
    explanation = explain_conditional_probability()

    # 1. Contains canonical formula
    assert r"P(A \mid B) = \frac{P(A \cap B)}{P(B)}" in explanation
    assert r"P(B) > 0" in explanation

    # 2. Contains condition preservation rationale
    assert "P(B) > 0" in explanation
    assert "undefined" in explanation.lower() or "impossible" in explanation.lower()

    # 3. Contains non-equivalence distinction
    assert r"P(A \mid B)" in explanation
    assert r"\frac{P(A)}{P(B)}" in explanation
    assert "non-equivalent" in explanation.lower() or "not equivalent" in explanation.lower()

    # 4. Zero informal plain-text approximations
    assert not re.search(r"\bP\([A-Z]/[A-Z]\)\s*=", explanation)
    assert not re.search(r"\bP\([A-Z]\|[A-Z]\)\s*=\s*P\([A-Z][A-Z]\)", explanation)


def test_rules_a_to_l_specifications():
    """Validates that math expressions follow Rules A through L."""
    explanation = explain_conditional_probability()

    # Rule A: Fractions
    assert r"\frac{a}{b}" in explanation

    # Rule B: Conditional probability
    assert r"P(A \mid B)" in explanation

    # Rule C: Subscripts
    assert r"p_{11}" in explanation or r"B_1" in explanation

    # Rule D: Superscripts
    assert r"\sigma_1^2" in explanation or r"\sigma_2^2" in explanation

    # Rule F: Summations with proper limits
    assert r"\sum_{i=1}^{n}" in explanation

    # Rule I: Matrices (bmatrix)
    assert r"\begin{bmatrix}" in explanation
    assert r"\end{bmatrix}" in explanation

    # Rule L: Aligned multi-step equations
    assert r"\begin{aligned}" in explanation
    assert r"\end{aligned}" in explanation


def test_math_renderer_display_flowable():
    """Verifies that create_math_flowable converts display LaTeX into image flowables."""
    flowable = create_math_flowable(r"P(A \mid B) = \frac{P(A \cap B)}{P(B)}", is_display=True)
    assert flowable is not None
    inner_img = flowable._content[0] if hasattr(flowable, "_content") else flowable
    assert hasattr(inner_img, "drawWidth")
    assert hasattr(inner_img, "drawHeight")
    assert inner_img.drawWidth > 0
    assert inner_img.drawHeight > 0


def test_math_renderer_matrix():
    """Verifies matrix rendering via bmatrix parser."""
    png_bytes = render_matrix_to_png(r"p_{11} & p_{12} \\ p_{21} & p_{22}")
    assert png_bytes is not None
    assert len(png_bytes) > 100


def test_math_renderer_aligned():
    """Verifies aligned multi-step derivation rendering."""
    body = r"""
    x^2 - 5x + 6 &= 0 \\
    (x-2)(x-3) &= 0 \\
    x &= 2 \quad \text{or} \quad x = 3
    """
    png_bytes = render_aligned_equations_to_png(body)
    assert png_bytes is not None
    assert len(png_bytes) > 100


def test_pdf_math_compilation_and_qa_clean(tmp_path: Path):
    """End-to-end: Compiles math markdown into PDF and runs dual-pass QA audit."""
    md_content = explain_conditional_probability()
    out_pdf = tmp_path / "Conditional_Probability_Academic.pdf"

    builder = ReferenceManualBuilder(out_pdf, topic="Conditional Probability")
    compiled_path = builder.compile(md_content)

    assert compiled_path.exists()
    assert compiled_path.stat().st_size > 5000

    report = run_qa_audit(compiled_path, profile="math")
    assert report.overall_passed, f"QA failed: {report.summary}"
    assert report.pass1_visual.error_count == 0
    assert report.pass2_textual.error_count == 0
    assert len(report.pass2_textual.rendering_violations) == 0


def test_qa_audit_flags_informal_math(tmp_path: Path):
    """Verifies that Pass 2 QA catches and rejects informal linear math approximations."""
    bad_md = tmp_path / "bad_math.md"
    bad_md.write_text(
        "# Faulty Probability Notes\n\n"
        "Prepared by @issparsh @sumitsingh097\n\n"
        "Formula: P(A/B) = P(AB)/P(B), where P(B) > 0\n\n"
        "Summation: sum(i=1 to n) xi\n\n"
        "Root: sqrt(a+b)\n",
        encoding="utf-8",
    )

    result = run_pass2_textual(bad_md, profile="math")
    assert not result.passed
    assert any("Informal linear math approximation" in v for v in result.rendering_violations)
