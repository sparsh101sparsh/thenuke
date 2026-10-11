"""Academic Mathematical Explanation & Typesetting Module for thenuke.

Produces academically rigorous educational content and reference explanations
following professional university textbook standards:
- 100% proper LaTeX notation: inline \\( ... \\) and display \\[ ... \\].
- Zero informal plain-text approximations (never a/b, P(A|B) = P(A B)/P(B), sum(i=1 to n)).
- Strict preservation of mathematical meaning, conditions (e.g. P(B) > 0), and grouping.
- Dual-register cadence: natural Roman Hinglish narrative bridges + formal technical English.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def explain_conditional_probability(branding: str = "Prepared by @issparsh @sumitsingh097") -> str:
    """Produces a rigorous academic explanation and formula for conditional probability."""
    template = r"""# Conditional Probability: Academic Reference Manual

**Topic:** Probability Theory & Mathematical Foundations
**Edition:** Production Reference Edition
**Prepared by:** __BRANDING__

---

## 1. Executive Definition & Theoretical Foundations

Technically bolo toh, conditional probability ek event \(A\) ki occurrence probability describe karti hai given that another event \(B\) has already occurred. In this setting, the original sample space \(\Omega\) effectively collapses onto the conditioning subspace \(B\).

The foundational formula for the conditional probability of \(A\), given \(B\), is:

\[
P(A \mid B) = \frac{P(A \cap B)}{P(B)},
\qquad P(B) > 0
\]

### Strict Boundary Conditions & Invariants
- **Non-Zero Conditioning Invariant:** The condition \(P(B) > 0\) is strictly mandatory. Agar conditioning event impossible ho (\(P(B) = 0\)), then the conditional probability is mathematically undefined because division by zero is strictly prohibited.
- **Joint Intersection vs Product:** The numerator represents the joint probability of the intersection \(P(A \cap B)\). For independent events, \(P(A \cap B) = P(A) \cdot P(B)\), which simplifies the expression to \(P(A \mid B) = P(A)\).
- **Critical Distinction:** Never confuse \(P(A \mid B)\) with the ratio \(\frac{P(A)}{P(B)}\). These two expressions are fundamentally non-equivalent.

---

## 2. Multi-Step Derivation: Bayes' Theorem

Starting from the definition of conditional probability:

\[
\begin{aligned}
P(A \mid B) &= \frac{P(A \cap B)}{P(B)} \\
P(A \cap B) &= P(A \mid B) \cdot P(B) = P(B \mid A) \cdot P(A) \\
P(A \mid B) &= \frac{P(B \mid A) \cdot P(A)}{P(B)}, \qquad P(B) > 0
\end{aligned}
\]

---

## 3. Core Academic Notation Demonstrations

### A. Fractions
The probability ratio between two arbitrary measures is typeset with a clean horizontal bar:

\[
\frac{a}{b}
\]

### B. Summations & Partitions
By the Law of Total Probability, if \(\{B_1, B_2, \dots, B_n\}\) forms a partition of \(\Omega\):

\[
P(A) = \sum_{i=1}^{n} P(A \cap B_i) = \sum_{i=1}^{n} P(A \mid B_i) \cdot P(B_i)
\]

### C. Transition Matrices
In a discrete Markov chain, state transition probabilities form an aligned stochastic matrix:

\[
P = \begin{bmatrix} p_{11} & p_{12} \\ p_{21} & p_{22} \end{bmatrix}
\]

### D. Subscripts & Superscripts
Variance and squared expectations for independent variables:

\[
\sigma_1^2 + \sigma_2^2 = \sigma_{\text{total}}^2
\]
"""
    return template.replace("__BRANDING__", branding)


def explain_math_topic(topic: str, branding: str = "Prepared by @issparsh @sumitsingh097") -> str:
    """Generates an academically typeset markdown explanation for a given mathematical topic."""
    t_lower = topic.lower()
    if "conditional" in t_lower or "probab" in t_lower:
        return explain_conditional_probability(branding=branding)

    safe_title = topic.strip().title()
    template = r"""# __TITLE__: Mathematical Engineering Reference

**Topic:** __TITLE__
**Edition:** Academic Reference Edition
**Prepared by:** __BRANDING__

---

## 1. Executive Definition & Mathematical Formulation

Academically rigorous formulation of __TITLE__ following formal university standards.

All variables and expressions strictly adhere to professional LaTeX notation:

\[
\sum_{i=1}^{n} x_i = S, \qquad x_i \in \mathbb{R}
\]

Where each component \(x_i\) represents an individual scalar measure.
"""
    return template.replace("__TITLE__", safe_title).replace("__BRANDING__", branding)
