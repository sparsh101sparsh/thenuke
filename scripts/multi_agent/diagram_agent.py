"""Diagram Agent for thenuke multi-agent authoring system.

Responsible for:
1. Managing the registry of publication-grade vector diagrams.
2. Generating and validating ReportLab Drawing flowables.
3. Auditing the document corpus to ensure every required architectural
   milestone has an embedded vector diagram directive.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple
from reportlab.graphics.shapes import Drawing

from scripts.diagramming.vector_diagrams import DIAGRAM_REGISTRY, get_diagram


class DiagramAgent:
    """Specialized Agent responsible for vector diagram generation, sizing, and validation."""

    def __init__(self):
        self.available_diagrams: Set[str] = set(DIAGRAM_REGISTRY.keys())

    def validate_diagram(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validates that a diagram exists and compiles into a valid ReportLab Drawing."""
        clean_name = name.strip().lower()
        if clean_name not in self.available_diagrams:
            return False, f"Diagram '{clean_name}' not registered in DIAGRAM_REGISTRY."

        try:
            d = get_diagram(clean_name)
            if not isinstance(d, Drawing):
                return False, f"Diagram '{clean_name}' did not return a Drawing instance."
            if d.width != 475.0:
                return False, f"Diagram '{clean_name}' width is {d.width}, expected 475.0 pt."
            return True, None
        except Exception as e:
            return False, f"Diagram '{clean_name}' failed to render: {str(e)}"

    def audit_markdown_diagrams(self, md_text: str, required_slots: List[str]) -> Tuple[bool, List[str]]:
        """Audits a markdown string to ensure all required vector diagrams are embedded."""
        found_tags = set(re.findall(r"\[DIAGRAM:\s*([a-zA-Z0-9_\-]+)\]", md_text, re.IGNORECASE))
        clean_found = {t.lower() for t in found_tags}

        missing = []
        for req in required_slots:
            if req.lower() not in clean_found:
                missing.append(req)

        # Also verify that every found diagram is valid
        invalid = []
        for found in clean_found:
            valid, err = self.validate_diagram(found)
            if not valid:
                invalid.append(f"{found}: {err}")

        issues = []
        if missing:
            issues.append(f"Missing required vector diagram directives: {missing}")
        if invalid:
            issues.append(f"Invalid diagram directives found: {invalid}")

        return len(issues) == 0, issues
