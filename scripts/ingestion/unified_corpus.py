"""Unified Corpus Data Model and Serializer for thenuke skill.

Defines data classes and serialization for the intermediate ingestion output
(nuke_ingestion_corpus.json) conforming to PROJECT.md § 4.1 specification.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Chapter:
    """Represents a coherent chapter, slide, or content section."""
    chapter_index: int
    title: str
    start_time: float
    end_time: float
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_index": self.chapter_index,
            "title": self.title,
            "start_time": round(float(self.start_time), 3),
            "end_time": round(float(self.end_time), 3),
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Chapter:
        return cls(
            chapter_index=int(data.get("chapter_index", 0)),
            title=str(data.get("title", "")),
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 0.0)),
            text=str(data.get("text", "")),
        )


@dataclass
class CodeBlock:
    """Represents an extracted source code snippet."""
    language: str
    code: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language or "text",
            "code": self.code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CodeBlock:
        return cls(
            language=str(data.get("language", "text")),
            code=str(data.get("code", "")),
        )


@dataclass
class ExtractedImage:
    """Represents an extracted or captured image/screenshot with OCR text."""
    path: str
    caption: str = ""
    ocr_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "caption": self.caption,
            "ocr_text": self.ocr_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExtractedImage:
        return cls(
            path=str(data.get("path", "")),
            caption=str(data.get("caption", "")),
            ocr_text=str(data.get("ocr_text", "")),
        )


@dataclass
class IngestionSource:
    """Represents a single ingested multi-modal source (YouTube, Web, Local)."""
    source_type: str  # "youtube", "web", or "local_file"
    identifier: str  # URL or relative file path
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chapters: List[Chapter] = field(default_factory=list)
    extracted_code_blocks: List[CodeBlock] = field(default_factory=list)
    extracted_images: List[ExtractedImage] = field(default_factory=list)

    def add_chapter(
        self,
        title: str,
        text: str,
        start_time: float = 0.0,
        end_time: float = 0.0,
        chapter_index: Optional[int] = None,
    ) -> Chapter:
        idx = chapter_index if chapter_index is not None else len(self.chapters) + 1
        chapter = Chapter(
            chapter_index=idx,
            title=title,
            start_time=start_time,
            end_time=end_time,
            text=text,
        )
        self.chapters.append(chapter)
        return chapter

    def add_code_block(self, code: str, language: str = "text") -> CodeBlock:
        block = CodeBlock(language=language or "text", code=code)
        self.extracted_code_blocks.append(block)
        return block

    def add_image(self, path: str, caption: str = "", ocr_text: str = "") -> ExtractedImage:
        img = ExtractedImage(path=path, caption=caption, ocr_text=ocr_text)
        self.extracted_images.append(img)
        return img

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "identifier": self.identifier,
            "title": self.title,
            "metadata": self.metadata,
            "chapters": [c.to_dict() for c in self.chapters],
            "extracted_code_blocks": [cb.to_dict() for cb in self.extracted_code_blocks],
            "extracted_images": [img.to_dict() for img in self.extracted_images],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IngestionSource:
        return cls(
            source_type=str(data.get("source_type", "local_file")),
            identifier=str(data.get("identifier", "")),
            title=str(data.get("title", "")),
            metadata=dict(data.get("metadata", {})),
            chapters=[Chapter.from_dict(c) for c in data.get("chapters", [])],
            extracted_code_blocks=[
                CodeBlock.from_dict(cb) for cb in data.get("extracted_code_blocks", [])
            ],
            extracted_images=[
                ExtractedImage.from_dict(img) for img in data.get("extracted_images", [])
            ],
        )


@dataclass
class UnifiedCorpus:
    """Unified corpus container for all ingested raw materials."""
    corpus_id: str = field(default_factory=lambda: f"corpus_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sources: List[IngestionSource] = field(default_factory=list)
    aggregated_topics: List[str] = field(default_factory=list)

    def add_source(self, source: IngestionSource) -> None:
        self.sources.append(source)
        self.extract_topics()

    def extract_topics(self) -> List[str]:
        """Extract recurring technical topics and keywords across all sources."""
        stop_words = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with",
            "is", "are", "was", "were", "this", "that", "it", "of", "from", "by",
            "as", "be", "have", "has", "do", "does", "will", "can", "how", "what",
            "why", "chapter", "slide", "section", "part", "video", "introduction",
            "overview", "summary", "conclusion"
        }
        topic_counts: Dict[str, int] = {}

        # Heuristic 1: Titles of sources and chapters
        for source in self.sources:
            # Source title tokens
            for token in re.split(r"[\s\-_,:|]+", source.title):
                clean = token.strip().lower()
                if clean and len(clean) > 2 and clean not in stop_words and not clean.isnumeric():
                    topic_counts[token.strip()] = topic_counts.get(token.strip(), 0) + 3

            # Chapter titles
            for chapter in source.chapters:
                for token in re.split(r"[\s\-_,:|]+", chapter.title):
                    clean = token.strip().lower()
                    if clean and len(clean) > 2 and clean not in stop_words and not clean.isnumeric():
                        topic_counts[token.strip()] = topic_counts.get(token.strip(), 0) + 2

                # Technical keywords in chapter text (e.g., CamelCase, PascalCase, or specific markers)
                tech_matches = re.findall(r"\b[A-Z][a-zA-Z0-9_]{3,}\b|\b[a-z]+[A-Z][a-zA-Z0-9]*\b", chapter.text)
                for tm in tech_matches[:50]:
                    if tm.lower() not in stop_words:
                        topic_counts[tm] = topic_counts.get(tm, 0) + 1

        # Sort by frequency and preserve top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        # Select top unique normalized topics
        seen_normalized = set()
        final_topics = []
        for word, count in sorted_topics:
            norm = word.lower()
            if norm not in seen_normalized:
                seen_normalized.add(norm)
                final_topics.append(word)
            if len(final_topics) >= 15:
                break

        self.aggregated_topics = final_topics
        return self.aggregated_topics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "timestamp": self.timestamp,
            "sources": [s.to_dict() for s in self.sources],
            "aggregated_topics": self.aggregated_topics,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        return path

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UnifiedCorpus:
        corpus = cls(
            corpus_id=str(data.get("corpus_id", f"corpus_{uuid.uuid4().hex[:12]}")),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            sources=[IngestionSource.from_dict(s) for s in data.get("sources", [])],
            aggregated_topics=list(data.get("aggregated_topics", [])),
        )
        return corpus

    @classmethod
    def load(cls, file_path: str | Path) -> UnifiedCorpus:
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
