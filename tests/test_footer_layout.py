"""Tests for Two-Column Running Footer Geometry & Zero Overlap."""

from pathlib import Path
import pytest
import pymupdf


def test_compiled_manual_footer_gutter_and_no_overlap():
    pdf_path = Path("/Users/iamsparsh00321/Downloads/Git_Complete_Reference_Manual.pdf")
    if not pdf_path.exists():
        pytest.skip("Git manual not found in Downloads directory")

    doc = pymupdf.open(str(pdf_path))
    assert len(doc) >= 60

    min_gutter = 9999.0
    for pno in range(1, len(doc)):
        page = doc[pno]
        words = [w for w in page.get_text("words") if w[1] >= 790 or w[3] >= 790]
        left_words = [
            w for w in words
            if w[4] in ["Page", "of", "•", "Monochrome", "Reference", "Edition"] or (w[4].isdigit() and float(w[0]) < 300)
        ]
        right_words = [
            w for w in words
            if w[4] in ["Prepared", "by", "@issparsh", "@sumitsingh097"]
        ]

        if not left_words or not right_words:
            continue

        max_left_x = max(w[2] for w in left_words)
        min_right_x = min(w[0] for w in right_words)
        gutter = min_right_x - max_left_x
        if gutter < min_gutter:
            min_gutter = gutter

    assert min_gutter > 140.0, f"Footer gutter must be > 140 pt, found {min_gutter:.2f} pt"
