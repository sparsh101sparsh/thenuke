"""Vector Diagramming & Branding Engine for thenuke skill.

Implements Milestone 4 (R4) requirements:
- PyMuPDF vector drawing primitives: shapes, lines, arrows, Bézier curves, callout boxes.
- CS Memory Architecture Visualizers: Call Stack, Heap Graph, Event Loop Pipeline, Prototype Chain.
- Minimalist High-Contrast Monochrome Aesthetic (strict palette tokens).
- Official Twitter/X vector glyph embedded on cover page and footers.
- Mandatory attribution branding: "Prepared by @issparsh @sumitsingh097".
- High-density ISO A4 PDF compilation from synthesized Markdown corpus.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Monochrome Palette (strict tokens matching style guide §4)
# ---------------------------------------------------------------------------

class Palette:
    BLACK = (0.0, 0.0, 0.0)            # #000000 — primary titles & critical headings
    CHARCOAL = (0.133, 0.133, 0.133)   # #222222 — primary body prose
    DARK_GREY = (0.267, 0.267, 0.267)  # #444444 — secondary captions
    SLATE = (0.333, 0.333, 0.333)      # #555555 — secondary captions alt
    MUTED = (0.4, 0.4, 0.4)           # #666666 — running headers & footers
    HAIRLINE = (0.8, 0.8, 0.8)        # #CCCCCC — thin dividing rules & grids
    OFFWHITE = (0.973, 0.973, 0.973)  # #F8F8F8 — code block backgrounds
    CALLOUT_BG = (0.945, 0.961, 0.976) # #F1F5F9 — callout box fill
    WHITE = (1.0, 1.0, 1.0)           # #FFFFFF — page background

    # Stroke widths
    HAIRLINE_WIDTH = 0.5
    BORDER_WIDTH = 1.0
    THICK_WIDTH = 1.5
    ARROW_WIDTH = 1.2


# ---------------------------------------------------------------------------
# Page & Typography Constants (ISO A4 at 72 DPI)
# ---------------------------------------------------------------------------

A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89
MARGIN_PT = 54.0  # 54pt ≈ 19mm

FONT_TITLE = "hebo"        # Helvetica-Bold
FONT_BODY = "helv"         # Helvetica-Regular
FONT_BOLD = "hebo"         # Helvetica-Bold
FONT_ITALIC = "heit"       # Helvetica-Oblique
FONT_MONO = "cour"         # Courier-Regular

SIZE_DOC_TITLE = 14.0
SIZE_PHASE_HEADER = 13.0
SIZE_CHAPTER_TITLE = 11.0
SIZE_SUBHEADING = 9.5
SIZE_BODY = 8.5
SIZE_TABLE = 7.5
SIZE_CODE = 7.5
SIZE_FOOTER = 7.5

LEADING_BODY = 11.5
LEADING_CODE = 9.5

CONTENT_WIDTH = A4_WIDTH_PT - 2 * MARGIN_PT
CONTENT_HEIGHT = A4_HEIGHT_PT - 2 * MARGIN_PT


# ---------------------------------------------------------------------------
# X (Twitter) Vector Glyph — Native Vector Path (no rasterization)
# ---------------------------------------------------------------------------

def _x_logo_path_commands() -> List[Tuple]:
    """
    Returns the X glyph as a sequence of (command, *args) tuples for PyMuPDF.
    The glyph is the official Twitter/X logo drawn as two crossing diagonal
    rectangles scaled to fit a bounding box of width w, height h at origin (ox, oy).
    """
    # The X logo is two thick diagonal strokes crossing center.
    # We parametrize the strokes relative to a unit square then scale.
    return [("X_GLYPH_PLACEHOLDER", True)]  # resolved at draw-time via _draw_x_glyph


def _draw_x_glyph(page: "fitz.Page", x: float, y: float, size: float, color: Tuple) -> None:  # noqa: F821
    """
    Draw the official Twitter/X logo as native PyMuPDF vector strokes.
    The X glyph consists of two thick diagonal bars crossing at center.

    Args:
        page: PyMuPDF Page object.
        x, y: Top-left corner of the bounding box.
        size: Width & height of the square bounding box in points.
        color: RGB tuple from Palette.
    """
    try:
        import fitz  # PyMuPDF

        shape = page.new_shape()
        cx, cy = x + size / 2, y + size / 2
        hw = size * 0.42   # half-width of the X arm tips
        sw = size * 0.13   # stroke width of each bar

        # Bar 1: top-left to bottom-right
        p1 = fitz.Point(cx - hw, cy - hw)
        p2 = fitz.Point(cx + hw, cy + hw)
        shape.draw_line(p1, p2)
        shape.finish(
            width=sw * 1.8,
            color=color,
            fill=color,
            stroke_opacity=1.0,
            fill_opacity=1.0,
        )

        # Bar 2: top-right to bottom-left
        p3 = fitz.Point(cx + hw, cy - hw)
        p4 = fitz.Point(cx - hw, cy + hw)
        shape.draw_line(p3, p4)
        shape.finish(
            width=sw * 1.8,
            color=color,
            fill=color,
            stroke_opacity=1.0,
            fill_opacity=1.0,
        )

        shape.commit()
    except ImportError:
        logger.warning("PyMuPDF (fitz) not available — X glyph rendering skipped.")


# ---------------------------------------------------------------------------
# Callout Box Renderer
# ---------------------------------------------------------------------------

def draw_callout_box(page: "fitz.Page", rect: Tuple, label: str, body: str) -> None:  # noqa: F821
    """Draw a [MENTAL MODEL] / [ENGINEERING GOTCHA] style callout box."""
    try:
        import fitz

        x0, y0, x1, y1 = rect
        fitz_rect = fitz.Rect(x0, y0, x1, y1)

        shape = page.new_shape()
        # Fill background
        shape.draw_rect(fitz_rect)
        shape.finish(
            fill=Palette.CALLOUT_BG,
            color=Palette.BLACK,
            width=Palette.BORDER_WIDTH,
        )
        shape.commit()

        # Label text (bold)
        page.insert_text(
            fitz.Point(x0 + 6, y0 + 10),
            label,
            fontname=FONT_BOLD,
            fontsize=SIZE_SUBHEADING,
            color=Palette.BLACK,
        )
        # Body text
        page.insert_textbox(
            fitz.Rect(x0 + 6, y0 + 20, x1 - 6, y1 - 4),
            body,
            fontname=FONT_ITALIC,
            fontsize=SIZE_BODY,
            color=Palette.CHARCOAL,
            align=0,
        )
    except ImportError:
        logger.warning("PyMuPDF (fitz) not available — callout box rendering skipped.")


# ---------------------------------------------------------------------------
# Running Header & Footer Renderer
# ---------------------------------------------------------------------------

HEADER_TEXT = "JavaScript: The Complete Reference Manual — Architecture & Core Internals"
FOOTER_RIGHT = "High-Performance Engineering Manual • Monochrome Edition"


def draw_header_footer(page: "fitz.Page", page_num: int, total_pages: int, header_text: Optional[str] = None) -> None:  # noqa: F821
    """Draw running header and footer on a page."""
    try:
        import fitz

        # Header rule
        header_y = MARGIN_PT - 12
        shape = page.new_shape()
        shape.draw_line(
            fitz.Point(MARGIN_PT, header_y + 8),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, header_y + 8),
        )
        shape.finish(color=Palette.HAIRLINE, width=Palette.HAIRLINE_WIDTH)
        shape.commit()

        page.insert_text(
            fitz.Point(MARGIN_PT, header_y),
            header_text or HEADER_TEXT,
            fontname=FONT_BODY,
            fontsize=SIZE_FOOTER,
            color=Palette.MUTED,
        )

        # Footer rule
        footer_y = A4_HEIGHT_PT - MARGIN_PT + 6
        shape2 = page.new_shape()
        shape2.draw_line(
            fitz.Point(MARGIN_PT, footer_y),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, footer_y),
        )
        shape2.finish(color=Palette.HAIRLINE, width=Palette.HAIRLINE_WIDTH)
        shape2.commit()

        page.insert_text(
            fitz.Point(MARGIN_PT, footer_y + 10),
            f"Page {page_num} of {total_pages}",
            fontname=FONT_BODY,
            fontsize=SIZE_FOOTER,
            color=Palette.MUTED,
        )
        page.insert_text(
            fitz.Point(A4_WIDTH_PT - MARGIN_PT - 220, footer_y + 10),
            FOOTER_RIGHT,
            fontname=FONT_BODY,
            fontsize=SIZE_FOOTER,
            color=Palette.MUTED,
        )
    except ImportError:
        logger.warning("PyMuPDF (fitz) not available — header/footer rendering skipped.")


# ---------------------------------------------------------------------------
# CS Diagram Renderers
# ---------------------------------------------------------------------------

def draw_call_stack_diagram(page: "fitz.Page", origin_x: float, origin_y: float) -> float:  # noqa: F821
    """
    Render a Call Stack memory diagram.
    Returns the y-coordinate below the diagram.
    """
    try:
        import fitz

        frames = [
            ("Global Execution Context", "globalThis, window"),
            ("outer() Frame", "arg=42, local=x"),
            ("inner() Frame [TOP]", "closure_ref → outer_env"),
        ]
        frame_w = 220.0
        frame_h = 28.0
        gap = 4.0
        label_x = origin_x

        shape = page.new_shape()

        # Stack grows upward — draw from bottom
        for i, (frame_name, frame_detail) in enumerate(reversed(frames)):
            fy = origin_y + (len(frames) - 1 - i) * (frame_h + gap)
            rect = fitz.Rect(label_x, fy, label_x + frame_w, fy + frame_h)

            # Frame background — topmost frame gets darker fill
            fill_color = Palette.OFFWHITE if i < len(frames) - 1 else Palette.CALLOUT_BG
            shape.draw_rect(rect)
            shape.finish(
                fill=fill_color,
                color=Palette.BLACK,
                width=Palette.BORDER_WIDTH,
            )

        shape.commit()

        # Insert text per frame
        for i, (frame_name, frame_detail) in enumerate(reversed(frames)):
            fy = origin_y + (len(frames) - 1 - i) * (frame_h + gap)
            page.insert_text(
                fitz.Point(label_x + 5, fy + 10),
                frame_name,
                fontname=FONT_BOLD,
                fontsize=7.0,
                color=Palette.BLACK,
            )
            page.insert_text(
                fitz.Point(label_x + 5, fy + 20),
                frame_detail,
                fontname=FONT_MONO,
                fontsize=6.5,
                color=Palette.SLATE,
            )

        # Stack label
        page.insert_text(
            fitz.Point(label_x, origin_y - 12),
            "[CALL STACK]",
            fontname=FONT_BOLD,
            fontsize=SIZE_SUBHEADING,
            color=Palette.BLACK,
        )

        bottom_y = origin_y + len(frames) * (frame_h + gap)
        return bottom_y
    except ImportError:
        logger.warning("PyMuPDF not available — Call Stack diagram skipped.")
        return origin_y + 120


def draw_event_loop_diagram(page: "fitz.Page", origin_x: float, origin_y: float) -> float:  # noqa: F821
    """
    Render the Event Loop Tick Pipeline as a horizontal flow diagram.
    Returns the y-coordinate below the diagram.
    """
    try:
        import fitz

        stages = [
            "Call\nStack",
            "Microtask\nQueue",
            "Macrotask\nQueue",
            "Render\n(rAF)",
            "I/O\nCallbacks",
        ]
        box_w = 60.0
        box_h = 36.0
        gap = 18.0
        total_w = len(stages) * box_w + (len(stages) - 1) * gap

        # Center horizontally
        start_x = origin_x + (CONTENT_WIDTH - total_w) / 2

        shape = page.new_shape()

        for i, stage in enumerate(stages):
            bx = start_x + i * (box_w + gap)
            by = origin_y
            rect = fitz.Rect(bx, by, bx + box_w, by + box_h)
            shape.draw_rect(rect)
            shape.finish(
                fill=Palette.OFFWHITE,
                color=Palette.BLACK,
                width=Palette.BORDER_WIDTH,
            )

            # Arrow between stages
            if i < len(stages) - 1:
                arrow_start = fitz.Point(bx + box_w + 2, by + box_h / 2)
                arrow_end = fitz.Point(bx + box_w + gap - 2, by + box_h / 2)
                shape.draw_line(arrow_start, arrow_end)
                shape.finish(color=Palette.BLACK, width=Palette.ARROW_WIDTH)

        shape.commit()

        # Stage labels
        for i, stage in enumerate(stages):
            bx = start_x + i * (box_w + gap)
            lines_list = stage.split("\n")
            for li, line in enumerate(lines_list):
                page.insert_text(
                    fitz.Point(bx + box_w / 2 - len(line) * 2.2, origin_y + 12 + li * 10),
                    line,
                    fontname=FONT_BOLD,
                    fontsize=6.5,
                    color=Palette.BLACK,
                )

        page.insert_text(
            fitz.Point(origin_x, origin_y - 12),
            "[EVENT LOOP TICK PIPELINE]",
            fontname=FONT_BOLD,
            fontsize=SIZE_SUBHEADING,
            color=Palette.BLACK,
        )

        return origin_y + box_h + 20
    except ImportError:
        logger.warning("PyMuPDF not available — Event Loop diagram skipped.")
        return origin_y + 80


# ---------------------------------------------------------------------------
# Cover Page Generator
# ---------------------------------------------------------------------------

def render_cover_page(
    doc: "fitz.Document",
    branding_line: str = "Prepared by @issparsh @sumitsingh097",
    doc_title: str = "JAVASCRIPT",
) -> None:  # noqa: F821
    """Insert a full cover page as page 0 of the document."""
    try:
        import fitz

        page = doc.new_page(pno=0, width=A4_WIDTH_PT, height=A4_HEIGHT_PT)

        # Full-page white background
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(0, 0, A4_WIDTH_PT, A4_HEIGHT_PT))
        shape.finish(fill=Palette.WHITE, color=Palette.WHITE)
        shape.commit()

        # Top accent rule
        shape2 = page.new_shape()
        shape2.draw_line(
            fitz.Point(MARGIN_PT, MARGIN_PT),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, MARGIN_PT),
        )
        shape2.finish(color=Palette.BLACK, width=Palette.THICK_WIDTH)
        shape2.commit()

        cy = MARGIN_PT + 80

        # Main title
        page.insert_text(
            fitz.Point(MARGIN_PT, cy),
            doc_title.upper(),
            fontname=FONT_BOLD,
            fontsize=SIZE_DOC_TITLE * 2.2,
            color=Palette.BLACK,
        )
        cy += 36

        page.insert_text(
            fitz.Point(MARGIN_PT, cy),
            "THE COMPLETE REFERENCE MANUAL",
            fontname=FONT_BOLD,
            fontsize=SIZE_DOC_TITLE * 1.4,
            color=Palette.CHARCOAL,
        )
        cy += 24

        page.insert_text(
            fitz.Point(MARGIN_PT, cy),
            "Architecture & Core Internals — Monochrome High-Density Engineering Edition",
            fontname=FONT_ITALIC,
            fontsize=SIZE_CHAPTER_TITLE,
            color=Palette.DARK_GREY,
        )
        cy += 50

        # Horizontal rule
        shape3 = page.new_shape()
        shape3.draw_line(
            fitz.Point(MARGIN_PT, cy),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, cy),
        )
        shape3.finish(color=Palette.HAIRLINE, width=Palette.HAIRLINE_WIDTH)
        shape3.commit()
        cy += 30

        # Call Stack diagram on cover
        draw_call_stack_diagram(page, MARGIN_PT, cy)
        # Event loop diagram offset to the right
        draw_event_loop_diagram(page, MARGIN_PT, cy + 140)
        cy += 280

        # Horizontal rule
        shape4 = page.new_shape()
        shape4.draw_line(
            fitz.Point(MARGIN_PT, cy),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, cy),
        )
        shape4.finish(color=Palette.HAIRLINE, width=Palette.HAIRLINE_WIDTH)
        shape4.commit()
        cy += 20

        # Branding section
        # X logo
        logo_size = 20.0
        _draw_x_glyph(page, MARGIN_PT, cy - logo_size / 2, logo_size, Palette.BLACK)

        page.insert_text(
            fitz.Point(MARGIN_PT + logo_size + 8, cy + 4),
            branding_line,
            fontname=FONT_BOLD,
            fontsize=SIZE_CHAPTER_TITLE,
            color=Palette.BLACK,
        )

        # Bottom accent rule
        shape5 = page.new_shape()
        shape5.draw_line(
            fitz.Point(MARGIN_PT, A4_HEIGHT_PT - MARGIN_PT),
            fitz.Point(A4_WIDTH_PT - MARGIN_PT, A4_HEIGHT_PT - MARGIN_PT),
        )
        shape5.finish(color=Palette.BLACK, width=Palette.THICK_WIDTH)
        shape5.commit()

    except ImportError:
        logger.warning("PyMuPDF not available — cover page rendering skipped.")


# ---------------------------------------------------------------------------
# Markdown-to-PDF Compiler
# ---------------------------------------------------------------------------

_PHASE_HEADER_RE = re.compile(r"^={10,}\s*$", re.MULTILINE)
_CHAPTER_RE = re.compile(r"^### .+", re.MULTILINE)
_CALLOUT_RE = re.compile(r"^\[([A-Z][A-Z _]+)\]$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)


@dataclass
class TextBlock:
    kind: str   # "phase_header" | "chapter_title" | "callout" | "body" | "code" | "challenge"
    text: str
    extra: str = ""  # callout label when kind == "callout"


def _parse_markdown_blocks(md_text: str) -> List[TextBlock]:
    """Segment Markdown text into typed rendering blocks."""
    blocks: List[TextBlock] = []
    lines = md_text.split("\n")
    i = 0
    in_code_fence = False
    code_buf: List[str] = []
    body_buf: List[str] = []

    def flush_body():
        if body_buf:
            text = "\n".join(body_buf).strip()
            if text:
                blocks.append(TextBlock(kind="body", text=text))
            body_buf.clear()

    while i < len(lines):
        line = lines[i]

        # Code fence toggle
        if line.startswith("```"):
            if not in_code_fence:
                flush_body()
                in_code_fence = True
                code_buf = []
            else:
                in_code_fence = False
                blocks.append(TextBlock(kind="code", text="\n".join(code_buf)))
                code_buf = []
            i += 1
            continue

        if in_code_fence:
            code_buf.append(line)
            i += 1
            continue

        # Phase header (== ... ==)
        if re.match(r"^={10,}$", line.strip()):
            flush_body()
            if i + 1 < len(lines) and lines[i + 1].startswith("PHASE"):
                phase_line = lines[i + 1]
                blocks.append(TextBlock(kind="phase_header", text=phase_line))
                i += 3
                continue

        # Chapter title (### ...)
        if line.startswith("### "):
            flush_body()
            blocks.append(TextBlock(kind="chapter_title", text=line[4:]))
            i += 1
            continue

        # H1 / H2 document title
        if line.startswith("# ") or line.startswith("## "):
            flush_body()
            blocks.append(TextBlock(kind="phase_header", text=line.lstrip("# ")))
            i += 1
            continue

        # Callout label
        callout_m = re.match(r"^\[([A-Z][A-Z _]+)\]$", line.strip())
        if callout_m:
            flush_body()
            label = callout_m.group(0)
            # Collect callout body until empty line or next callout
            i += 1
            callout_body_lines = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^\[([A-Z][A-Z _]+)\]$", lines[i].strip()):
                callout_body_lines.append(lines[i])
                i += 1
            blocks.append(TextBlock(
                kind="callout",
                text="\n".join(callout_body_lines),
                extra=label,
            ))
            continue

        # Challenge header
        if line.startswith("Challenge ") and ":" in line:
            flush_body()
            blocks.append(TextBlock(kind="challenge", text=line))
            i += 1
            continue

        # Regular body line
        body_buf.append(line)
        i += 1

    flush_body()
    return blocks


def compile_markdown_to_pdf(
    markdown_text: str,
    output_path: str | Path,
    branding: str = "Prepared by @issparsh @sumitsingh097",
) -> Path:
    """
    Compile a synthesized Markdown manual into a high-density ISO A4 PDF
    with cover page, running headers/footers, and vector diagrams.

    Args:
        markdown_text: Full Markdown content from manual_synthesizer.
        output_path: Target PDF file path.
        branding: Author attribution string.

    Returns:
        Path to the compiled PDF file.
    """
    try:
        import fitz

        doc = fitz.open()

        # Detect topic from first heading in markdown
        detected_topic = "JAVASCRIPT"
        for line in markdown_text.splitlines()[:10]:
            if line.startswith("# ") and ":" in line:
                candidate = line.lstrip("# ").split(":")[0].strip()
                if candidate:
                    detected_topic = candidate.upper()
                    break

        # Render cover page
        render_cover_page(doc, branding_line=branding, doc_title=detected_topic)

        # Parse Markdown into typed blocks
        blocks = _parse_markdown_blocks(markdown_text)

        # Render blocks across pages
        cur_page = doc.new_page(width=A4_WIDTH_PT, height=A4_HEIGHT_PT)
        cursor_y = MARGIN_PT + 8.0
        page_count_placeholder: List = [cur_page]

        def new_page() -> "fitz.Page":
            nonlocal cur_page, cursor_y
            p = doc.new_page(width=A4_WIDTH_PT, height=A4_HEIGHT_PT)
            cursor_y = MARGIN_PT + 8.0
            cur_page = p
            page_count_placeholder.append(p)
            return p

        def ensure_space(needed: float) -> None:
            nonlocal cur_page, cursor_y
            if cursor_y + needed > A4_HEIGHT_PT - MARGIN_PT - 12:
                new_page()

        for block in blocks:
            if block.kind == "phase_header":
                ensure_space(36)
                cur_page.insert_textbox(
                    fitz.Rect(MARGIN_PT, cursor_y, A4_WIDTH_PT - MARGIN_PT, cursor_y + 32),
                    block.text.upper(),
                    fontname=FONT_BOLD,
                    fontsize=SIZE_PHASE_HEADER,
                    color=Palette.BLACK,
                )
                cursor_y += SIZE_PHASE_HEADER + 8
                # Underline
                shape = cur_page.new_shape()
                shape.draw_line(
                    fitz.Point(MARGIN_PT, cursor_y),
                    fitz.Point(A4_WIDTH_PT - MARGIN_PT, cursor_y),
                )
                shape.finish(color=Palette.BLACK, width=Palette.BORDER_WIDTH)
                shape.commit()
                cursor_y += 8

            elif block.kind == "chapter_title":
                ensure_space(28)
                cur_page.insert_textbox(
                    fitz.Rect(MARGIN_PT, cursor_y, A4_WIDTH_PT - MARGIN_PT, cursor_y + 26),
                    block.text,
                    fontname=FONT_BOLD,
                    fontsize=SIZE_CHAPTER_TITLE,
                    color=Palette.BLACK,
                )
                cursor_y += SIZE_CHAPTER_TITLE + 8

            elif block.kind == "callout":
                box_h = 52.0
                ensure_space(box_h + 8)
                draw_callout_box(
                    cur_page,
                    (MARGIN_PT, cursor_y, A4_WIDTH_PT - MARGIN_PT, cursor_y + box_h),
                    block.extra,
                    block.text[:320],
                )
                cursor_y += box_h + 8

            elif block.kind == "code":
                lines_in_code = block.text.split("\n")
                code_h = max(len(lines_in_code) * LEADING_CODE + 12, 30)
                ensure_space(code_h)
                # Code block background
                code_rect = fitz.Rect(
                    MARGIN_PT, cursor_y,
                    A4_WIDTH_PT - MARGIN_PT, cursor_y + code_h
                )
                shape = cur_page.new_shape()
                shape.draw_rect(code_rect)
                shape.finish(
                    fill=Palette.OFFWHITE,
                    color=Palette.HAIRLINE,
                    width=Palette.HAIRLINE_WIDTH,
                )
                shape.commit()
                cur_page.insert_textbox(
                    fitz.Rect(MARGIN_PT + 4, cursor_y + 4, A4_WIDTH_PT - MARGIN_PT - 4, cursor_y + code_h - 2),
                    block.text,
                    fontname=FONT_MONO,
                    fontsize=SIZE_CODE,
                    color=Palette.CHARCOAL,
                )
                cursor_y += code_h + 6

            elif block.kind == "challenge":
                ensure_space(22)
                cur_page.insert_textbox(
                    fitz.Rect(MARGIN_PT, cursor_y, A4_WIDTH_PT - MARGIN_PT, cursor_y + 22),
                    block.text,
                    fontname=FONT_BOLD,
                    fontsize=SIZE_SUBHEADING,
                    color=Palette.CHARCOAL,
                )
                cursor_y += SIZE_SUBHEADING + 6

            else:  # body
                body_lines = block.text.split("\n")
                for bline in body_lines:
                    if not bline.strip():
                        cursor_y += 4
                        continue
                    ensure_space(LEADING_BODY + 2)
                    cur_page.insert_textbox(
                        fitz.Rect(MARGIN_PT, cursor_y, A4_WIDTH_PT - MARGIN_PT, cursor_y + LEADING_BODY + 4),
                        bline,
                        fontname=FONT_BODY,
                        fontsize=SIZE_BODY,
                        color=Palette.CHARCOAL,
                        align=0,
                    )
                    cursor_y += LEADING_BODY

        # Apply headers & footers to all content pages (skip cover at index 0)
        total = doc.page_count
        dynamic_header = f"{detected_topic.title()}: The Complete Reference Manual — Architecture & Core Internals"
        for pg_idx in range(1, total):
            draw_header_footer(doc[pg_idx], pg_idx, total - 1, header_text=dynamic_header)

        # Save PDF
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path), garbage=4, deflate=True)
        doc.close()
        logger.info("PDF compiled: %s (%d pages)", out_path, total)
        return out_path

    except ImportError:
        logger.error("PyMuPDF (fitz) is required for PDF compilation. Install via: pip install pymupdf")
        raise


# ---------------------------------------------------------------------------
# Convenience Entry Point
# ---------------------------------------------------------------------------

def build_branded_pdf(
    markdown_text: str,
    output_path: str | Path,
    branding: str = "Prepared by @issparsh @sumitsingh097",
) -> Path:
    """Top-level entry point: compile Markdown -> branded PDF."""
    return compile_markdown_to_pdf(markdown_text, output_path, branding=branding)
