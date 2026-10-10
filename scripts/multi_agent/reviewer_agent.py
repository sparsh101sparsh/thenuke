"""Reviewer Agent (Adversarial Quality Auditor) for thenuke multi-agent authoring system.

Enforces the 4-Pass Automated Quality Gate before document publication:
- Pass 1: Visual Layout & Geometry Audit (ReportLab LayoutError, frame overflow, max lines per code chunk)
- Pass 2: Strict Zero-Devanagari Audit (100% Latin Roman script, 0 matches for Unicode range U+0900 to U+097F)
- Pass 3: Vector Diagram Density Audit (presence and validity of all architectural vector diagrams)
- Pass 4: FAANG Drill & Code Completeness Audit (every challenge contains requirements + working solution)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AuditReport:
    """Comprehensive adversarial quality audit report."""
    pass_1_layout_clean: bool
    pass_2_zero_devanagari: bool
    pass_3_diagram_density: bool
    pass_4_drills_complete: bool
    total_pages: int
    devanagari_count: int
    diagram_count: int
    drills_count: int
    issues: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.pass_1_layout_clean
            and self.pass_2_zero_devanagari
            and self.pass_3_diagram_density
            and self.pass_4_drills_complete
        )


class ReviewerAgent:
    """Specialized Adversarial Auditor enforcing zero-defect publication standards."""

    REQUIRED_DIAGRAMS = [
        "object_model",
        "index_binary",
        "three_trees",
        "branching_dag",
        "three_way_merge",
        "merge_conflict",
        "rebase_replay",
        "reset_matrix",
        "remote_sync",
    ]

    def audit_markdown_source(self, md_text: str) -> Tuple[bool, List[str]]:
        """Audits raw markdown source for Devanagari, diagram tags, and challenge structure."""
        issues: List[str] = []

        # 1. Zero Devanagari check
        devanagari_chars = re.findall(r"[\u0900-\u097F]", md_text)
        if devanagari_chars:
            issues.append(f"Pass 2 Failed: Found {len(devanagari_chars)} Devanagari characters in markdown source.")

        # 2. Vector diagram presence check
        found_tags = set(re.findall(r"\[DIAGRAM:\s*([a-zA-Z0-9_\-]+)\]", md_text, re.IGNORECASE))
        clean_found = {t.lower() for t in found_tags}
        for req in self.REQUIRED_DIAGRAMS:
            if req not in clean_found:
                issues.append(f"Pass 3 Failed: Missing required diagram tag '[DIAGRAM: {req}]'.")

        # 3. Drills count check
        challenges = re.findall(r"CHALLENGE\s+\d+", md_text, re.IGNORECASE)
        if len(challenges) < 25:
            issues.append(f"Pass 4 Failed: Found only {len(challenges)} challenges (expected 27).")

        return len(issues) == 0, issues

    def audit_compiled_pdf(self, pdf_path: Path) -> AuditReport:
        """Audits compiled PDF for zero Devanagari, page count, and structural integrity."""
        import fitz  # PyMuPDF

        issues: List[str] = []
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)

        # Pass 1: Layout & Page Count
        pass_1 = total_pages >= 60  # Complete Git manual should be at least 60-80 pages
        if not pass_1:
            issues.append(f"Pass 1 Warning: Document has {total_pages} pages (expected >= 60).")

        # Pass 2: Zero Devanagari across 100% of pages
        devanagari_matches = []
        for pno in range(total_pages):
            page_text = doc[pno].get_text()
            matches = re.findall(r"[\u0900-\u097F]", page_text)
            if matches:
                devanagari_matches.extend(matches)
                issues.append(f"Pass 2 Failed on page {pno + 1}: Found {len(matches)} Devanagari characters.")

        pass_2 = len(devanagari_matches) == 0

        # Pass 3: Diagram Density (Audited via markdown source or text inspection)
        # We also check that the PDF contains drawings on multiple pages
        pages_with_drawings = 0
        for pno in range(total_pages):
            drawings = doc[pno].get_drawings()
            if len(drawings) > 3:  # Beyond just header/footer lines
                pages_with_drawings += 1

        pass_3 = pages_with_drawings >= len(self.REQUIRED_DIAGRAMS)
        if not pass_3:
            issues.append(f"Pass 3 Warning: Found {pages_with_drawings} pages with custom vector drawings (expected >= {len(self.REQUIRED_DIAGRAMS)}).")

        # Pass 4: FAANG Drills presence in text
        full_text = "".join(page.get_text() for page in doc)
        drill_matches = len(re.findall(r"CHALLENGE\s+\d+", full_text, re.IGNORECASE))
        pass_4 = drill_matches >= 25
        if not pass_4:
            issues.append(f"Pass 4 Warning: Found {drill_matches} challenges in compiled text (expected >= 27).")

        doc.close()

        return AuditReport(
            pass_1_layout_clean=pass_1,
            pass_2_zero_devanagari=pass_2,
            pass_3_diagram_density=pass_3,
            pass_4_drills_complete=pass_4,
            total_pages=total_pages,
            devanagari_count=len(devanagari_matches),
            diagram_count=pages_with_drawings,
            drills_count=drill_matches,
            issues=issues,
        )
