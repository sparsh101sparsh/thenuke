"""Corpus Indexer & Evidence Layer for thenuke.

Provides structured indexing and evidence extraction over UnifiedCorpus,
enabling downstream synthesizers to cite, quote, and ground technical manuals
in real ingested video transcripts, web documentation, and local files.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from scripts.ingestion.unified_corpus import UnifiedCorpus, IngestionSource, Chapter, CodeBlock


@dataclass
class EvidenceSpan:
    """Represents a discrete, citable unit of ingested source evidence."""
    span_id: str
    source_type: str  # 'youtube', 'web', 'local_file', 'cp_problem'
    source_id: str    # URL or file identifier
    source_title: str
    section_hint: str
    span_type: str    # 'transcript', 'code', 'table', 'header', 'ocr', 'prose'
    content: str
    timestamp_range: Optional[tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "section_hint": self.section_hint,
            "span_type": self.span_type,
            "content": self.content,
            "timestamp_range": self.timestamp_range,
            "metadata": self.metadata,
        }


class CorpusIndexer:
    """Indexes a UnifiedCorpus into structured EvidenceSpans and thematic sections."""

    def __init__(self, corpus: Union[UnifiedCorpus, Dict[str, Any], Path, str, None] = None):
        self.sources: List[IngestionSource] = []
        self.spans: List[EvidenceSpan] = []
        self.sections: List[Dict[str, Any]] = []

        if corpus is not None:
            self.load(corpus)

    def load(self, corpus: Union[UnifiedCorpus, Dict[str, Any], Path, str]) -> None:
        """Load and index corpus data."""
        if isinstance(corpus, (str, Path)):
            p = Path(corpus)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                self._load_dict(data)
        elif isinstance(corpus, UnifiedCorpus):
            self.sources = corpus.sources
            self._index_sources()
        elif isinstance(corpus, dict):
            self._load_dict(corpus)

    def _load_dict(self, data: Dict[str, Any]) -> None:
        """Parse dictionary structure into sources and index."""
        raw_sources = data.get("sources", [])
        self.sources = [IngestionSource.from_dict(s) for s in raw_sources]
        self._index_sources()

    def _index_sources(self) -> None:
        """Deconstruct all sources into EvidenceSpans and sections."""
        self.spans.clear()
        self.sections.clear()

        for s_idx, src in enumerate(self.sources, start=1):
            s_title = src.title or f"Source {s_idx}"
            s_id = src.identifier or f"src_{s_idx}"
            s_type = src.source_type

            # 1. Index Chapters / Transcripts
            for ch in src.chapters:
                ch_title = ch.title.strip() if ch.title else f"Section {ch.chapter_index}"
                ch_text = ch.text.strip()
                if not ch_text:
                    continue

                # Split chapter into paragraphs or chunks of ~200-400 words
                paragraphs = [p.strip() for p in ch_text.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [ch_text]

                span_type = "transcript" if s_type == "youtube" else "prose"
                for p_idx, para in enumerate(paragraphs, start=1):
                    span = EvidenceSpan(
                        span_id=f"{s_id[:12]}_ch{ch.chapter_index}_p{p_idx}_{uuid.uuid4().hex[:6]}",
                        source_type=s_type,
                        source_id=s_id,
                        source_title=s_title,
                        section_hint=ch_title,
                        span_type=span_type,
                        content=para,
                        timestamp_range=(ch.start_time, ch.end_time) if ch.end_time > 0 else None,
                        metadata={"chapter_index": ch.chapter_index},
                    )
                    self.spans.append(span)

            # 2. Index Extracted Code Blocks
            for cb_idx, cb in enumerate(src.extracted_code_blocks, start=1):
                if not cb.code.strip():
                    continue
                span = EvidenceSpan(
                    span_id=f"{s_id[:12]}_code_{cb_idx}_{uuid.uuid4().hex[:6]}",
                    source_type=s_type,
                    source_id=s_id,
                    source_title=s_title,
                    section_hint="Extracted Code Snippet",
                    span_type="code",
                    content=cb.code.strip(),
                    metadata={"language": cb.language},
                )
                self.spans.append(span)

            # 3. Index Extracted Images / OCR
            for im_idx, im in enumerate(src.extracted_images, start=1):
                ocr = im.ocr_text.strip()
                if not ocr:
                    continue
                span = EvidenceSpan(
                    span_id=f"{s_id[:12]}_ocr_{im_idx}_{uuid.uuid4().hex[:6]}",
                    source_type=s_type,
                    source_id=s_id,
                    source_title=s_title,
                    section_hint=im.caption or "Visual Slide / Frame OCR",
                    span_type="ocr",
                    content=ocr,
                    metadata={"image_path": im.path, "caption": im.caption},
                )
                self.spans.append(span)

        self._build_thematic_sections()

    def _build_thematic_sections(self) -> None:
        """Group evidence spans into coherent sections."""
        section_map: Dict[str, List[EvidenceSpan]] = {}

        for span in self.spans:
            hint = span.section_hint or "General Fundamentals"
            # Normalize hint
            clean_hint = re.sub(r"^\d+[\.\-\s]+", "", hint).strip().title()
            if not clean_hint:
                clean_hint = "Core Engineering Principles"
            if clean_hint not in section_map:
                section_map[clean_hint] = []
            section_map[clean_hint].append(span)

        for title, span_list in section_map.items():
            self.sections.append({
                "title": title,
                "spans": span_list,
                "quote_count": len([s for s in span_list if s.span_type in ("transcript", "prose")]),
                "code_count": len([s for s in span_list if s.span_type == "code"]),
            })

    def get_all_spans(self) -> List[EvidenceSpan]:
        """Return all indexed evidence spans."""
        return list(self.spans)

    def get_spans_by_type(self, span_type: str) -> List[EvidenceSpan]:
        """Return spans filtered by type ('transcript', 'code', 'ocr', 'prose')."""
        return [s for s in self.spans if s.span_type == span_type]

    def get_sections(self) -> List[Dict[str, Any]]:
        """Return thematic sections containing clustered evidence spans."""
        return list(self.sections)

    def total_evidence_words(self) -> int:
        """Count total words across all evidence spans."""
        return sum(len(s.content.split()) for s in self.spans)
