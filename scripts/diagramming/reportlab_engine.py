"""Professional Publication-Grade PDF Compilation Engine for thenuke.

Implements the exact layout, typography, alignment, and aesthetic of
JavaScript_Complete_Reference_Manual.pdf using ReportLab:
- ISO A4 (595.28 x 841.89 pt) with 60.14 pt margins (475 pt printable width)
- Running header with top hairline rule (#CCCCCC, 0.5pt) at y=800 pt
- Running footer with page count ("Page X of N"), edition label, and official
  Twitter/X vector glyph alongside "Prepared by @issparsh @sumitsingh097" at y=32 pt
- Phase Title in Helvetica-Bold 18pt with 1.5pt solid black dividing rule
- Chapter Title in Helvetica-Bold 13.5pt
- Section Subheadings in Helvetica-Bold 11pt
- Body prose in Helvetica 10pt with 14pt leading
- Code blocks in bordered (#777777, 0.75pt) light-grey (#EFEFEF) boxes in Courier 8.5pt / 11.5pt leading
- Callout boxes in bordered (#444444, 1.0pt) soft-grey (#F8F8F8) tables for
  [MENTAL MODEL], [ENGINEERING GOTCHA], [INTERVIEW TIP], [INVARIANT], [RULE]
- Structured multi-page Syllabus & Table of Contents (Part I to VI)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from scripts.diagramming.vector_diagrams import get_diagram
from scripts.quotes.quote_library import get_quote

logger = logging.getLogger(__name__)

# Dimensions
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.276, 841.890
MARGIN_LEFT = 60.14
MARGIN_RIGHT = 60.14
MARGIN_TOP = 54.0
MARGIN_BOTTOM = 54.0
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 475.0 pt

# Colors matching JavaScript_Complete_Reference_Manual.pdf exactly
COLOR_BLACK = colors.HexColor("#000000")
COLOR_CHARCOAL = colors.HexColor("#222222")
COLOR_MUTED = colors.HexColor("#666666")
COLOR_HAIRLINE = colors.HexColor("#CCCCCC")
COLOR_BORDER_CODE = colors.HexColor("#777777")
COLOR_BG_CODE = colors.HexColor("#EFEFEF")
COLOR_BORDER_CALLOUT = colors.HexColor("#444444")
COLOR_BG_CALLOUT = colors.HexColor("#F8F8F8")
COLOR_WHITE = colors.HexColor("#FFFFFF")


def md_to_reportlab_html(text: str) -> str:
    """Safely converts markdown bold, italic, code, and escapes XML entities for ReportLab Paragraphs."""
    # 1. Escape bare & that are not already valid HTML entities
    text = re.sub(r"&(?!(?:amp|lt|gt|quot|#\d+|#x[0-9a-fA-F]+);)", "&amp;", text)

    # 2. Extract inline code `foo` into placeholders to prevent cross-interaction with **
    codes: List[str] = []
    def code_store(m: re.Match) -> str:
        raw = m.group(1)
        safe = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        idx = len(codes)
        codes.append(f'<font face="Courier" size="8.5">{safe}</font>')
        return f"___CODE_PH_{idx}___"

    text = re.sub(r"`([^`]+)`", code_store, text)

    # 3. Convert **bold** to <b>bold</b>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    # 4. Convert *italic* to <i>italic</i>
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)

    # 5. Escape any remaining < or > that aren't allowed ReportLab tags
    def tag_cleaner(m: re.Match) -> str:
        tag = m.group(0)
        if re.match(r"^</?(?:b|i|font(?:\s+[^>]+)?|br/?)>$", tag):
            return tag
        return tag.replace("<", "&lt;").replace(">", "&gt;")

    text = re.sub(r"<[^>]*>", tag_cleaner, text)
    # Also escape standalone <
    text = re.sub(r"<(?!(?:/?(?:b|i|font|br)))", "&lt;", text)

    # 6. Restore code placeholders
    for idx, c_html in enumerate(codes):
        text = text.replace(f"___CODE_PH_{idx}___", c_html)

    return text


class PublicationCanvas(canvas.Canvas):
    """Two-pass canvas that renders running headers, footers, total page counts, and the X glyph."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self.doc_title = "Git: The Complete Reference Manual"
        self.edition_label = "Monochrome Reference Edition"
        self.author_branding = "Prepared by @issparsh @sumitsingh097"

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_x_logo(self, x: float, y: float, size: float = 7.5):
        """Draw official vector Twitter/X glyph matching brand geometry."""
        self.saveState()
        self.setFillColor(COLOR_BLACK)
        self.setStrokeColor(COLOR_BLACK)
        # Bounding box is (x, y) to (x + size, y + size)
        # Main thick diagonal: from top-left to bottom-right
        self.setLineWidth(size * 0.18)
        self.line(x, y + size, x + size, y)
        # Secondary thin diagonal: from top-right to bottom-left
        self.setLineWidth(size * 0.11)
        self.line(x + size, y + size, x, y)
        self.restoreState()

    def _draw_page_decorations(self, total_pages: int):
        pno = self._pageNumber
        if pno == 1:
            # Cover page has its own self-contained layout
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_MUTED)

        # 1. Top running header text
        header_text = f"{self.doc_title} — Architecture & Core Internals"
        self.drawString(54.0, PAGE_HEIGHT - 34.0, header_text)

        # 2. Top hairline dividing rule
        self.setStrokeColor(COLOR_HAIRLINE)
        self.setLineWidth(0.5)
        self.line(54.0, PAGE_HEIGHT - 42.0, PAGE_WIDTH - 54.0, PAGE_HEIGHT - 42.0)

        # 3. Bottom hairline dividing rule
        self.line(54.0, 46.0, PAGE_WIDTH - 54.0, 46.0)

        # 4. Bottom footer: Left page count and edition label
        footer_left = f"Page {pno} of {total_pages}  •  {self.edition_label}"
        self.drawString(54.0, 32.0, footer_left)

        # 5. Bottom footer: Right author branding with official vector X logo (pinned to right margin, zero collision)
        branding_text = self.author_branding
        bw = self.stringWidth(branding_text, "Helvetica", 8)
        logo_size = 7.0
        logo_pad = 4.0
        total_brand_w = bw + logo_pad + logo_size
        start_x = (PAGE_WIDTH - 54.0) - total_brand_w

        self.drawString(start_x, 32.0, branding_text)
        self._draw_x_logo(start_x + bw + logo_pad, 32.0, size=logo_size)

        self.restoreState()


class ReferenceManualBuilder:
    """Builds an archival reference manual conforming to the style specification."""

    def __init__(self, output_path: Union[str, Path], topic: str = "Git"):
        self.output_path = Path(output_path)
        self.topic = topic
        self.styles = self._init_styles()

    def _init_styles(self) -> Dict[str, ParagraphStyle]:
        styles: Dict[str, ParagraphStyle] = {}

        # Cover Styles
        styles["CoverTitle"] = ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=28.0,
            leading=34.0,
            alignment=TA_CENTER,
            textColor=COLOR_BLACK,
            spaceAfter=8,
        )
        styles["CoverSubtitle"] = ParagraphStyle(
            "CoverSubtitle",
            fontName="Helvetica-Bold",
            fontSize=13.0,
            leading=17.0,
            alignment=TA_CENTER,
            textColor=COLOR_CHARCOAL,
            spaceAfter=14,
        )
        styles["CoverDesc"] = ParagraphStyle(
            "CoverDesc",
            fontName="Helvetica",
            fontSize=10.0,
            leading=15.0,
            alignment=TA_CENTER,
            textColor=COLOR_CHARCOAL,
            spaceAfter=20,
        )
        styles["CoverMetaLabel"] = ParagraphStyle(
            "CoverMetaLabel",
            fontName="Helvetica-Bold",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_BLACK,
        )
        styles["CoverMetaVal"] = ParagraphStyle(
            "CoverMetaVal",
            fontName="Helvetica",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_CHARCOAL,
        )
        styles["CoverQuote"] = ParagraphStyle(
            "CoverQuote",
            fontName="Helvetica-BoldOblique",
            fontSize=11.0,
            leading=15.0,
            alignment=TA_CENTER,
            textColor=COLOR_BLACK,
        )

        # TOC Styles
        styles["TOCHeader"] = ParagraphStyle(
            "TOCHeader",
            fontName="Helvetica-Bold",
            fontSize=12.0,
            leading=16.0,
            textColor=COLOR_BLACK,
            spaceAfter=4,
        )
        styles["TOCSub"] = ParagraphStyle(
            "TOCSub",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.0,
            textColor=COLOR_MUTED,
            spaceAfter=8,
        )
        styles["TOCPhase"] = ParagraphStyle(
            "TOCPhase",
            fontName="Helvetica-Bold",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_BLACK,
            spaceBefore=6,
            spaceAfter=2,
        )
        styles["TOCChapter"] = ParagraphStyle(
            "TOCChapter",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.0,
            textColor=COLOR_CHARCOAL,
            leftIndent=10,
            spaceAfter=2,
        )
        styles["TOCSummary"] = ParagraphStyle(
            "TOCSummary",
            fontName="Helvetica-Oblique",
            fontSize=8.0,
            leading=11.0,
            textColor=COLOR_MUTED,
            leftIndent=10,
            spaceAfter=6,
        )

        # Content Styles
        styles["PhaseHeader"] = ParagraphStyle(
            "PhaseHeader",
            fontName="Helvetica-Bold",
            fontSize=18.0,
            leading=22.0,
            textColor=COLOR_BLACK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )
        styles["TopicsLabel"] = ParagraphStyle(
            "TopicsLabel",
            fontName="Helvetica",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_BLACK,
            spaceAfter=10,
            keepWithNext=True,
        )
        styles["ChapterHeader"] = ParagraphStyle(
            "ChapterHeader",
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17.5,
            textColor=COLOR_BLACK,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        )
        styles["SectionHeader"] = ParagraphStyle(
            "SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=11.0,
            leading=15.0,
            textColor=COLOR_BLACK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )
        styles["Body"] = ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_CHARCOAL,
            spaceAfter=6,
        )
        styles["Bullet"] = ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_CHARCOAL,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=3,
        )

        # Code Styles
        styles["CodeTitle"] = ParagraphStyle(
            "CodeTitle",
            fontName="Helvetica-Bold",
            fontSize=11.0,
            leading=14.0,
            textColor=COLOR_BLACK,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        )
        styles["CodeText"] = ParagraphStyle(
            "CodeText",
            fontName="Courier",
            fontSize=7.8,
            leading=10.5,
            textColor=COLOR_BLACK,
        )

        # Callout Styles
        styles["CalloutHead"] = ParagraphStyle(
            "CalloutHead",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13.0,
            textColor=COLOR_BLACK,
            spaceAfter=3,
        )
        styles["CalloutBody"] = ParagraphStyle(
            "CalloutBody",
            fontName="Helvetica-Oblique",
            fontSize=9.0,
            leading=12.5,
            textColor=COLOR_CHARCOAL,
        )

        # Challenge Styles
        styles["ChallengeTitle"] = ParagraphStyle(
            "ChallengeTitle",
            fontName="Helvetica-Bold",
            fontSize=11.0,
            leading=15.0,
            textColor=COLOR_BLACK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )
        styles["ChallengeReq"] = ParagraphStyle(
            "ChallengeReq",
            fontName="Helvetica-Bold",
            fontSize=10.0,
            leading=14.0,
            textColor=COLOR_CHARCOAL,
            spaceAfter=4,
            keepWithNext=True,
        )

        return styles

    def build_cover_page(
        self,
        topic_name: str,
        num_phases: int = 9,
        num_drills: int = 27,
        capstone_title: str = "",
        custom_quote: Optional[Tuple[str, str]] = None,
    ) -> List[Any]:
        """Constructs cover page flowables matching reference manual."""
        story = []
        story.append(Spacer(1, 40))

        # Title & Subtitle
        story.append(Paragraph(topic_name.upper(), self.styles["CoverTitle"]))
        story.append(Paragraph("The Complete Engineering Reference", self.styles["CoverSubtitle"]))

        # Description
        desc_text = (
            f"A rigorous, comprehensive, ground-up reference manual designed for software engineers and learners who want to "
            f"master {topic_name} from core architectural foundations to advanced enterprise methodologies, "
            f"invariants, and verified hands-on drills."
        )
        story.append(Paragraph(desc_text, self.styles["CoverDesc"]))
        story.append(Spacer(1, 15))

        # Dynamic Metadata Table
        arch_label = f"{num_phases} Phases + {num_drills} Production Drills + Comprehensive Deep Dives"
        capstone_label = capstone_title or f"Zero-Dependency {topic_name} Production Engine Architecture"
        meta_data = [
            [
                Paragraph("Curriculum Edition:", self.styles["CoverMetaLabel"]),
                Paragraph("2026 Definitive Edition (Production Ready)", self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Language & Tone:", self.styles["CoverMetaLabel"]),
                Paragraph("Hinglish Technical Prose (Direct, Casual, Zero Fluff)", self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Questions & Drills:", self.styles["CoverMetaLabel"]),
                Paragraph("100% Formal English Specifications with Verified Solutions", self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Architecture:", self.styles["CoverMetaLabel"]),
                Paragraph(arch_label, self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Capstone Project:", self.styles["CoverMetaLabel"]),
                Paragraph(capstone_label, self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Author Branding:", self.styles["CoverMetaLabel"]),
                Paragraph("Prepared by @issparsh @sumitsingh097", self.styles["CoverMetaVal"]),
            ],
            [
                Paragraph("Visual Design:", self.styles["CoverMetaLabel"]),
                Paragraph("Minimalist High-Contrast Monochrome for Focused Reading", self.styles["CoverMetaVal"]),
            ],
        ]
        t = Table(meta_data, colWidths=[140.0, 335.0])
        t.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(t)
        story.append(Spacer(1, 35))

        # Dynamic Quote Box from 100-Quotes Library
        if custom_quote:
            q_text, q_author = custom_quote
        else:
            q_text, q_author = get_quote(topic=topic_name)

        quote_html = f'"{q_text}" — <b>{q_author}</b>'
        quote_p = Paragraph(quote_html, self.styles["CoverQuote"])
        qt = Table([[quote_p]], colWidths=[CONTENT_WIDTH])
        qt.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_CALLOUT),
                ("BOX", (0, 0), (-1, -1), 1.0, COLOR_BORDER_CALLOUT),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ])
        )
        story.append(qt)

        story.append(PageBreak())
        return story

    def wrap_code_text(self, code_text: str, max_chars: int = 70) -> str:
        """Wraps long lines in code snippets so they never overflow table or right margin."""
        import textwrap
        out_lines = []
        for line in code_text.splitlines():
            if len(line) <= max_chars:
                out_lines.append(line)
            else:
                stripped = line.lstrip()
                indent = line[: len(line) - len(stripped)]
                if stripped.startswith(("#", "//", "/*", "*", ";")):
                    wrapped = textwrap.wrap(line, width=max_chars, subsequent_indent=indent + "# ")
                    out_lines.extend(wrapped)
                else:
                    wrapped = textwrap.wrap(line, width=max_chars, subsequent_indent=indent + "    ", break_long_words=True)
                    out_lines.extend(wrapped)
        return "\n".join(out_lines)

    def split_code_block(self, title: str, code_text: str, max_lines: int = 36) -> List[Tuple[str, str]]:
        """Splits long code blocks into parts so they never exceed single-page limits."""
        wrapped_text = self.wrap_code_text(code_text, max_chars=70)
        lines = wrapped_text.strip().splitlines()
        if len(lines) <= max_lines:
            return [(title, "\n".join(lines))]

        chunks = []
        total_parts = (len(lines) + max_lines - 1) // max_lines
        for p_idx in range(total_parts):
            chunk_lines = lines[p_idx * max_lines : (p_idx + 1) * max_lines]
            base_t = title if title else "Code Block"
            p_title = f"{base_t} (Part {p_idx + 1} of {total_parts})"
            chunks.append((p_title, "\n".join(chunk_lines)))
        return chunks

    def make_code_box(self, title: str, code_text: str) -> List[Any]:
        """Create styled code block table flowables with title and border, split if long."""
        chunks = self.split_code_block(title, code_text, max_lines=36)
        flowables = []
        for part_title, part_code in chunks:
            box_story = []
            if part_title:
                box_story.append(Paragraph(f"<b>Code: {part_title}</b>", self.styles["CodeTitle"]))
                box_story.append(Spacer(1, 2))

            pre = Preformatted(part_code.strip(), self.styles["CodeText"])
            t = Table([[pre]], colWidths=[CONTENT_WIDTH])
            t.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_CODE),
                    ("BOX", (0, 0), (-1, -1), 0.75, COLOR_BORDER_CODE),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            box_story.append(t)
            box_story.append(Spacer(1, 6))
            flowables.append(KeepTogether(box_story))
        return flowables

    def make_callout_box(self, header: str, body_text: str) -> KeepTogether:
        """Create a styled callout box flowable with border and soft background."""
        head_p = Paragraph(f"<b>{header}</b>", self.styles["CalloutHead"])
        body_p = Paragraph(md_to_reportlab_html(body_text.strip()), self.styles["CalloutBody"])
        t = Table([[head_p], [body_p]], colWidths=[CONTENT_WIDTH])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_CALLOUT),
                ("BOX", (0, 0), (-1, -1), 1.0, COLOR_BORDER_CALLOUT),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        return KeepTogether([t, Spacer(1, 8)])

    def parse_markdown_to_flowables(self, md_text: str) -> List[Any]:
        """Parse structured markdown manual into publication flowables."""
        story: List[Any] = []
        lines = md_text.splitlines()
        i = 0
        n = len(lines)

        in_syllabus = False
        topic_name = self.topic

        def safe_page_break():
            if story and not isinstance(story[-1], PageBreak):
                story.append(PageBreak())

        while i < n:
            line = lines[i].rstrip()
            if not line or line.startswith("=" * 10) or line.startswith("-" * 10):
                i += 1
                continue

            # Cover Title detection
            if line.startswith("# ") and not story:
                title_line = line.lstrip("# ").strip()
                if ":" in title_line:
                    topic_name = title_line.split(":")[0].strip()
                detected_phases = len(set(re.findall(r"^PHASE\s+(\d+)", md_text, re.MULTILINE))) or 9
                detected_drills = len(re.findall(r"CHALLENGE\s+\d+", md_text, re.IGNORECASE)) or 27
                story.extend(self.build_cover_page(topic_name, num_phases=detected_phases, num_drills=detected_drills))
                i += 1
                # Skip cover subtitle, branding, and dividers so they don't leak onto Page 2
                while i < n and "DETAILED SYLLABUS" not in lines[i]:
                    i += 1
                continue

            # Syllabus Index detection
            if "DETAILED SYLLABUS & TABLE OF CONTENTS" in line:
                if in_syllabus:
                    # Next Part of syllabus (e.g., PART II to VI) gets fresh page
                    safe_page_break()
                in_syllabus = True
                story.append(Paragraph(line.strip("=").strip(), self.styles["TOCHeader"]))
                story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_BLACK, spaceBefore=4, spaceAfter=6))
                i += 1
                continue

            # End of Syllabus Index
            if line.strip() == "<!-- END SYLLABUS -->":
                in_syllabus = False
                safe_page_break()
                i += 1
                continue

            if in_syllabus:
                if line.startswith("PHASE "):
                    story.append(Paragraph(line.strip(), self.styles["TOCPhase"]))
                elif line.startswith("Topics:"):
                    story.append(Paragraph(line.strip(), self.styles["TOCSub"]))
                elif line.startswith("Chapter "):
                    story.append(Paragraph(line.strip(), self.styles["TOCChapter"]))
                elif line.startswith("Hands-On Challenges:"):
                    story.append(Paragraph(line.strip(), self.styles["TOCSummary"]))
                elif line.startswith("Deep Dive "):
                    story.append(Paragraph(line.strip(), self.styles["TOCChapter"]))
                elif line.startswith("APPENDICES"):
                    story.append(Paragraph(line.strip(), self.styles["TOCPhase"]))
                else:
                    story.append(Paragraph(line.strip(), self.styles["TOCSub"]))
                i += 1
                continue

            # -------------------------------------------------------------
            # Content Parsing (Post-Syllabus)
            # -------------------------------------------------------------

            # 1. Phase Header (starts on fresh page)
            if re.match(r"^(?:#\s*)?PHASE\s+\d+\s*—\s*PRACTICE DRILLS", line, re.IGNORECASE):
                story.append(Spacer(1, 14))
                story.append(Paragraph(line.lstrip("# ").strip(), self.styles["PhaseHeader"]))
                story.append(HRFlowable(width="100%", thickness=1.0, color=COLOR_BLACK, spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            if re.match(r"^(?:#\s*)?PHASE\s+\d+\s*—", line, re.IGNORECASE):
                safe_page_break()
                story.append(Paragraph(line.lstrip("# ").strip(), self.styles["PhaseHeader"]))
                story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_BLACK, spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            # 2. Appendices Header (starts on fresh page)
            if "APPENDICES — ARCHITECTURAL DEEP DIVES" in line:
                safe_page_break()
                story.append(Paragraph(line.lstrip("# ").strip(), self.styles["PhaseHeader"]))
                story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_BLACK, spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            # 3. Topics Bar
            if line.startswith("Topics:") or line.startswith("**Topics:**"):
                topic_text = line.replace("**Topics:**", "").replace("Topics:", "").strip()
                story.append(Paragraph(f"<b>Topics:</b> {topic_text}", self.styles["TopicsLabel"]))
                i += 1
                continue

            # 4. Scope Bar (in Appendices)
            if line.startswith("Scope:"):
                scope_text = line.replace("Scope:", "").strip()
                story.append(Paragraph(f"<b>Scope:</b> {scope_text}", self.styles["TopicsLabel"]))
                i += 1
                continue

            # 5. Chapter Header
            if re.match(r"^(?:#{2,3}\s*)?Chapter\s+\d+\.\d+", line, re.IGNORECASE) or line.startswith("## Appendix"):
                ch_title = line.lstrip("# ").strip()
                story.append(Paragraph(ch_title, self.styles["ChapterHeader"]))
                i += 1
                continue

            # 6. Challenge Header
            if re.match(r"^(?:#{2,3}\s*)?CHALLENGE\s+\d+", line, re.IGNORECASE):
                ch_title = line.lstrip("# ").strip()
                story.append(Paragraph(ch_title, self.styles["ChallengeTitle"]))
                i += 1
                continue

            if "Problem Statement & Requirements:" in line:
                story.append(Paragraph("<b>Problem Statement & Requirements:</b>", self.styles["ChallengeReq"]))
                i += 1
                continue

            # 7. Section Header
            if line.startswith("### ") or line.startswith("## "):
                sec_title = line.lstrip("# ").strip()
                story.append(Paragraph(sec_title, self.styles["SectionHeader"]))
                i += 1
                continue

            # 7b. Technical Vector Diagram Directive: [DIAGRAM: name]
            diag_match = re.match(r"^\[DIAGRAM:\s*([a-zA-Z0-9_\-]+)\]", line.strip())
            if diag_match:
                diag_name = diag_match.group(1).lower()
                diag_flowable = get_diagram(diag_name)
                if diag_flowable:
                    story.append(Spacer(1, 4))
                    story.append(KeepTogether([diag_flowable]))
                    story.append(Spacer(1, 8))
                i += 1
                continue

            # 8. Callout Box: [MENTAL MODEL], [ENGINEERING GOTCHA], [INTERVIEW TIP], [INVARIANT], [RULE]
            if line.strip().startswith(("[MENTAL MODEL]", "[ENGINEERING GOTCHA]", "[INTERVIEW TIP]", "[INVARIANT]", "[RULE]", "[THE EVENT LOOP TICK INVARIANT]")):
                callout_head = line.strip()
                callout_lines = []
                i += 1
                while i < n and lines[i].strip() and not lines[i].startswith(("#", "[", "```", "CHALLENGE", "PHASE")):
                    callout_lines.append(lines[i].strip())
                    i += 1
                callout_body = " ".join(callout_lines)
                story.append(self.make_callout_box(callout_head, callout_body))
                continue

            # 9. Code Block
            code_title = ""
            if line.startswith("Code:"):
                code_title = line.replace("Code:", "").strip()
                i += 1
                if i < n and lines[i].strip().startswith("```"):
                    line = lines[i].rstrip()

            if line.startswith("```"):
                code_lines = []
                i += 1
                while i < n and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # consume closing ```
                code_text = "\n".join(code_lines)
                story.extend(self.make_code_box(code_title, code_text))
                continue

            # 10. Bullet Points
            if line.strip().startswith(("• ", "- ", "* ")):
                bullet_text = line.strip()[2:].strip()
                story.append(Paragraph(f"• {md_to_reportlab_html(bullet_text)}", self.styles["Bullet"]))
                i += 1
                continue

            # 11. Regular Body Paragraph
            story.append(Paragraph(md_to_reportlab_html(line.strip()), self.styles["Body"]))
            i += 1

        return story

    def compile(self, markdown_text: str) -> Path:
        """Compiles the given Markdown manual into an aligned, publication-grade PDF."""
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
        )

        flowables = self.parse_markdown_to_flowables(markdown_text)

        canvas_maker = PublicationCanvas
        canvas_maker.doc_title = f"{self.topic}: The Complete Reference Manual"

        doc.build(flowables, canvasmaker=canvas_maker)
        logger.info(f"Published PDF compiled via ReportLab: {self.output_path}")
        return self.output_path
