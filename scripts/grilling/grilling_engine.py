"""Interactive Grilling Protocol & Alignment Engine for thenuke skill.

Implements Milestone 2 (R2) requirements:
- Clarification interview across Level of Detail, Visual Frame Inclusion,
  Audience & Focus, and Target Language standards.
- Explicit visual frame clarification: 'images' specifically refers to
  captured video frames and slides.
- Strict relevance filter: filter_relevant_visual_frames evaluating OCR density,
  code presence, architecture diagram shapes vs talking-head/generic video frames.
- Profile persistence complying strictly with PROJECT.md § 4.2 schema.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants and Choice Enums
# ---------------------------------------------------------------------------

VALID_LEVELS_OF_DETAIL: Set[str] = {
    "foundations",
    "resource_parity",
    "senior_architect",
}

VALID_VISUAL_THRESHOLDS: Set[str] = {
    "strict_need_based",
    "balanced",
    "diagram_dense",
}

VALID_AUDIENCE_FOCUSES: Set[str] = {
    "production_engineering",
    "faang_interview",
    "academic_foundations",
}

LOCKED_TARGET_LANGUAGE: str = "roman_hinglish_zero_devanagari"

DEFAULT_DOMAIN_PRIORITIES: List[str] = [
    "event_loop",
    "v8_internals",
    "concurrency",
]

# Normalization mappings for user friendly input / CLI flags
LOD_MAPPINGS: Dict[str, str] = {
    "1": "foundations",
    "foundations": "foundations",
    "beginner": "foundations",
    "lod_beginner": "foundations",
    "2": "resource_parity",
    "parity": "resource_parity",
    "resource_parity": "resource_parity",
    "lod_parity": "resource_parity",
    "3": "senior_architect",
    "senior_architect": "senior_architect",
    "architect": "senior_architect",
    "lod_architect": "senior_architect",
}

VIT_MAPPINGS: Dict[str, str] = {
    "1": "strict_need_based",
    "strict": "strict_need_based",
    "strict_need_based": "strict_need_based",
    "need_based": "strict_need_based",
    "need-based": "strict_need_based",
    "vit_need_based": "strict_need_based",
    "2": "balanced",
    "balanced": "balanced",
    "vit_balanced": "balanced",
    "3": "diagram_dense",
    "dense": "diagram_dense",
    "diagram_dense": "diagram_dense",
    "vit_diagram_dense": "diagram_dense",
    # Boolean yes/no responses to image inclusion prompt
    "yes": "strict_need_based",
    "y": "strict_need_based",
    "no": "strict_need_based",
    "n": "strict_need_based",
}

FOCUS_MAPPINGS: Dict[str, str] = {
    "1": "production_engineering",
    "production": "production_engineering",
    "production_engineering": "production_engineering",
    "prod": "production_engineering",
    "aaf_production": "production_engineering",
    "2": "faang_interview",
    "interview": "faang_interview",
    "faang": "faang_interview",
    "faang_interview": "faang_interview",
    "aaf_interview": "faang_interview",
    "3": "academic_foundations",
    "academic": "academic_foundations",
    "academic_foundations": "academic_foundations",
    "theory": "academic_foundations",
    "aaf_academic": "academic_foundations",
}

# Regex to sanitize special characters in domain priorities
SANITIZE_PRIORITY_REGEX = re.compile(r"[;\"\'<>`#$\\]+")

# Code indicators for frame relevance scoring
CODE_SYNTAX_KEYWORDS = {
    "function", "const", "let", "var", "class", "return", "import", "export",
    "interface", "type", "async", "await", "promise", "def", "lambda", "console.log",
    "public", "private", "struct", "enum", "extends", "implements", "throw",
}

# Architecture diagram keywords
DIAGRAM_KEYWORDS = {
    "diagram", "architecture", "call stack", "memory", "heap", "pointer",
    "event loop", "microtask", "macrotask", "v8", "engine", "queue",
    "pipeline", "flowchart", "prototype", "scope chain", "table", "schema",
    "ast", "bytecode", "turbofan", "ignition", "gc", "garbage collection",
}

# Talking-head / low-relevance indicators
TALKING_HEAD_INDICATORS = {
    "talking_head", "talking head", "face", "webcam", "portrait", "presenter",
    "speaker", "intro", "outro", "sponsor", "camera", "headshot", "selfie",
}


# ---------------------------------------------------------------------------
# GrillingProfile Data Model
# ---------------------------------------------------------------------------

@dataclass
class GrillingProfile:
    """Represents the pedagogical and visual alignment profile for thenuke.

    Conforms strictly to PROJECT.md § 4.2 schema:
    {
      "level_of_detail": "foundations | resource_parity | senior_architect",
      "visual_inclusion_threshold": "strict_need_based | balanced | diagram_dense",
      "audience_focus": "production_engineering | faang_interview | academic_foundations",
      "target_language": "roman_hinglish_zero_devanagari",
      "domain_priorities": ["event_loop", "v8_internals", "concurrency"],
      "created_at": "ISO8601 string"
    }
    """
    level_of_detail: str = "senior_architect"
    visual_inclusion_threshold: str = "strict_need_based"
    audience_focus: str = "faang_interview"
    target_language: str = LOCKED_TARGET_LANGUAGE
    domain_priorities: List[str] = field(default_factory=lambda: list(DEFAULT_DOMAIN_PRIORITIES))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.normalize_and_validate()

    def normalize_and_validate(self) -> None:
        """Validates all fields and normalizes domain priorities."""
        # Normalize and validate level_of_detail
        normalized_lod = LOD_MAPPINGS.get(str(self.level_of_detail).lower().strip(), self.level_of_detail)
        if normalized_lod not in VALID_LEVELS_OF_DETAIL:
            raise ValueError(
                f"Invalid level_of_detail '{self.level_of_detail}'. "
                f"Must be one of: {sorted(VALID_LEVELS_OF_DETAIL)}"
            )
        self.level_of_detail = normalized_lod

        # Normalize and validate visual_inclusion_threshold
        normalized_vit = VIT_MAPPINGS.get(
            str(self.visual_inclusion_threshold).lower().strip(),
            self.visual_inclusion_threshold,
        )
        if normalized_vit not in VALID_VISUAL_THRESHOLDS:
            raise ValueError(
                f"Invalid visual_inclusion_threshold '{self.visual_inclusion_threshold}'. "
                f"Must be one of: {sorted(VALID_VISUAL_THRESHOLDS)}"
            )
        self.visual_inclusion_threshold = normalized_vit

        # Normalize and validate audience_focus
        normalized_focus = FOCUS_MAPPINGS.get(
            str(self.audience_focus).lower().strip(),
            self.audience_focus,
        )
        if normalized_focus not in VALID_AUDIENCE_FOCUSES:
            raise ValueError(
                f"Invalid audience_focus '{self.audience_focus}'. "
                f"Must be one of: {sorted(VALID_AUDIENCE_FOCUSES)}"
            )
        self.audience_focus = normalized_focus

        # Invariant: target_language is permanently locked
        self.target_language = LOCKED_TARGET_LANGUAGE

        # Sanitize and deduplicate domain priorities
        self.domain_priorities = sanitize_domain_priorities(self.domain_priorities)

        # Validate created_at or set if empty
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes to a dictionary conforming to PROJECT.md § 4.2."""
        return {
            "level_of_detail": self.level_of_detail,
            "visual_inclusion_threshold": self.visual_inclusion_threshold,
            "audience_focus": self.audience_focus,
            "target_language": self.target_language,
            "domain_priorities": list(self.domain_priorities),
            "created_at": self.created_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, output_path: Union[str, Path]) -> Path:
        """Persists profile to target JSON file."""
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))
        logger.info(f"Saved GrillingProfile to {path}")
        return path

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GrillingProfile:
        """Constructs and validates a GrillingProfile from a dictionary."""
        return cls(
            level_of_detail=data.get("level_of_detail", "senior_architect"),
            visual_inclusion_threshold=data.get("visual_inclusion_threshold", "strict_need_based"),
            audience_focus=data.get("audience_focus", "faang_interview"),
            target_language=data.get("target_language", LOCKED_TARGET_LANGUAGE),
            domain_priorities=data.get("domain_priorities", list(DEFAULT_DOMAIN_PRIORITIES)),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_json(cls, json_str: str) -> GrillingProfile:
        """Parses and validates a GrillingProfile from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: Union[str, Path]) -> GrillingProfile:
        """Loads a GrillingProfile from file."""
        target_path = Path(path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Grilling profile not found at: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Domain Priorities Sanitization
# ---------------------------------------------------------------------------

def sanitize_domain_priorities(
    raw_priorities: Optional[Sequence[str]],
    max_count: int = 20,
    default_priorities: Optional[List[str]] = None,
) -> List[str]:
    """Sanitizes, deduplicates, and caps user-provided domain priorities.

    - Strips shell injection / SQL injection characters (; " ' < > ` # $ \\).
    - Removes empty or whitespace-only tokens.
    - Preserves order while eliminating duplicates.
    - Caps to max_count (default 20).
    - Falls back to default_priorities if empty.
    """
    if default_priorities is None:
        default_priorities = list(DEFAULT_DOMAIN_PRIORITIES)

    if not raw_priorities:
        return list(default_priorities)

    cleaned_list: List[str] = []
    seen: Set[str] = set()

    for item in raw_priorities:
        if not isinstance(item, str):
            continue
        # Strip dangerous special characters
        cleaned = SANITIZE_PRIORITY_REGEX.sub("", item).strip()
        # Normalize internal whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)
        # Skip empty strings
        if not cleaned:
            continue
        # Case-preserving deduplication key
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            cleaned_list.append(cleaned)
            if len(cleaned_list) >= max_count:
                break

    if not cleaned_list:
        return list(default_priorities)

    return cleaned_list


# ---------------------------------------------------------------------------
# Strict Visual Relevance Filter
# ---------------------------------------------------------------------------

def calculate_frame_relevance_score(
    frame: Any,
    topic: Optional[str] = None,
) -> Tuple[float, Dict[str, Any]]:
    """Calculates a genuine heuristic relevance score for a visual frame.

    Evaluates:
    - Text/OCR density & length.
    - Source code syntax markers (function, const, let, return, class, etc.).
    - Architecture diagram keywords (heap, stack, event loop, queue, boxes).
    - Talking-head / presenter penalties (face, webcam, sponsor tags).
    - Topic token overlap if topic is provided.

    Returns:
        (composite_score, details_dict)
    """
    # Extract fields from dict, ExtractedImage, or generic object
    if isinstance(frame, dict):
        ocr_text = str(frame.get("ocr_text", "") or "")
        caption = str(frame.get("caption", "") or "")
        path = str(frame.get("path", "") or "")
        classification = str(frame.get("classification", "") or "").lower()
        has_code_flag = bool(frame.get("has_code", False))
        has_diagram_flag = bool(frame.get("has_diagram", False))
        is_slide_flag = bool(frame.get("is_slide", False))
        raw_entropy = frame.get("entropy", 0.0)
    elif frame is not None:
        ocr_text = str(getattr(frame, "ocr_text", "") or "")
        caption = str(getattr(frame, "caption", "") or "")
        path = str(getattr(frame, "path", "") or "")
        classification = str(getattr(frame, "classification", "") or "").lower()
        has_code_flag = bool(getattr(frame, "has_code", False))
        has_diagram_flag = bool(getattr(frame, "has_diagram", False))
        is_slide_flag = bool(getattr(frame, "is_slide", False))
        raw_entropy = getattr(frame, "entropy", 0.0)
    else:
        ocr_text = ""
        caption = ""
        path = ""
        classification = ""
        has_code_flag = False
        has_diagram_flag = False
        is_slide_flag = False
        raw_entropy = 0.0

    try:
        entropy = float(raw_entropy) if raw_entropy is not None else 0.0
    except (ValueError, TypeError):
        entropy = 0.0

    combined_text = f"{ocr_text} {caption}".lower()
    ocr_len = len(ocr_text.strip())

    # 1. OCR Density & Length Score (0.0 to 0.35)
    # Slides / code typically have > 40 chars of technical text
    if ocr_len >= 120:
        ocr_score = 0.35
    elif ocr_len >= 50:
        ocr_score = 0.25
    elif ocr_len >= 15:
        ocr_score = 0.12
    else:
        ocr_score = 0.0

    # 2. Code presence score (0.0 to 0.40)
    code_matches = sum(1 for kw in CODE_SYNTAX_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", combined_text))
    has_code_syntax = code_matches >= 2 or has_code_flag or ("=>" in ocr_text) or ("{" in ocr_text and "}" in ocr_text)
    if has_code_matches := code_matches:
        code_score = min(0.40, 0.15 + (has_code_matches * 0.05))
    elif has_code_syntax:
        code_score = 0.30
    else:
        code_score = 0.0

    # 3. Diagram / Architectural Shape Score (0.0 to 0.45)
    diagram_matches = sum(1 for kw in DIAGRAM_KEYWORDS if kw in combined_text)
    is_genuine_diagram = (
        has_diagram_flag
        or any(k in classification for k in ("diagram", "architecture", "flowchart", "code_whiteboard", "whiteboard"))
    )

    if is_genuine_diagram:
        diagram_score = 0.45
    elif is_slide_flag or "slide" in classification or "slide" in path.lower():
        # Text-only bullet slides without diagrams do not receive full diagram score
        diagram_score = min(0.04, diagram_matches * 0.02)
    elif diagram_matches >= 2:
        diagram_score = 0.35
    elif diagram_matches == 1:
        diagram_score = 0.20
    else:
        diagram_score = 0.0

    # Slide structure bonus
    slide_bonus = 0.15 if is_slide_flag or "slide" in classification or "slide" in path.lower() else 0.0

    # 4. Talking head / Generic frame penalty
    is_talking_head = False
    caption_lower = caption.lower()
    path_lower = path.lower()
    caption_words = caption_lower.replace("_", " ")
    class_words = classification.replace("_", " ")
    path_words = re.sub(r"[_\-./\\]", " ", path_lower)

    def has_th_indicator(text: str) -> bool:
        return any(bool(re.search(rf"\b{re.escape(ind)}\b", text)) for ind in TALKING_HEAD_INDICATORS)

    if (
        has_th_indicator(caption_lower)
        or has_th_indicator(caption_words)
        or has_th_indicator(classification)
        or has_th_indicator(class_words)
    ):
        is_talking_head = True
    elif "talking_head" in path_lower or "talking head" in path_words or bool(re.search(r"\bface\b", path_words)):
        is_talking_head = True
    elif ocr_len < 10 and not has_code_syntax and not has_diagram_flag and not is_slide_flag:
        # Near-zero text and no explicit diagram/slide flag
        is_talking_head = True

    talking_head_penalty = -0.75 if is_talking_head else 0.0

    # 5. Topic relevance boost (0.0 to 0.25)
    topic_boost = 0.0
    if topic:
        topic_tokens = set(re.findall(r"[a-zA-Z0-9]+", topic.lower().replace("_", " ")))
        if topic_tokens:
            matches = sum(1 for token in topic_tokens if len(token) > 2 and token in combined_text)
            if matches > 0:
                topic_boost = min(0.25, 0.10 * matches)

    # Composite score calculation
    raw_score = ocr_score + code_score + diagram_score + slide_bonus + topic_boost + talking_head_penalty
    composite_score = max(0.0, min(1.0, raw_score))

    details = {
        "ocr_len": ocr_len,
        "ocr_score": round(ocr_score, 3),
        "code_score": round(code_score, 3),
        "diagram_score": round(diagram_score, 3),
        "slide_bonus": round(slide_bonus, 3),
        "topic_boost": round(topic_boost, 3),
        "is_talking_head": is_talking_head,
        "composite_score": round(composite_score, 3),
    }

    return composite_score, details


def filter_relevant_visual_frames(
    candidate_frames: Sequence[Any],
    topic: Optional[str] = None,
    threshold_mode: str = "strict_need_based",
) -> List[Any]:
    """Filters visual video frames and slides based on strict pedagogical need.

    Enforces the User Specification:
    - 'Images' specifically refers to captured video frames and presentation slides.
    - Strict need-based filter: include ONLY those frames where a concept is
      fundamentally better explained visually (diagrams, architecture charts,
      code diffs, high-information slide frames); otherwise explain via text.
    - Rejects talking-head frames, generic video frames, low-content cards,
      and irrelevant visuals.

    Threshold modes:
    - 'strict_need_based': Highest threshold (score >= 0.55). Discards talking
      heads, generic frames, and simple text slides that can be conveyed in prose.
    - 'balanced': Moderate threshold (score >= 0.30). Retains code snippets,
      diagrams, and informative slides.
    - 'diagram_dense': Permissive threshold (score >= 0.15). Retains most visual
      slides and diagrams while still discarding talking-head/empty frames.

    Args:
        candidate_frames: List of dicts or ExtractedImage objects.
        topic: Optional domain topic string for relevance alignment.
        threshold_mode: One of 'strict_need_based', 'balanced', 'diagram_dense'.

    Returns:
        Filtered list of frames maintaining the original object types.
    """
    normalized_mode = VIT_MAPPINGS.get(str(threshold_mode).lower().strip(), threshold_mode)
    if normalized_mode not in VALID_VISUAL_THRESHOLDS:
        raise ValueError(
            f"Invalid threshold_mode '{threshold_mode}'. "
            f"Must be one of: {sorted(VALID_VISUAL_THRESHOLDS)}"
        )

    # Establish score thresholds per mode
    if normalized_mode == "strict_need_based":
        cutoff = 0.55
    elif normalized_mode == "balanced":
        cutoff = 0.30
    else:  # diagram_dense
        cutoff = 0.15

    filtered_frames: List[Any] = []

    for frame in candidate_frames:
        score, details = calculate_frame_relevance_score(frame, topic=topic)
        # Talking heads are strictly rejected in all modes unless explicitly overridden
        if details["is_talking_head"] and score < 0.60:
            continue

        if score >= cutoff:
            filtered_frames.append(frame)

    return filtered_frames


# ---------------------------------------------------------------------------
# Grilling Engine & Interactive Questionnaire
# ---------------------------------------------------------------------------

class GrillingEngine:
    """Orchestrates the user alignment interview and configuration builder."""

    def __init__(
        self,
        default_lod: str = "senior_architect",
        default_vit: str = "strict_need_based",
        default_focus: str = "faang_interview",
        default_priorities: Optional[List[str]] = None,
        input_fn: Optional[Callable[[str], str]] = None,
        print_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.default_lod = default_lod
        self.default_vit = default_vit
        self.default_focus = default_focus
        self.default_priorities = default_priorities or list(DEFAULT_DOMAIN_PRIORITIES)
        self.input_fn = input_fn or input
        self.print_fn = print_fn or print

    def build_profile(
        self,
        level_of_detail: Optional[str] = None,
        visual_inclusion_threshold: Optional[str] = None,
        audience_focus: Optional[str] = None,
        domain_priorities: Optional[Sequence[str]] = None,
        created_at: Optional[str] = None,
    ) -> GrillingProfile:
        """Programmatically builds and validates a GrillingProfile."""
        lod = level_of_detail or self.default_lod
        vit = visual_inclusion_threshold or self.default_vit
        focus = audience_focus or self.default_focus
        priorities = domain_priorities if domain_priorities is not None else self.default_priorities

        profile = GrillingProfile(
            level_of_detail=lod,
            visual_inclusion_threshold=vit,
            audience_focus=focus,
            target_language=LOCKED_TARGET_LANGUAGE,
            domain_priorities=list(priorities),
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
        )
        return profile

    def conduct_interview(
        self,
        corpus_topics: Optional[List[str]] = None,
        non_interactive: bool = False,
    ) -> GrillingProfile:
        """Executes the interactive clarification interview.

        Queries:
        1. Level of Detail.
        2. Visual Inclusion Threshold (with explicit clarification on captured
           video frames and slides).
        3. Audience & Focus.
        4. Target Language (displayed as locked).
        5. Domain Priorities (with detected corpus topics suggested).
        """
        if non_interactive or not self._is_stdin_interactive():
            logger.info("Non-interactive mode or non-TTY stdin: Using defaults.")
            suggested_priorities = corpus_topics or self.default_priorities
            return self.build_profile(
                level_of_detail=self.default_lod,
                visual_inclusion_threshold=self.default_vit,
                audience_focus=self.default_focus,
                domain_priorities=suggested_priorities,
            )

        self._print_banner()

        # Step 1: Level of Detail
        lod = self._prompt_level_of_detail()

        # Step 2: Visual Inclusion Threshold with mandatory clarification
        vit = self._prompt_visual_threshold()

        # Step 3: Audience & Focus
        focus = self._prompt_audience_focus()

        # Step 4: Language notice
        self.print_fn("\n[Dimension 4] Language & Standards:")
        self.print_fn(
            "  * Target Language: roman_hinglish_zero_devanagari (LOCKED)\n"
            "  * 100% Roman-alphabet Hinglish with 0 Devanagari characters.\n"
            "  * Spoken Hinglish cadence combined with formal English technical keywords."
        )

        # Step 5: Domain priorities
        priorities = self._prompt_domain_priorities(corpus_topics=corpus_topics)

        profile = self.build_profile(
            level_of_detail=lod,
            visual_inclusion_threshold=vit,
            audience_focus=focus,
            domain_priorities=priorities,
        )

        self.print_fn("\n" + "=" * 72)
        self.print_fn("[✓] Interactive Grilling Profile Alignment Confirmed!")
        self.print_fn(f"    - Level of Detail: {profile.level_of_detail}")
        self.print_fn(f"    - Visual Threshold: {profile.visual_inclusion_threshold}")
        self.print_fn(f"    - Audience & Focus: {profile.audience_focus}")
        self.print_fn(f"    - Domain Priorities: {', '.join(profile.domain_priorities)}")
        self.print_fn("=" * 72 + "\n")

        return profile

    def _is_stdin_interactive(self) -> bool:
        """Determines if current stdin is an interactive TTY."""
        if self.input_fn is not input:
            return True
        try:
            return sys.stdin.isatty()
        except Exception:
            return False

    def _print_banner(self) -> None:
        banner = (
            "\n"
            "╔══════════════════════════════════════════════════════════════════════════╗\n"
            "║               THENUKE — INTERACTIVE GRILLING PROTOCOL                     ║\n"
            "║           Pedagogical & Structural Alignment Engine                      ║\n"
            "╚══════════════════════════════════════════════════════════════════════════╝\n"
        )
        self.print_fn(banner)

    def _prompt_level_of_detail(self) -> str:
        self.print_fn("[Dimension 1 of 4] Select Level of Detail:")
        self.print_fn("  [1] Complete Beginner Foundations (Analogies, zero-prerequisite pacing)")
        self.print_fn("  [2] Resource-Matched Parity (1:1 depth matching source videos/docs)")
        self.print_fn("  [3] Autonomous Senior-Architect Depth (V8 internals, invariants, Staff+) [Default]")
        
        while True:
            try:
                choice = self.input_fn("Enter selection [1-3] (Press Enter for default [3]): ").strip()
            except (EOFError, KeyboardInterrupt):
                return self.default_lod

            if not choice:
                return "senior_architect"
            if choice in LOD_MAPPINGS:
                return LOD_MAPPINGS[choice]
            if choice.lower() in VALID_LEVELS_OF_DETAIL:
                return choice.lower()
            self.print_fn("  [!] Invalid choice. Please enter 1, 2, or 3.")

    def _prompt_visual_threshold(self) -> str:
        # Mandatory user clarification message:
        self.print_fn("\n" + "-" * 72)
        self.print_fn("[Dimension 2 of 4] Visual Frame Inclusion Threshold")
        self.print_fn("CLARIFICATION: In 'thenuke', 'images' specifically refers to captured")
        self.print_fn("video frames and presentation slides extracted from the input resources.")
        self.print_fn("-" * 72)
        self.print_fn("Do you want the documentation to include images (captured video frames and slides)?")
        self.print_fn("  [1] Strict Need-Based (Include ONLY where a concept is fundamentally")
        self.print_fn("      better explained visually; otherwise explain via text) [Default]")
        self.print_fn("  [2] Balanced (Include architectural diagrams & key slide frames)")
        self.print_fn("  [3] Diagram-Dense (Include high density of visual frames across all sections)")

        while True:
            try:
                choice = self.input_fn("Enter selection [1-3] (Press Enter for default [1]): ").strip()
            except (EOFError, KeyboardInterrupt):
                return self.default_vit

            if not choice:
                return "strict_need_based"
            if choice in VIT_MAPPINGS:
                return VIT_MAPPINGS[choice]
            if choice.lower() in VALID_VISUAL_THRESHOLDS:
                return choice.lower()
            self.print_fn("  [!] Invalid choice. Please enter 1, 2, or 3.")

    def _prompt_audience_focus(self) -> str:
        self.print_fn("\n[Dimension 3 of 4] Select Target Audience & Pedagogical Focus:")
        self.print_fn("  [1] Production Enterprise Engineering (ES2024+, Zero-dependency resilience)")
        self.print_fn("  [2] FAANG / High-Stakes Coding Interview & Machine Coding [Default]")
        self.print_fn("  [3] Academic / Theoretical Foundations (Syllabus proofs & mastery)")

        while True:
            try:
                choice = self.input_fn("Enter selection [1-3] (Press Enter for default [2]): ").strip()
            except (EOFError, KeyboardInterrupt):
                return self.default_focus

            if not choice:
                return "faang_interview"
            if choice in FOCUS_MAPPINGS:
                return FOCUS_MAPPINGS[choice]
            if choice.lower() in VALID_AUDIENCE_FOCUSES:
                return choice.lower()
            self.print_fn("  [!] Invalid choice. Please enter 1, 2, or 3.")

    def _prompt_domain_priorities(self, corpus_topics: Optional[List[str]] = None) -> List[str]:
        suggested = corpus_topics or self.default_priorities
        display_suggested = ", ".join(suggested)
        self.print_fn(f"\n[Domain Priorities] Focus Topics (Detected / Default: {display_suggested}):")
        
        try:
            val = self.input_fn("Enter priority topics separated by commas (Press Enter for defaults): ").strip()
        except (EOFError, KeyboardInterrupt):
            return suggested

        if not val:
            return suggested

        raw_parts = [p.strip() for p in val.split(",") if p.strip()]
        sanitized = sanitize_domain_priorities(raw_parts, default_priorities=suggested)
        return sanitized


# ---------------------------------------------------------------------------
# Convenience Runner Function
# ---------------------------------------------------------------------------

def run_grilling_interview(
    corpus: Optional[Any] = None,
    output_path: Optional[Union[str, Path]] = "grilling_profile.json",
    interactive: bool = True,
    level_of_detail: Optional[str] = None,
    visual_inclusion_threshold: Optional[str] = None,
    audience_focus: Optional[str] = None,
    domain_priorities: Optional[Sequence[str]] = None,
    input_fn: Optional[Callable[[str], str]] = None,
    print_fn: Optional[Callable[[str], None]] = None,
) -> GrillingProfile:
    """Conducts or builds a grilling interview and optionally persists profile.

    Args:
        corpus: Optional corpus dict, path, or UnifiedCorpus object to extract topics.
        output_path: Path to write grilling_profile.json (or None to skip disk write).
        interactive: If True and stdin is a TTY, launches interactive prompts.
        level_of_detail: Programmatic override for LOD.
        visual_inclusion_threshold: Programmatic override for visual threshold.
        audience_focus: Programmatic override for audience focus.
        domain_priorities: Programmatic override for domain priorities.
        input_fn: Optional input callable for testing or GUI piping.
        print_fn: Optional print callable.

    Returns:
        Validated GrillingProfile instance.
    """
    engine = GrillingEngine(input_fn=input_fn, print_fn=print_fn)

    # Extract corpus topics if available
    corpus_topics: List[str] = []
    if corpus is not None:
        if isinstance(corpus, (str, Path)):
            cpath = Path(corpus)
            if cpath.exists():
                try:
                    with open(cpath, "r", encoding="utf-8") as f:
                        cdata = json.load(f)
                    corpus_topics = cdata.get("aggregated_topics", []) or cdata.get("summary", {}).get("detected_topics", [])
                except Exception as e:
                    logger.warning(f"Could not read corpus file {corpus}: {e}")
        elif isinstance(corpus, dict):
            corpus_topics = corpus.get("aggregated_topics", []) or corpus.get("summary", {}).get("detected_topics", [])
        elif hasattr(corpus, "aggregated_topics"):
            corpus_topics = getattr(corpus, "aggregated_topics", [])

    if interactive and (input_fn is not None or engine._is_stdin_interactive()):
        profile = engine.conduct_interview(
            corpus_topics=corpus_topics,
            non_interactive=False,
        )
        # Apply any explicit overrides if supplied
        if level_of_detail:
            profile.level_of_detail = level_of_detail
        if visual_inclusion_threshold:
            profile.visual_inclusion_threshold = visual_inclusion_threshold
        if audience_focus:
            profile.audience_focus = audience_focus
        if domain_priorities:
            profile.domain_priorities = sanitize_domain_priorities(domain_priorities)
        profile.normalize_and_validate()
    else:
        priorities = domain_priorities or corpus_topics or engine.default_priorities
        profile = engine.build_profile(
            level_of_detail=level_of_detail,
            visual_inclusion_threshold=visual_inclusion_threshold,
            audience_focus=audience_focus,
            domain_priorities=priorities,
        )

    if output_path is not None:
        profile.save(output_path)

    return profile


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="thenuke Interactive Grilling Protocol & Alignment Engine")
    parser.add_argument("--corpus", type=str, default=None, help="Path to nuke_ingestion_corpus.json")
    parser.add_argument("--output", type=str, default="grilling_profile.json", help="Path to save grilling_profile.json")
    parser.add_argument("--non-interactive", action="store_true", help="Run without interactive prompts")
    parser.add_argument("--lod", type=str, default=None, choices=list(VALID_LEVELS_OF_DETAIL), help="Level of Detail")
    parser.add_argument("--vit", type=str, default=None, choices=list(VALID_VISUAL_THRESHOLDS), help="Visual Inclusion Threshold")
    parser.add_argument("--focus", type=str, default=None, choices=list(VALID_AUDIENCE_FOCUSES), help="Audience Focus")
    parser.add_argument("--priorities", nargs="*", default=None, help="Domain priorities")

    args = parser.parse_args()

    prof = run_grilling_interview(
        corpus=args.corpus,
        output_path=args.output,
        interactive=not args.non_interactive,
        level_of_detail=args.lod,
        visual_inclusion_threshold=args.vit,
        audience_focus=args.focus,
        domain_priorities=args.priorities,
    )
    print(f"Alignment Profile successfully generated:\n{prof.to_json(indent=2)}")
