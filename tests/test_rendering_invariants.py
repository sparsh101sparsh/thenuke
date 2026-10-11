"""Exhaustive Test Suite for Rendering Invariants & Armor against Regressions.

Verifies:
1. Input normalization and defense against literal escape artifacts (\n-, \n, \t).
2. Math parity preservation and scoped delimiter matching (no line bleeding).
3. Mathematical typography fidelity (upright Roman numbers, operators, functions, and scaled exponents).
4. XML parsing resilience and automatic ExpatError recovery.
5. End-to-end PDF compilation with zero QA violations.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from scripts.diagramming.reportlab_engine import (
    normalize_and_sanitize_markdown,
    emergency_xml_repair,
    safe_paragraph,
    latex_to_reportlab_html,
    md_to_reportlab_html,
    ReferenceManualBuilder,
)
from scripts.qa.qa_audit_engine import run_qa_audit
from reportlab.lib.styles import getSampleStyleSheet


# ===========================================================================
# 1. Input Normalization & Escape Artifact Defense Tests
# ===========================================================================

class TestInputNormalization:
    """Ensures literal escape characters (\n, \n-, \t) can never corrupt output."""

    def test_bullet_escape_conversion(self):
        raw = r"Memo and Momo are playing:\n- If both are divisible\n- If only a is divisible"
        normalized = normalize_and_sanitize_markdown(raw)
        assert r"\n-" not in normalized
        assert "\n• If both are divisible" in normalized
        assert "\n• If only a is divisible" in normalized

    def test_word_attached_escape_conversion(self):
        raw = r"First line.\nSecond line is here.\nThird line follows."
        normalized = normalize_and_sanitize_markdown(raw)
        assert r"\nSecond" not in normalized
        assert "First line.\nSecond line is here.\nThird line follows." == normalized

    def test_latex_n_macro_preservation(self):
        raw = r"In math mode: $x \ne 0$ and $y \notin S$ with \noindent and \nabla."
        normalized = normalize_and_sanitize_markdown(raw)
        assert r"\ne" in normalized
        assert r"\notin" in normalized
        assert r"\noindent" in normalized
        assert r"\nabla" in normalized

    def test_code_block_escape_protection(self):
        raw = r"Code: `int x = 0;\nreturn x;` with outside text."
        normalized = normalize_and_sanitize_markdown(raw)
        assert r"`int x = 0;\nreturn x;`" in normalized

    def test_literal_tab_conversion(self):
        raw = "Item 1:\tDescription."
        normalized = normalize_and_sanitize_markdown(raw)
        assert "\t" not in normalized
        assert "    " in normalized


# ===========================================================================
# 2. Math Parity Preservation & Scoped Delimiter Matching
# ===========================================================================

class TestMathParityAndScoping:
    """Verifies that odd dollar counts, regexes, and currency signs never invert parity."""

    def test_regex_with_dollar_inside_backticks(self):
        text = "Explanation: 'meOw' matches regex `^[mM]+[eE]+[oO]+[wW]+$`. Next condition is $t (1 \le t \le 10^4)$."
        html = md_to_reportlab_html(text)
        assert '<font face="Courier" size="8.5">^[mM]+[eE]+[oO]+[wW]+$</font>' in html
        assert "<i>t</i>" in html
        assert "&le;" in html
        assert "10<super>" in html

    def test_inline_math_does_not_bleed_across_newlines(self):
        text = "Line 1: Let $x be an unclosed variable.\nLine 2: Then $y$ is an independent variable."
        html = md_to_reportlab_html(text)
        assert "<i>y</i>" in html
        assert "Line 1: Let $x be an unclosed variable." in html

    def test_currency_and_isolated_dollar_handling(self):
        text = "The entry fee is $100 and bonus is $50. Bounds are $1 \le k \le 10^9$."
        html = md_to_reportlab_html(text)
        assert "$100" in html
        assert "$50" in html
        assert "&le;" in html
        assert "10<super>" in html

    def test_escaped_dollar_preservation(self):
        text = r"Use \$HOME variable and cost is \$10. Expression: $x + y = z$."
        html = md_to_reportlab_html(text)
        assert "$HOME" in html
        assert "$10" in html
        assert "<i>x</i> + <i>y</i> = <i>z</i>" in html


# ===========================================================================
# 3. Mathematical Typography Fidelity Tests
# ===========================================================================

class TestMathTypographyFidelity:
    """Verifies AMS-LaTeX/KaTeX standard typography."""

    def test_upright_numbers_and_functions(self):
        tex = r"\gcd(a, b) = \min(x, y) + 10^9"
        html = latex_to_reportlab_html(tex)
        assert "gcd(" in html
        assert "min(" in html
        assert "10<super>" in html
        assert "<i>a</i>" in html
        assert "<i>b</i>" in html

    def test_true_minus_sign(self):
        tex = r"-10^9 \le x - y \le 10^9"
        html = latex_to_reportlab_html(tex)
        assert "&minus;10<super>" in html
        assert "<i>x</i> &minus; <i>y</i>" in html

    def test_scaled_super_and_sub(self):
        tex = r"(-1)^{a+b}S^2 \cdot a_i"
        html = latex_to_reportlab_html(tex)
        assert '<super><font size="6.5">' in html
        assert '<sub><font size="6.5">' in html
        assert "&middot;" in html

    def test_sum_and_prod_with_subscripts(self):
        tex = r"\sum_{i=1}^n a_i = \prod_{k=1}^m b_k"
        html = latex_to_reportlab_html(tex)
        assert "&Sigma;" in html
        assert "&Pi;" in html
        assert "<sub>" in html

    def test_floor_and_ceiling_functions(self):
        tex = r"\lfloor \sqrt{X} \rfloor + \lceil n/2 \rceil + \lfloor a_i / 2 \rfloor"
        html = latex_to_reportlab_html(tex)
        assert r"\lfloor" not in html
        assert r"\rfloor" not in html
        assert r"\lceil" not in html
        assert r"\rceil" not in html
        assert "floor(" in html
        assert "ceil(" in html
        assert "&radic;(<i>X</i>)" in html

    def test_latex_escaped_symbols_and_factorization(self):
        tex = r"X \% i == 0 \text{ with } p_1^{a_1} \times p_2^{a_2}"
        html = latex_to_reportlab_html(tex)
        assert r"\%" not in html
        assert "%" in html
        assert r"\times" not in html
        assert "&times;" in html
        assert '<sub><font size="6.5">1</font></sub>' in html

    def test_extended_operators_and_lcm(self):
        tex = r"f(X) = X - \lfloor X/C \rfloor + \text{lcm}(C, D) \le 10^9"
        html = latex_to_reportlab_html(tex)
        assert r"\lfloor" not in html
        assert "floor(" in html
        assert "lcm(" in html
        assert "&le;" in html

    def test_universal_macro_extinguisher(self):
        """Ensures NO backslash can ever leave latex_to_reportlab_html, even with unsupported/custom macros."""
        tex = r"\operatorname{mex}(S) + \cancel{x} + \mathcal{O}(N) + \unknownmacro{foo} + \isolatedcommand"
        html = latex_to_reportlab_html(tex)
        assert "\\" not in html
        assert "mex(" in html
        assert "foo" in html
        assert "isolatedcommand" in html

    def test_cases_and_matrix_environments(self):
        """Ensures piecewise cases and matrix environments are rendered cleanly without backslashes."""
        tex = r"\begin{cases} x & \text{if } x > 0 \\ -x & \text{otherwise} \end{cases}"
        html = latex_to_reportlab_html(tex)
        assert "\\" not in html
        assert "otherwise" in html
        assert "&gt;" in html

    def test_binomials_and_fractions(self):
        """Tests standard binomials and TeX primitive fractions."""
        tex = r"\binom{n}{k} + {n \choose 2} + {a \over b}"
        html = latex_to_reportlab_html(tex)
        assert "\\" not in html
        assert "<i>C</i>(" in html

    def test_greek_alphabet_coverage(self):
        """Verifies full Greek alphabet lowercase and uppercase support."""
        tex = r"\alpha + \beta + \Delta + \Sigma + \Omega + \pi"
        html = latex_to_reportlab_html(tex)
        assert "\\" not in html
        assert "&alpha;" in html
        assert "&Delta;" in html
        assert "&Omega;" in html
        assert "&pi;" in html

    def test_delimiter_normalizations(self):
        """Verifies triple dollars, \(...\), \[...\], and spaced dollars in markdown."""
        md = r"Bounds: $$$10^5$$$ and \( y \ge 0 \) and $ 1 \le x \le n $ with \[ \sum i \]."
        html = md_to_reportlab_html(md)
        assert "$$$" not in html
        assert r"\(" not in html
        assert r"\[" not in html
        assert "&ge;" in html
        assert "&le;" in html
        assert "&Sigma;" in html

    def test_bare_operators_outside_math(self):
        """Ensures bare LaTeX operators outside dollar signs are rendered as HTML entities."""
        md = r"Constraints: 1 \le n \le 10^5 and a \ne 0 and x \to y."
        html = md_to_reportlab_html(md)
        assert r"\le" not in html
        assert r"\ne" not in html
        assert r"\to" not in html
        assert "&le;" in html
        assert "&ne;" in html
        assert "&rarr;" in html


# ===========================================================================
# 4. XML Parsing Resilience & Emergency Repair Tests
# ===========================================================================

class TestEmergencyXMLRepair:
    """Verifies that malformed tags, brackets, and ExpatErrors are recovered safely."""

    def test_unclosed_tags_repaired(self):
        raw = "<b>Bold text without closing tag"
        repaired = emergency_xml_repair(raw)
        assert repaired.endswith("</b>")

    def test_bare_bracket_escaped(self):
        raw = "Template <vector<int>> with operator a < b && b > c."
        repaired = emergency_xml_repair(raw)
        assert "&lt;vector" in repaired
        assert "&amp;&amp;" in repaired

    def test_safe_paragraph_never_crashes(self):
        styles = getSampleStyleSheet()
        malformed = "<font face='Unknown'><b>Mismatched tag</i></font>"
        p = safe_paragraph(malformed, styles["Normal"])
        assert p is not None


# ===========================================================================
# 5. End-to-End PDF Compilation with QA Verification
# ===========================================================================

class TestEndToEndCompilationInvariants:
    """Compiles an adversarial stress document and validates zero QA violations."""

    def test_compile_adversarial_document(self):
        md_content = """# Competitive Programming Stress Test Reference Manual

**Platform:** Codeforces | **Problem ID:** STRESS-01 | **Time Limit:** 2.0 s | **Memory Limit:** 256 MB

Given string $s$ of length $n$. Matches regex `^[mM]+[eE]+[oO]+[wW]+$`.
Bounds: $t (1 \le t \le 10^4)$ and $x \ne 0$ with $y \notin S$.
Items details:\\n- If both $a$ and $b$ are divisible by $k$, print "Both".\\n- If only $a$ is divisible, print "Memo".
Input format:\\nFirst line contains $t$.\\nSecond line contains names.

:::sample 1
#### Input
```
3
10 20
30 40
```
#### Output
```
YES
NO
```
#### Explanation
Matches regex `^[a-z]+$` and formula $(-1)^{a+b}S^2 \le 10^{18}$.
:::

[MENTAL MODEL]
Bitwise invariant: check if $(n \ \& \ (n - 1)) \ne 0$. In $O(1)$ time.

• Algorithm: Trial division up to $\sqrt{a+b} \approx 4.5 \cdot 10^5$.
• Complexity Analysis: Time: $O(1)$ | Space: $O(1)$
"""

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = Path(f.name)

        try:
            builder = ReferenceManualBuilder(output_path=pdf_path, topic="CP Stress Test")
            builder.compile(md_content)
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0

            # Run QA audit
            report = run_qa_audit(pdf_path)
            assert report.overall_passed is True
            assert report.pass1_visual.error_count == 0
            assert report.pass2_textual.error_count == 0
            assert len(report.pass2_textual.rendering_violations) == 0
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
