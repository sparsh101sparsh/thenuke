"""Native Vector Technical Diagrams for thenuke Reference Manuals.

Constructs publication-grade vector diagrams using ReportLab Drawing primitives:
- Rect, String, Line, Group, Polygon, PolyLine, Circle
- Strictly adheres to the monochrome palette:
    #000000 (black), #222222 (charcoal), #444444 (dark grey), #666666 (muted),
    #CCCCCC (hairline), #EFEFEF (code bg), #F8F8F8 (card bg), #FFFFFF (white).
- Exact 475 pt printable width to fit ISO A4 margins without overflow.
- All diagrams are pure vector math (0% rasterization, infinite DPI resolution).
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple
from reportlab.graphics.shapes import (
    Drawing,
    Group,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors

# ---------------------------------------------------------------------------
# Strict Monochrome Palette Tokens
# ---------------------------------------------------------------------------
COLOR_BLACK = colors.HexColor("#000000")
COLOR_CHARCOAL = colors.HexColor("#222222")
COLOR_DARK_GREY = colors.HexColor("#444444")
COLOR_MUTED = colors.HexColor("#666666")
COLOR_HAIRLINE = colors.HexColor("#CCCCCC")
COLOR_BG_LIGHT = colors.HexColor("#F8F8F8")
COLOR_BG_BOX = colors.HexColor("#FFFFFF")
COLOR_BG_SHADED = colors.HexColor("#EFEFEF")
COLOR_WHITE = colors.HexColor("#FFFFFF")

TOTAL_WIDTH = 475.0


def _draw_arrow(
    g: Group,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color=COLOR_CHARCOAL,
    stroke_width: float = 1.0,
    head_len: float = 6.0,
    head_width: float = 4.0,
) -> None:
    """Draw a vector line with a sharp triangular arrowhead at (x2, y2)."""
    g.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=stroke_width))
    angle = math.atan2(y2 - y1, x2 - x1)
    # Arrowhead vertices
    x_tip = x2
    y_tip = y2
    x_left = x2 - head_len * math.cos(angle) + head_width * math.sin(angle)
    y_left = y2 - head_len * math.sin(angle) - head_width * math.cos(angle)
    x_right = x2 - head_len * math.cos(angle) - head_width * math.sin(angle)
    y_right = y2 - head_len * math.sin(angle) + head_width * math.cos(angle)

    g.add(
        Polygon(
            [x_tip, y_tip, x_left, y_left, x_right, y_right],
            fillColor=color,
            strokeColor=color,
            strokeWidth=0.5,
        )
    )


def _draw_dashed_line(
    g: Group,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color=COLOR_HAIRLINE,
    stroke_width: float = 0.75,
    dash_len: float = 4.0,
    gap_len: float = 3.0,
) -> None:
    """Draw a dashed line segment."""
    total_dist = math.hypot(x2 - x1, y2 - y1)
    if total_dist == 0:
        return
    dx = (x2 - x1) / total_dist
    dy = (y2 - y1) / total_dist

    curr = 0.0
    while curr < total_dist:
        seg_end = min(curr + dash_len, total_dist)
        sx = x1 + dx * curr
        sy = y1 + dy * curr
        ex = x1 + dx * seg_end
        ey = y1 + dy * seg_end
        g.add(Line(sx, sy, ex, ey, strokeColor=color, strokeWidth=stroke_width))
        curr += dash_len + gap_len


def _make_canvas_frame(height: float, title: str, subtitle: str = "") -> Tuple[Drawing, Group]:
    """Creates a framed container for a technical vector diagram."""
    d = Drawing(TOTAL_WIDTH, height)
    # Outer container box
    d.add(
        Rect(
            0,
            0,
            TOTAL_WIDTH,
            height,
            fillColor=COLOR_BG_LIGHT,
            strokeColor=COLOR_HAIRLINE,
            strokeWidth=0.75,
            rx=3,
            ry=3,
        )
    )
    # Header strip
    d.add(
        Rect(
            0,
            height - 22,
            TOTAL_WIDTH,
            22,
            fillColor=COLOR_BG_SHADED,
            strokeColor=COLOR_HAIRLINE,
            strokeWidth=0.75,
        )
    )
    # Header title
    d.add(
        String(
            10,
            height - 15,
            title.upper(),
            fontName="Helvetica-Bold",
            fontSize=8.5,
            fillColor=COLOR_BLACK,
        )
    )
    if subtitle:
        d.add(
            String(
                TOTAL_WIDTH - 10,
                height - 15,
                subtitle,
                fontName="Helvetica-Oblique",
                fontSize=7.5,
                fillColor=COLOR_MUTED,
                textAnchor="end",
            )
        )

    g = Group()
    d.add(g)
    return d, g


# ---------------------------------------------------------------------------
# 1. Git Object Model & Storage Graph Diagram
# ---------------------------------------------------------------------------
def create_object_model_diagram() -> Drawing:
    """Renders the Git Content-Addressable Object Storage Graph.
    Shows Commit -> Tree -> Blob / Subtree hierarchy with SHA-1 pointers.
    """
    height = 165.0
    d, g = _make_canvas_frame(
        height,
        "Figure 1.1: Git Object Model & Content-Addressable Storage Graph",
        "DAG Hierarchy: Commit ➔ Tree ➔ Blob",
    )

    # 1. Commit Object Box (Left)
    g.add(Rect(15, 75, 125, 60, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(20, 122, "COMMIT OBJECT", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))
    g.add(Line(15, 116, 140, 116, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(20, 105, "hash: 8f3a9d (SHA-1)", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(20, 94, "tree: 4b825d ➔", fontName="Courier", fontSize=7.0, fillColor=COLOR_MUTED))
    g.add(String(20, 83, "author: Linus Torvalds", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))

    # 2. Root Tree Object Box (Center)
    g.add(Rect(175, 55, 130, 80, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(180, 122, "ROOT TREE (DIR)", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))
    g.add(Line(175, 116, 305, 116, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(180, 105, "hash: 4b825d", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(180, 93, "100644 blob a1f2 (main.c)", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(180, 81, "100644 blob c3e4 (README)", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(180, 69, "040000 tree d5a6 (src/) ➔", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # 3. Blobs & Subtree (Right Column)
    # Blob 1
    g.add(Rect(340, 102, 120, 33, fillColor=COLOR_BG_BOX, strokeColor=COLOR_DARK_GREY, strokeWidth=0.75))
    g.add(String(345, 124, "BLOB: main.c", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(345, 111, "hash: a1f2 (zlib data)", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # Blob 2
    g.add(Rect(340, 62, 120, 33, fillColor=COLOR_BG_BOX, strokeColor=COLOR_DARK_GREY, strokeWidth=0.75))
    g.add(String(345, 84, "BLOB: README.md", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(345, 71, "hash: c3e4 (zlib text)", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # Subtree 3
    g.add(Rect(340, 20, 120, 35, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(345, 43, "SUBTREE: src/", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(345, 30, "hash: d5a6 ➔ util.c", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # Connecting Arrows
    _draw_arrow(g, 140, 95, 175, 95, color=COLOR_BLACK, stroke_width=1.2)
    _draw_arrow(g, 305, 95, 340, 118, color=COLOR_CHARCOAL, stroke_width=1.0)
    _draw_arrow(g, 305, 85, 340, 78, color=COLOR_CHARCOAL, stroke_width=1.0)
    _draw_arrow(g, 305, 70, 340, 38, color=COLOR_CHARCOAL, stroke_width=1.0)

    # Invariant Tag at Bottom
    g.add(Rect(15, 15, 300, 22, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(
        String(
            22,
            22,
            "INVARIANT: Blobs store pure data; Trees store filenames + permissions + hashes.",
            fontName="Helvetica-Bold",
            fontSize=7.0,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 2. Three Trees Architecture Diagram
# ---------------------------------------------------------------------------
def create_three_trees_diagram() -> Drawing:
    """Renders the Three Trees Architecture: Working Tree, Index, HEAD Repository."""
    height = 170.0
    d, g = _make_canvas_frame(
        height,
        "Figure 3.1: The Three Trees Architecture & Transition Lifecycle",
        "Working Tree ➔ Index / Staging ➔ HEAD Repository",
    )

    col_w = 125.0
    col_h = 95.0
    y_col = 35.0

    # Column 1: Working Tree
    g.add(Rect(15, y_col, col_w, col_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(22, y_col + col_h - 14, "WORKING TREE", fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_BLACK))
    g.add(String(22, y_col + col_h - 25, "Filesystem / Sandboxed", fontName="Helvetica-Oblique", fontSize=7.0, fillColor=COLOR_MUTED))
    g.add(Line(15, y_col + col_h - 30, 15 + col_w, y_col + col_h - 30, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(22, y_col + 50, "• Active file modifications", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(22, y_col + 38, "• Untracked & dirty files", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(22, y_col + 24, "• Real OS disk files", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(22, y_col + 10, "state: DIRTY / MODIFIED", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_DARK_GREY))

    # Column 2: Staging Index
    g.add(Rect(175, y_col, col_w, col_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(182, y_col + col_h - 14, "STAGING INDEX", fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_BLACK))
    g.add(String(182, y_col + col_h - 25, ".git/index (Binary Cache)", fontName="Helvetica-Oblique", fontSize=7.0, fillColor=COLOR_MUTED))
    g.add(Line(175, y_col + col_h - 30, 175 + col_w, y_col + col_h - 30, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(182, y_col + 50, "• Next commit payload", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(182, y_col + 38, "• stat cache + SHA-1 hash", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(182, y_col + 24, "• Stage resolution matrix", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(182, y_col + 10, "state: STAGED CACHE", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_DARK_GREY))

    # Column 3: HEAD Repository
    g.add(Rect(335, y_col, col_w, col_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(342, y_col + col_h - 14, "HEAD REPOSITORY", fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_BLACK))
    g.add(String(342, y_col + col_h - 25, "Immutable Commit DAG", fontName="Helvetica-Oblique", fontSize=7.0, fillColor=COLOR_MUTED))
    g.add(Line(335, y_col + col_h - 30, 335 + col_w, y_col + col_h - 30, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(342, y_col + 50, "• Cryptographic snapshots", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(342, y_col + 38, "• Permanent commit chain", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(342, y_col + 24, "• Pointer: refs/heads/...", fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
    g.add(String(342, y_col + 10, "state: COMMITTED (IMMUTABLE)", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_DARK_GREY))

    # Transition Arrows
    # 1. git add (Working Tree -> Index)
    _draw_arrow(g, 140, y_col + 65, 175, y_col + 65, color=COLOR_BLACK, stroke_width=1.2)
    g.add(String(144, y_col + 70, "git add", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # 2. git commit (Index -> HEAD)
    _draw_arrow(g, 300, y_col + 65, 335, y_col + 65, color=COLOR_BLACK, stroke_width=1.2)
    g.add(String(302, y_col + 70, "git commit", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # 3. git restore --staged (Index -> Working Tree or unstage)
    _draw_arrow(g, 175, y_col + 40, 140, y_col + 40, color=COLOR_MUTED, stroke_width=0.75)
    g.add(String(142, y_col + 32, "git restore", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # 4. git reset --soft (HEAD -> Index)
    _draw_arrow(g, 335, y_col + 40, 300, y_col + 40, color=COLOR_MUTED, stroke_width=0.75)
    g.add(String(302, y_col + 32, "git reset", fontName="Courier", fontSize=6.5, fillColor=COLOR_MUTED))

    # Bottom summary legend
    g.add(
        String(
            15,
            16,
            "LIFECYCLE PIPELINE: git add copies disk bytes to object store + updates index; git commit creates immutable tree + commit object.",
            fontName="Helvetica-Bold",
            fontSize=7.0,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 3. Branching & Commit DAG Topology Diagram
# ---------------------------------------------------------------------------
def create_branching_dag_diagram() -> Drawing:
    """Renders Branching Pointers, Divergent Commit DAG, and HEAD attachment."""
    height = 155.0
    d, g = _make_canvas_frame(
        height,
        "Figure 6.1: Git Commit Directed Acyclic Graph (DAG) & Branch References",
        "Pointers, HEAD Symref & Divergence Mechanics",
    )

    y_main = 85.0
    y_feature = 40.0

    # Main commit nodes
    # C0
    g.add(Rect(25, y_main - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(37, y_main - 4, "C0", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # C1
    g.add(Rect(110, y_main - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(122, y_main - 4, "C1", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # C2 (Branch point)
    g.add(Rect(195, y_main - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(207, y_main - 4, "C2", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # C3 (main tip)
    g.add(Rect(290, y_main - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(302, y_main - 4, "C3", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # Feature branch commits (branching from C2)
    # C4
    g.add(Rect(260, y_feature - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_DARK_GREY, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(272, y_feature - 4, "C4", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # C5 (feature tip)
    g.add(Rect(350, y_feature - 12, 45, 24, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.2, rx=2, ry=2))
    g.add(String(362, y_feature - 4, "C5", fontName="Helvetica-Bold", fontSize=9.0, fillColor=COLOR_BLACK))

    # Commit DAG Parent Arrows (Child points backwards to Parent!)
    _draw_arrow(g, 110, y_main, 70, y_main, color=COLOR_CHARCOAL, stroke_width=1.0)
    _draw_arrow(g, 195, y_main, 155, y_main, color=COLOR_CHARCOAL, stroke_width=1.0)
    _draw_arrow(g, 290, y_main, 240, y_main, color=COLOR_CHARCOAL, stroke_width=1.0)

    # Feature branch arrows
    _draw_arrow(g, 260, y_feature, 225, y_main - 12, color=COLOR_CHARCOAL, stroke_width=1.0)
    _draw_arrow(g, 350, y_feature, 305, y_feature, color=COLOR_CHARCOAL, stroke_width=1.0)

    # Branch Pointer Labels (Refs)
    # 'main' pointer -> C3
    g.add(Rect(290, y_main + 20, 52, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(296, y_main + 25, "refs: main", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    _draw_arrow(g, 312, y_main + 20, 312, y_main + 12, color=COLOR_BLACK, stroke_width=0.75)

    # 'feature' pointer -> C5
    g.add(Rect(350, y_feature + 20, 60, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(355, y_feature + 25, "refs: feature", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    _draw_arrow(g, 372, y_feature + 20, 372, y_feature + 12, color=COLOR_BLACK, stroke_width=0.75)

    # Active HEAD pointer -> refs: feature
    g.add(Rect(415, y_feature + 18, 50, 22, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(423, y_feature + 25, "HEAD ➔", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_WHITE))
    _draw_arrow(g, 415, y_feature + 29, 410, y_feature + 29, color=COLOR_BLACK, stroke_width=1.0)

    # Explanation text
    g.add(
        String(
            15,
            15,
            "TOPOLOGY RULE: Commits are immutable DAG nodes storing SHA-1 parent hashes. Branches are mutable 41-byte text files holding a SHA-1 pointer.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 4. 3-Way Merge & Lowest Common Ancestor (LCA) Diagram
# ---------------------------------------------------------------------------
def create_three_way_merge_diagram() -> Drawing:
    """Renders 3-Way Merge, Lowest Common Ancestor base resolution, and Merge Commit."""
    height = 160.0
    d, g = _make_canvas_frame(
        height,
        "Figure 7.1: Recursive 3-Way Merge & Lowest Common Ancestor (LCA)",
        "Base Commit B ➔ Ours O + Theirs T ➔ Merge Commit M",
    )

    y_top = 100.0
    y_mid = 70.0
    y_bot = 40.0

    # Base Ancestor B (LCA)
    g.add(Rect(30, y_mid - 14, 55, 28, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.2, rx=2, ry=2))
    g.add(String(40, y_mid - 2, "BASE (B)", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))
    g.add(String(38, y_mid - 11, "LCA Commit", fontName="Helvetica-Oblique", fontSize=6.0, fillColor=COLOR_MUTED))

    # Branch A (Ours / HEAD / main)
    g.add(Rect(160, y_top - 14, 60, 28, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(168, y_top - 2, "OURS (C2)", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))
    g.add(String(166, y_top - 11, "HEAD branch", fontName="Helvetica-Oblique", fontSize=6.0, fillColor=COLOR_MUTED))

    # Branch B (Theirs / feature)
    g.add(Rect(160, y_bot - 14, 60, 28, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=2, ry=2))
    g.add(String(166, y_bot - 2, "THEIRS (C3)", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))
    g.add(String(165, y_bot - 11, "merged branch", fontName="Helvetica-Oblique", fontSize=6.0, fillColor=COLOR_MUTED))

    # Merge Commit M (Two Parents!)
    g.add(Rect(305, y_mid - 16, 75, 32, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.5, rx=3, ry=3))
    g.add(String(312, y_mid + 2, "MERGE (M)", fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_BLACK))
    g.add(String(312, y_mid - 7, "parent1: C2", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(312, y_mid - 15, "parent2: C3", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_CHARCOAL))

    # DAG Links
    # Ours -> Base
    _draw_arrow(g, 160, y_top, 85, y_mid + 7, color=COLOR_CHARCOAL, stroke_width=1.0)
    # Theirs -> Base
    _draw_arrow(g, 160, y_bot, 85, y_mid - 7, color=COLOR_CHARCOAL, stroke_width=1.0)
    # Merge M -> Ours (Parent 1)
    _draw_arrow(g, 305, y_mid + 5, 220, y_top, color=COLOR_BLACK, stroke_width=1.2)
    # Merge M -> Theirs (Parent 2)
    _draw_arrow(g, 305, y_mid - 5, 220, y_bot, color=COLOR_BLACK, stroke_width=1.2)

    # 3-Way Merge Delta Formula Box (Right)
    g.add(Rect(390, 30, 75, 95, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(395, 112, "3-WAY FORMULA:", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(String(395, 98, "ΔO = Ours - Base", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(395, 85, "ΔT = Theirs - Base", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(395, 68, "If ΔO ≠ ΔT on", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_MUTED))
    g.add(String(395, 58, "same line chunk:", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_MUTED))
    g.add(String(395, 42, "CONFLICT!", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # Bottom summary
    g.add(
        String(
            15,
            14,
            "RESOLVER: Git computes git merge-base to find Base B, then computes Myers diff deltas Δ(B➔Ours) and Δ(B➔Theirs).",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 5. Git Rebase Linear Replay Diagram
# ---------------------------------------------------------------------------
def create_rebase_replay_diagram() -> Drawing:
    """Renders Linear Commit Replay during git rebase."""
    height = 155.0
    d, g = _make_canvas_frame(
        height,
        "Figure 8.1: Git Rebase Mechanics — Detached Commit Replay",
        "Original Divergent Commits ➔ Sequential Patch Replay onto Upstream",
    )

    # 1. Before Rebase (Left Half)
    g.add(Rect(10, 25, 220, 105, fillColor=COLOR_BG_BOX, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(18, 118, "BEFORE REBASE (Divergent DAG)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    # Base C1
    g.add(Rect(20, 70, 32, 20, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(30, 76, "C1", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    # Main C2
    g.add(Rect(75, 88, 35, 20, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(85, 94, "C2", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(75, 110, "main", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_MUTED))

    # Feature C3, C4
    g.add(Rect(75, 48, 32, 20, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_DARK_GREY, strokeWidth=0.75))
    g.add(String(85, 54, "C3", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    g.add(Rect(130, 48, 32, 20, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_DARK_GREY, strokeWidth=0.75))
    g.add(String(140, 54, "C4", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(130, 36, "feature", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_MUTED))

    # Links before
    _draw_arrow(g, 75, 98, 52, 80, color=COLOR_CHARCOAL, stroke_width=0.75)
    _draw_arrow(g, 75, 58, 52, 80, color=COLOR_CHARCOAL, stroke_width=0.75)
    _draw_arrow(g, 130, 58, 107, 58, color=COLOR_CHARCOAL, stroke_width=0.75)

    # Center transition symbol
    g.add(String(235, 75, "➔", fontName="Helvetica-Bold", fontSize=14.0, fillColor=COLOR_BLACK))

    # 2. After Rebase (Right Half)
    g.add(Rect(255, 25, 210, 105, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(263, 118, "AFTER REBASE (Linear DAG)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    # Linear sequence: C1 -> C2 -> C3' -> C4'
    g.add(Rect(265, 62, 30, 22, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(273, 69, "C1", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    g.add(Rect(312, 62, 30, 22, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(320, 69, "C2", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(312, 88, "main", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_MUTED))

    g.add(Rect(360, 62, 32, 22, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(368, 69, "C3'", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    g.add(Rect(410, 62, 32, 22, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.2))
    g.add(String(418, 69, "C4'", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(405, 88, "feature (HEAD)", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))

    # Linear Links
    _draw_arrow(g, 312, 73, 295, 73, color=COLOR_CHARCOAL, stroke_width=0.75)
    _draw_arrow(g, 360, 73, 342, 73, color=COLOR_BLACK, stroke_width=1.0)
    _draw_arrow(g, 410, 73, 392, 73, color=COLOR_BLACK, stroke_width=1.0)

    # Bottom summary
    g.add(
        String(
            15,
            12,
            "INVARIANT: git rebase creates NEW commits (C3', C4') with brand-new SHA-1 hashes; original commits (C3, C4) become unreachable orphans.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 6. Remote Tracking & Synchronization Pipeline Diagram
# ---------------------------------------------------------------------------
def create_remote_sync_diagram() -> Drawing:
    """Renders the 4-Stage Distributed Synchronization Pipeline."""
    height = 150.0
    d, g = _make_canvas_frame(
        height,
        "Figure 9.1: Distributed Remote Synchronization Pipeline",
        "Local Repositories ➔ Tracking Refs ➔ Remote Upstream",
    )

    y_pos = 42.0
    box_w = 95.0
    box_h = 75.0

    # 1. Local Working / Index
    g.add(Rect(15, y_pos, box_w, box_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(22, y_pos + box_h - 14, "WORKING / INDEX", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(15, y_pos + box_h - 20, 15 + box_w, y_pos + box_h - 20, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(22, y_pos + 38, "Local sandbox", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(22, y_pos + 26, "Dirty files / staged", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(22, y_pos + 12, "state: UNCOMMITTED", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # 2. Local HEAD branch
    g.add(Rect(130, y_pos, box_w, box_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(137, y_pos + box_h - 14, "LOCAL BRANCH", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(130, y_pos + box_h - 20, 130 + box_w, y_pos + box_h - 20, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(137, y_pos + 38, "refs/heads/main", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(137, y_pos + 26, "Local committed tip", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(137, y_pos + 12, "state: LOCAL COMMITS", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # 3. Remote Tracking Branch
    g.add(Rect(245, y_pos, box_w, box_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(250, y_pos + box_h - 14, "REMOTE-TRACKING", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(245, y_pos + box_h - 20, 245 + box_w, y_pos + box_h - 20, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(250, y_pos + 38, "origin/main", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(250, y_pos + 26, "Read-only pointer", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(250, y_pos + 12, "state: LAST KNOWN", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # 4. Remote Server
    g.add(Rect(360, y_pos, box_w + 5, box_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.2))
    g.add(String(367, y_pos + box_h - 14, "REMOTE UPSTREAM", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(360, y_pos + box_h - 20, 360 + box_w + 5, y_pos + box_h - 20, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(367, y_pos + 38, "GitHub / GitLab", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(367, y_pos + 26, "Bare repository", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_MUTED))
    g.add(String(367, y_pos + 12, "state: CANONICAL", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))

    # Connecting Commands
    # Local commit -> Tracking: git push
    _draw_arrow(g, 225, y_pos + 52, 360, y_pos + 52, color=COLOR_BLACK, stroke_width=1.2)
    g.add(String(270, y_pos + 56, "git push", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # Remote -> Remote tracking: git fetch
    _draw_arrow(g, 360, y_pos + 30, 340, y_pos + 30, color=COLOR_CHARCOAL, stroke_width=1.0)
    g.add(String(280, y_pos + 34, "git fetch", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_CHARCOAL))

    # Remote tracking -> Local: git merge (git pull = fetch + merge)
    _draw_arrow(g, 245, y_pos + 18, 225, y_pos + 18, color=COLOR_CHARCOAL, stroke_width=1.0)
    g.add(String(160, y_pos + 8, "git merge (pull)", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_MUTED))

    # Bottom summary
    g.add(
        String(
            15,
            14,
            "RULE: git fetch downloads packfiles and updates origin/main safely; git pull executes fetch + merge immediately.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 7. Reset vs Restore vs Revert Comparison Matrix
# ---------------------------------------------------------------------------
def create_reset_matrix_diagram() -> Drawing:
    """Renders Comparison Matrix of git reset --soft/--mixed/--hard vs restore."""
    height = 145.0
    d, g = _make_canvas_frame(
        height,
        "Figure 8.2: Git Reset Scope Matrix & Destructive Impact Table",
        "Target Tree Mutations Across Reset Modes",
    )

    y_start = 100.0
    row_h = 18.0

    # Header Row
    g.add(Rect(15, y_start, 445, row_h, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
    g.add(String(22, y_start + 6, "COMMAND / MODE", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(160, y_start + 6, "HEAD", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(250, y_start + 6, "INDEX (STAGE)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(String(350, y_start + 6, "WORKING TREE", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))

    rows = [
        ("git reset --soft HEAD~1", "MOVES", "PRESERVED", "PRESERVED (Safe)"),
        ("git reset --mixed HEAD~1 (Default)", "MOVES", "RESET (Unstaged)", "PRESERVED (Safe)"),
        ("git reset --hard HEAD~1", "MOVES", "RESET", "OVERWRITTEN (DESTRUCTIVE)"),
        ("git restore --staged <file>", "UNCHANGED", "UNSTAGED", "PRESERVED (Safe)"),
    ]

    for idx, (cmd, head_col, idx_col, work_col) in enumerate(rows):
        y = y_start - (idx + 1) * row_h
        bg = COLOR_BG_BOX if idx % 2 == 0 else COLOR_BG_LIGHT
        g.add(Rect(15, y, 445, row_h, fillColor=bg, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        g.add(String(22, y + 5, cmd, fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
        g.add(String(160, y + 5, head_col, fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
        g.add(String(250, y + 5, idx_col, fontName="Helvetica", fontSize=7.0, fillColor=COLOR_CHARCOAL))
        color_w = COLOR_BLACK if "DESTRUCTIVE" in work_col else COLOR_MUTED
        g.add(String(350, y + 5, work_col, fontName="Helvetica-Bold" if "DESTRUCTIVE" in work_col else "Helvetica", fontSize=6.5, fillColor=color_w))

    g.add(
        String(
            15,
            12,
            "RECOVERY: If you run git reset --hard by accident, recover lost commit objects immediately via git reflog.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 8. Git Index Binary Structure Diagram
# ---------------------------------------------------------------------------
def create_index_binary_diagram() -> Drawing:
    """Renders the internal binary anatomy of .git/index."""
    height = 145.0
    d, g = _make_canvas_frame(
        height,
        "Figure 2.1: Binary Anatomy of the .git/index Cache File",
        "Header ➔ Entry Table ➔ Extensions ➔ SHA-1 Checksum",
    )

    y_pos = 45.0
    # 1. 12-byte Header
    g.add(Rect(15, y_pos, 85, 65, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(20, y_pos + 52, "12-BYTE HEADER", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(15, y_pos + 46, 100, y_pos + 46, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(20, y_pos + 34, "4B: 'DIRC' (Magic)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(20, y_pos + 22, "4B: Version 2/3/4", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(20, y_pos + 10, "4B: Entry Count", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # 2. Entry Table
    g.add(Rect(110, y_pos, 185, 65, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(118, y_pos + 52, "SORTED INDEX ENTRIES (Variable)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_BLACK))
    g.add(Line(110, y_pos + 46, 295, y_pos + 46, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(118, y_pos + 34, "ctime / mtime / dev / ino / mode / uid / gid / file size", fontName="Courier", fontSize=5.5, fillColor=COLOR_CHARCOAL))
    g.add(String(118, y_pos + 22, "20-byte SHA-1 Object ID of target Blob", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))
    g.add(String(118, y_pos + 10, "Flags (16-bit) + Variable-length File Path string", fontName="Courier", fontSize=5.5, fillColor=COLOR_MUTED))

    # 3. Optional Extensions
    g.add(Rect(305, y_pos, 85, 65, fillColor=COLOR_BG_BOX, strokeColor=COLOR_DARK_GREY, strokeWidth=0.75))
    g.add(String(312, y_pos + 52, "EXTENSIONS", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))
    g.add(Line(305, y_pos + 46, 390, y_pos + 46, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(312, y_pos + 34, "'TREE' (Cache)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(312, y_pos + 22, "'REUC' (Resolve)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(312, y_pos + 10, "'UNTR' (Untracked)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # 4. Checksum
    g.add(Rect(400, y_pos, 60, 65, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(405, y_pos + 52, "CHECKSUM", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(Line(400, y_pos + 46, 460, y_pos + 46, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(405, y_pos + 26, "20-byte", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(String(405, y_pos + 14, "SHA-1 Hash", fontName="Courier", fontSize=6.0, fillColor=COLOR_MUTED))

    # Connectors
    _draw_arrow(g, 100, y_pos + 32, 110, y_pos + 32, color=COLOR_CHARCOAL, stroke_width=0.75)
    _draw_arrow(g, 295, y_pos + 32, 305, y_pos + 32, color=COLOR_CHARCOAL, stroke_width=0.75)
    _draw_arrow(g, 390, y_pos + 32, 400, y_pos + 32, color=COLOR_CHARCOAL, stroke_width=0.75)

    g.add(
        String(
            15,
            14,
            "STAT CACHE: Git uses lstat() filesystem metadata to avoid re-reading file contents when disk mtime equals index mtime.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 9. Merge Conflict Anatomy Diagram
# ---------------------------------------------------------------------------
def create_merge_conflict_diagram() -> Drawing:
    """Renders the anatomy of a Git 3-Way Merge Conflict block."""
    height = 150.0
    d, g = _make_canvas_frame(
        height,
        "Figure 7.2: Anatomical Structure of a 3-Way Merge Conflict Marker",
        "Diff3 Marker View: HEAD ➔ Common Base ➔ Incoming Branch",
    )

    y_base = 28.0
    box_w = 445.0
    box_h = 95.0

    g.add(Rect(15, y_base, box_w, box_h, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0))

    # Conflict Marker Sections
    # 1. <<<<<<< HEAD
    g.add(Rect(20, y_base + 70, box_w - 10, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(28, y_base + 75, "<<<<<<< HEAD (Current Change / Ours)", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # Our code line
    g.add(String(28, y_base + 55, "const apiEndpoint = 'https://api.v2.internal/users';", fontName="Courier", fontSize=6.5, fillColor=COLOR_CHARCOAL))

    # 2. =======
    g.add(Line(20, y_base + 48, 20 + box_w - 10, y_base + 48, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(28, y_base + 40, "=======", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # Their code line
    g.add(String(28, y_base + 26, "const apiEndpoint = 'https://gateway.cloud.company.com/v1/users';", fontName="Courier", fontSize=6.5, fillColor=COLOR_CHARCOAL))

    # 3. >>>>>>> branch
    g.add(Rect(20, y_base + 5, box_w - 10, 16, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(28, y_base + 10, ">>>>>>> feature-cloud-migration (Incoming Change / Theirs)", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    g.add(
        String(
            15,
            12,
            "DIFF3 TIP: Enable 'git config --global merge.conflictstyle diff3' to inspect the Common Base version between markers.",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_BLACK,
        )
    )

    return d


# ---------------------------------------------------------------------------
# 10. Sleep Architecture & Ultradian Cycles Diagram
# ---------------------------------------------------------------------------
def create_sleep_architecture_diagram() -> Drawing:
    """Renders the 90-Minute Sleep Architecture & Ultradian Cycles."""
    height = 160.0
    d, g = _make_canvas_frame(
        height,
        "Figure 1.1: Human Sleep Architecture & Ultradian 90-Minute Cycles",
        "NREM Slow-Wave vs REM Distribution",
    )

    cycle_w = 100.0
    x_start = 20.0
    y_base = 35.0

    cycles = [
        ("Cycle 1 (0:00 - 1:30)", 70, 20),
        ("Cycle 2 (1:30 - 3:00)", 55, 35),
        ("Cycle 3 (3:00 - 4:30)", 40, 50),
        ("Cycle 4 (4:30 - 6:00)", 25, 65),
    ]

    for i, (title, nrem_h, rem_h) in enumerate(cycles):
        cx = x_start + i * 110.0
        g.add(Rect(cx, y_base, cycle_w, 90, fillColor=COLOR_BG_BOX, strokeColor=COLOR_HAIRLINE, strokeWidth=0.75, rx=2, ry=2))
        g.add(Rect(cx, y_base + 72, cycle_w, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        g.add(String(cx + 6, y_base + 78, title, fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))

        # Deep NREM Bar (Charcoal)
        g.add(Rect(cx + 10, y_base + 20, 35, nrem_h * 0.65, fillColor=COLOR_CHARCOAL, strokeColor=COLOR_BLACK, strokeWidth=0.5))
        g.add(String(cx + 12, y_base + 8, "NREM SWS", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_CHARCOAL))

        # REM Bar (Light shaded with border)
        g.add(Rect(cx + 55, y_base + 20, 35, rem_h * 0.65, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75))
        g.add(String(cx + 62, y_base + 8, "REM DREAM", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))

    g.add(String(20, 14, "INVARIANT: Early night is optimized for anatomical & memory consolidation (SWS); late night for emotional & associative synthesis (REM).", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    return d


# ---------------------------------------------------------------------------
# 11. Hippocampal-Neocortical Memory Transfer Diagram
# ---------------------------------------------------------------------------
def create_memory_transfer_diagram() -> Drawing:
    """Renders the Hippocampal-Neocortical Memory Consolidation Protocol."""
    height = 150.0
    d, g = _make_canvas_frame(
        height,
        "Figure 2.1: Hippocampal-Neocortical Memory Consolidation Pipeline",
        "Slow-Wave Sleep (<1 Hz) & Spindle (11-16 Hz) Coupling",
    )

    y_box = 35.0

    # 1. Hippocampus Box (Left - Volatile Cache / Temporary RAM)
    g.add(Rect(20, y_box, 135, 85, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=3, ry=3))
    g.add(Rect(20, y_box + 67, 135, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(26, y_box + 73, "HIPPOCAMPUS (Volatile RAM)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))
    g.add(String(26, y_box + 50, "• Short-term memory buffer", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(26, y_box + 38, "• Vulnerable to overwrite", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(26, y_box + 26, "• High turnover rate", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(26, y_box + 12, "STATUS: Cache Full at Bedtime", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_MUTED))

    # 2. Middle Channel (The Transfer Bus)
    _draw_arrow(g, 160, y_box + 50, 310, y_box + 50, color=COLOR_BLACK, stroke_width=1.5, head_len=8, head_width=5)
    g.add(Rect(175, y_box + 56, 120, 22, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=0.75, rx=2, ry=2))
    g.add(String(182, y_box + 68, "SLOW-WAVE OSCILLATIONS (<1 Hz)", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))
    g.add(String(190, y_box + 59, "+ SLEEP SPINDLES (11-16 Hz)", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # Feedback / Clear Cache Arrow
    _draw_arrow(g, 310, y_box + 20, 160, y_box + 20, color=COLOR_MUTED, stroke_width=1.0, head_len=6, head_width=4)
    g.add(String(185, y_box + 10, "CACHE FLUSH (Frees Next-Day Buffer)", fontName="Courier", fontSize=5.5, fillColor=COLOR_MUTED))

    # 3. Neocortex Box (Right - Distributed Long-Term Storage / HDD)
    g.add(Rect(315, y_box, 140, 85, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=3, ry=3))
    g.add(Rect(315, y_box + 67, 140, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(321, y_box + 73, "NEOCORTEX (Permanent Storage)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))
    g.add(String(321, y_box + 50, "• Infinite distributed capacity", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(321, y_box + 38, "• Schema integration & synaptogenesis", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(321, y_box + 26, "• Immune to simple overwrite", fontName="Helvetica", fontSize=6.5, fillColor=COLOR_CHARCOAL))
    g.add(String(321, y_box + 12, "STATUS: Consolidated Storage", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))

    g.add(String(20, 12, "PROVEN INVARIANT: Sleep deprivation after learning drops retention by 40% (Nature Neuroscience 10:385).", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    return d


# ---------------------------------------------------------------------------
# 12. Adenosine Sleep Pressure & Caffeine Blockade Diagram
# ---------------------------------------------------------------------------
def create_adenosine_caffeine_diagram() -> Drawing:
    """Renders the Adenosine Homeostatic Sleep Pressure & Caffeine Antagonism Curve."""
    height = 155.0
    d, g = _make_canvas_frame(
        height,
        "Figure 3.1: Adenosine Sleep Pressure & Competitive Caffeine Blockade",
        "Two-Process Model: Process S vs Receptor Antagonism",
    )

    y_base = 32.0

    # Axes
    g.add(Line(35, y_base, 450, y_base, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(Line(35, y_base, 35, y_base + 95, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(20, y_base + 88, "High", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_MUTED))
    g.add(String(20, y_base, "Low", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_MUTED))
    g.add(String(40, y_base - 10, "7:00 AM (Awake)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(160, y_base - 10, "1:00 PM (Coffee)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(290, y_base - 10, "7:00 PM (Evening)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(390, y_base - 10, "11:00 PM (Sleep Crash)", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))

    # Adenosine Accumulation Curve
    pts = [
        (35, y_base + 5), (90, y_base + 22), (160, y_base + 45),
        (230, y_base + 65), (310, y_base + 78), (390, y_base + 90)
    ]
    for idx in range(len(pts) - 1):
        g.add(Line(pts[idx][0], pts[idx][1], pts[idx+1][0], pts[idx+1][1], strokeColor=COLOR_BLACK, strokeWidth=1.5))
    g.add(String(170, y_base + 80, "Real Adenosine Pressure (Process S)", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))

    # Caffeine Blockade Shadow (Dotted line effect)
    c_pts = [
        (160, y_base + 45), (200, y_base + 25), (250, y_base + 20),
        (300, y_base + 35), (350, y_base + 60), (390, y_base + 90)
    ]
    for idx in range(len(c_pts) - 1):
        g.add(Line(c_pts[idx][0], c_pts[idx][1], c_pts[idx+1][0], c_pts[idx+1][1], strokeColor=COLOR_MUTED, strokeWidth=1.0))
    g.add(String(205, y_base + 12, "Perceived Fatigue (Caffeine Masking)", fontName="Helvetica-Oblique", fontSize=6.0, fillColor=COLOR_MUTED))

    # Crash Arrow at 11 PM
    _draw_arrow(g, 390, y_base + 88, 390, y_base + 25, color=COLOR_CHARCOAL, stroke_width=1.2, head_len=6, head_width=4)
    g.add(String(330, y_base + 45, "CAFFEINE CRASH: Liver clears drug,", fontName="Courier-Bold", fontSize=5.5, fillColor=COLOR_BLACK))
    g.add(String(330, y_base + 37, "accumulated adenosine floods brain.", fontName="Courier", fontSize=5.5, fillColor=COLOR_CHARCOAL))

    # Explanatory Callout Box
    g.add(Rect(310, y_base + 55, 140, 35, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=0.5, rx=2, ry=2))
    g.add(String(315, y_base + 78, "RECEPTOR ANTAGONISM:", fontName="Helvetica-Bold", fontSize=6.0, fillColor=COLOR_BLACK))
    g.add(String(315, y_base + 68, "Caffeine binds A1/A2A receptors without", fontName="Helvetica", fontSize=5.5, fillColor=COLOR_CHARCOAL))
    g.add(String(315, y_base + 60, "activating them. Adenosine continues to climb.", fontName="Helvetica", fontSize=5.5, fillColor=COLOR_CHARCOAL))

    g.add(String(20, 10, "PHARMACOKINETICS: Caffeine half-life is 5-7 hours; quarter-life 10-12 hours. Afternoon coffee impairs Stage 3/4 sleep.", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    return d


# ---------------------------------------------------------------------------
# 13. Natural Killer (NK) Cell Immunological Collapse Diagram
# ---------------------------------------------------------------------------
def create_immune_killer_cells_diagram() -> Drawing:
    """Renders the Natural Killer (NK) Cell Immunological Vulnerability Diagram."""
    height = 150.0
    d, g = _make_canvas_frame(
        height,
        "Figure 4.1: Natural Killer (NK) Cell Cytotoxic Collapse (4-Hour Sleep Loss)",
        "Empirical Benchmark: 70% Reduction in Innate Tumor Clearance",
    )

    y_base = 35.0

    # Left Container: Baseline 8 Hours of Sleep
    g.add(Rect(35, y_base, 180, 85, fillColor=COLOR_BG_BOX, strokeColor=COLOR_HAIRLINE, strokeWidth=0.75, rx=3, ry=3))
    g.add(Rect(35, y_base + 67, 180, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(42, y_base + 73, "BASELINE SLEEP (8 HOURS)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # 100% Bar
    g.add(Rect(50, y_base + 15, 45, 48, fillColor=COLOR_CHARCOAL, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(58, y_base + 35, "100%", fontName="Helvetica-Bold", fontSize=10.0, fillColor=COLOR_WHITE))
    g.add(String(105, y_base + 45, "Optimal NK Lytic Activity", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(String(105, y_base + 34, "• Continuous tumor surveillance", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(105, y_base + 24, "• Rapid virus particle lysis", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(105, y_base + 14, "• Low systemic inflammation", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # Right Container: Restricted Sleep (4 Hours Single Night)
    g.add(Rect(240, y_base, 205, 85, fillColor=COLOR_BG_BOX, strokeColor=COLOR_BLACK, strokeWidth=1.0, rx=3, ry=3))
    g.add(Rect(240, y_base + 67, 205, 18, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(247, y_base + 73, "PARTIAL SLEEP RESTRICTION (4 HOURS)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=COLOR_BLACK))

    # 30% Bar (70% Deficit)
    g.add(Rect(255, y_base + 15, 45, 15, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(265, y_base + 19, "30%", fontName="Helvetica-Bold", fontSize=8.0, fillColor=COLOR_BLACK))

    # Deficit Marker
    g.add(Rect(255, y_base + 30, 45, 33, fillColor=COLOR_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(258, y_base + 44, "-70% LOSS", fontName="Courier-Bold", fontSize=7.0, fillColor=COLOR_CHARCOAL))

    # Clinical Consequences
    g.add(String(310, y_base + 50, "IMMUNE DEFENSE COLLAPSE:", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(String(310, y_base + 38, "• 70% drop in NK cytotoxicity", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(310, y_base + 27, "• WHO classifies shift-work as carcinogen", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(310, y_base + 16, "• 711 genes disrupted (PNAS 110:E1132)", fontName="Helvetica", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    _draw_arrow(g, 220, y_base + 40, 235, y_base + 40, color=COLOR_BLACK, stroke_width=1.0, head_len=5, head_width=3)
    g.add(String(20, 12, "ONCOLOGICAL INVARIANT: Natural killer cells act as biological 007 agents. Single-night sleep loss disables surveillance.", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    return d


# ---------------------------------------------------------------------------
# 14. Core Body Thermoregulation & Circadian Sleep Gate Diagram
# ---------------------------------------------------------------------------
def create_thermal_circadian_diagram() -> Drawing:
    """Renders the Core Body Thermoregulation & Circadian Sleep Gate Diagram."""
    height = 155.0
    d, g = _make_canvas_frame(
        height,
        "Figure 5.1: Core Body Thermoregulation & Melatonin Circadian Gate",
        "Suprachiasmatic Nucleus Signaling & Distal Vasodilation",
    )

    y_base = 32.0

    # Axes
    g.add(Line(35, y_base, 450, y_base, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(Line(35, y_base, 35, y_base + 95, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    g.add(String(40, y_base - 10, "12:00 PM (Noon)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(145, y_base - 10, "6:00 PM (Peak Temp)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))
    g.add(String(270, y_base - 10, "11:00 PM (Sleep Onset)", fontName="Courier-Bold", fontSize=6.0, fillColor=COLOR_BLACK))
    g.add(String(390, y_base - 10, "4:00 AM (Thermal Min)", fontName="Courier", fontSize=6.0, fillColor=COLOR_CHARCOAL))

    # Core Temperature Curve
    temp_pts = [
        (35, y_base + 65), (145, y_base + 85), (220, y_base + 70),
        (270, y_base + 40), (340, y_base + 20), (390, y_base + 12), (450, y_base + 35)
    ]
    for idx in range(len(temp_pts) - 1):
        g.add(Line(temp_pts[idx][0], temp_pts[idx][1], temp_pts[idx+1][0], temp_pts[idx+1][1], strokeColor=COLOR_BLACK, strokeWidth=1.5))
    g.add(String(90, y_base + 90, "Core Body Temperature (Drops 2-3°F / 1°C for sleep)", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))

    # Melatonin Secretion Surge Curve
    mel_pts = [
        (35, y_base + 8), (145, y_base + 12), (220, y_base + 30),
        (270, y_base + 70), (340, y_base + 85), (390, y_base + 75), (450, y_base + 20)
    ]
    for idx in range(len(mel_pts) - 1):
        g.add(Line(mel_pts[idx][0], mel_pts[idx][1], mel_pts[idx+1][0], mel_pts[idx+1][1], strokeColor=COLOR_MUTED, strokeWidth=1.2))
    g.add(String(275, y_base + 60, "Melatonin Surge (Pineal Gland)", fontName="Helvetica-Oblique", fontSize=6.5, fillColor=COLOR_MUTED))

    # Shaded Sleep Window Container
    g.add(Rect(270, y_base, 180, 95, fillColor=COLOR_BG_SHADED, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    g.add(String(275, y_base + 82, "CIRCADIAN SLEEP WINDOW", fontName="Courier-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    g.add(String(275, y_base + 30, "• Ambient Room Temp: ~65°F (18.3°C)", fontName="Helvetica", fontSize=5.5, fillColor=COLOR_CHARCOAL))
    g.add(String(275, y_base + 20, "• Distal vasodilation radiates heat from hands/feet", fontName="Helvetica", fontSize=5.5, fillColor=COLOR_CHARCOAL))
    g.add(String(275, y_base + 10, "• Warm bath paradoxical cooling effect", fontName="Helvetica", fontSize=5.5, fillColor=COLOR_CHARCOAL))

    g.add(String(20, 10, "ACTIONABLE INVARIANT: Sleeping in a room warmer than 70°F (21°C) prevents core body cooling, fracturing NREM SWS.", fontName="Helvetica-Bold", fontSize=6.5, fillColor=COLOR_BLACK))
    return d


# ---------------------------------------------------------------------------
# Registry Map
# ---------------------------------------------------------------------------
DIAGRAM_REGISTRY = {
    "object_model": create_object_model_diagram,
    "three_trees": create_three_trees_diagram,
    "branching_dag": create_branching_dag_diagram,
    "three_way_merge": create_three_way_merge_diagram,
    "rebase_replay": create_rebase_replay_diagram,
    "remote_sync": create_remote_sync_diagram,
    "reset_matrix": create_reset_matrix_diagram,
    "index_binary": create_index_binary_diagram,
    "merge_conflict": create_merge_conflict_diagram,
    "sleep_architecture": create_sleep_architecture_diagram,
    "memory_transfer": create_memory_transfer_diagram,
    "adenosine_caffeine": create_adenosine_caffeine_diagram,
    "immune_killer_cells": create_immune_killer_cells_diagram,
    "thermal_circadian": create_thermal_circadian_diagram,
}


def get_diagram(diagram_name: str) -> Optional[Drawing]:
    """Retrieve a pre-built publication vector diagram by name."""
    builder = DIAGRAM_REGISTRY.get(diagram_name.strip().lower())
    if builder is not None:
        return builder()
    return None
