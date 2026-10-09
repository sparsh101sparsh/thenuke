<div align="center">

# ☢️ thenuke
### Multi-Agent Documentation Engine & Reference Manual Synthesizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Antigravity](https://img.shields.io/badge/Antigravity-Compatible-8A2BE2.svg?style=for-the-badge)](https://github.com/sparsh101sparsh/skills)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-453%20Passing%20(100%25)-00C853?style=for-the-badge)](#-test-architecture)
[![Style](https://img.shields.io/badge/Language-100%25%20Roman%20Hinglish-FF6F00?style=for-the-badge)](#-linguistic-system--style-invariants)

**Transform multi-modal learning resources into high-density, production-grade engineering reference manuals.**  
100% Roman-alphabet Hinglish (zero Devanagari script) • Minimalist Monochrome Design • PyMuPDF Vector Diagrams • Built for Google Antigravity

*Authored by [@issparsh](https://x.com/issparsh) & [@sumitsingh097](https://x.com/sumitsingh097)*

</div>

---

## ⚡ Executive Summary

**thenuke** is an automated multi-agent documentation engine packaged as an Antigravity skill. It ingests heterogeneous multi-modal learning resources (YouTube playlists/videos via `yt-dlp` at 720p, web documentation crawlers, local PDFs, PPT/PPTX slide decks, local video recordings, and screenshots) and synthesizes enterprise-grade engineering reference manuals.

All manuals are rendered in **100% Roman-alphabet Hinglish (zero Devanagari script)** with dual-register cadence: natural spoken Hinglish narrative combined with 100% formal English technical keywords, CS architecture diagrams drawn via PyMuPDF vector primitives, and end-of-phase 3-part FAANG drills.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/sparsh101sparsh/thenuke.git
cd thenuke

# Install Python dependencies
pip install -r requirements.txt

# System requirements (macOS / Linux)
brew install ffmpeg yt-dlp
```

### 2. Antigravity Skill Registration

Install directly to your global Antigravity skills directory:

```bash
mkdir -p ~/.gemini/config/skills/thenuke
cp -r scripts tests thenuke_cli.py SKILL.md requirements.txt ~/.gemini/config/skills/thenuke/
```

### 3. Running the Pipeline

```bash
# End-to-End: Ingest → Grill → Synthesize → Compile PDF → QA Audit → Post-Clearance Cleanup
python thenuke_cli.py run \
  "https://www.youtube.com/playlist?list=PLlasXeu85E9cQ32gLCvAvr9vNaUccPVNP" \
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide" \
  "/path/to/local_notes.pdf"

# Non-interactive CI execution with preset
python thenuke_cli.py run --non-interactive --preset senior_architect_faang \
  "https://youtu.be/dQw4w9WgXcQ"
```

---

## 🏗️ 6-Stage Pipeline Architecture

```
[Multi-Modal Inputs]
   ├── YouTube Videos / Playlists      → yt-dlp (720p) + faster-whisper (large-v3-turbo)
   ├── Web Documentation & Repositories → Requests / Headless Chrome DOM dump + screenshots
   └── Local Documents & Media         → PyMuPDF (PDF) + python-pptx (PPTX) + OCR
              │
              ▼
[Stage 1: Multi-Source Ingestion Engine (`scripts/ingestion/`)]
   ├── `unified_corpus.py`: Source normalization & JSON serialization
   ├── `yt_ingest.py`: 720p enforcement, rolling VTT deduplication, dynamic frame sampling
   ├── `web_crawler.py`: Semantic markdown extraction, pre/code protection
   └── `file_extract.py`: Multi-format local document extraction
              │
              ▼
[Stage 2: Interactive Grilling Protocol (`scripts/grilling/`)]
   └── `grilling_engine.py`: Scope alignment & visual thresholding interview
       • Level of Detail: foundations | resource_parity | senior_architect
       • Visual Threshold: strict_need_based | balanced | diagram_dense
       • Audience Focus: faang_interview | production_engineering | academic
              │
              ▼
[Stage 3: Reference Manual Synthesis Engine (`scripts/synthesis/`)]
   └── `manual_synthesizer.py`:
       • 100% Roman-alphabet Hinglish (zero Devanagari Unicode characters)
       • Detailed Syllabus Index: PART I to VI
       • 9-Phase modular blueprint with deep-dive appendices
       • Bracketed invariant callouts: [MENTAL MODEL], [ENGINEERING GOTCHA]
       • 3-part Phase Challenges (Output Prediction, Algorithm, Mini-Project)
       • ES2024+ native standards, zero npm dependencies, anti-toy-code policy
              │
              ▼
[Stage 4: Vector Diagramming & Branding Engine (`scripts/diagramming/`)]
   └── `vector_engine.py`:
       • PyMuPDF vector drawing (Call Stack, Heap Graph, Event Loop Pipeline)
       • Minimalist High-Contrast Monochrome aesthetic (#000000, #222222, #CCCCCC, #F8F8F8)
       • Official 𝕏 Vector Glyph + "Prepared by @issparsh @sumitsingh097"
              │
              ▼
[Stage 5: Dual-Pass Visual QA & Quality Audit Loop (`scripts/qa/`)]
   └── `qa_audit_engine.py`:
       • Pass 1: Visual & Structural QA (rasterization, text overflow, orphan headers)
       • Pass 2: Textual QA (zero-Devanagari regex assertion, syllabus index check)
              │
              ▼
[Stage 6: Post-Clearance Automated Data Cleanup (`thenuke_cli.py clean`)]
   └── Purges intermediate 720p videos, extracted frames, audio WAVs, and scraper caches
```

---

## 📐 Linguistic System & Style Invariants

| Dimension | Rule | Example / Specification |
|---|---|---|
| **Script Rule** | **100% Latin / Roman English alphabet ONLY** | `NEVER` write Devanagari (`देवनागरी`, `है`, `करो`). Verified via programmatic regex assertions. |
| **Conversational Register** | Spoken, fast-paced senior engineer Roman Hinglish | *"Technically bolo toh..."*, *"Sabse pehle ye samajhna zaroori hai ki..."*, *"Gotcha ye hai ki..."* |
| **Technical Register** | 100% formal English technical terminology | `Call Stack`, `Memory Heap`, `Lexical Environment Record`, `Temporal Dead Zone`, `TurboFan JIT` |
| **Code Standard** | Modern ES2024+ native APIs | `Object.groupBy`, `Promise.withResolvers`, `Array.prototype.toSorted`, new `Set` methods |
| **Dependency Rule** | Zero npm dependencies | 100% native standard APIs, zero third-party runtime imports |
| **Anti-Toy Code** | Production schema entities | Strict ban on `foo`, `bar`, `test`; authentic enterprise entities only |

---

## 🎨 Visual Identity & Typographic Palette

Designed for high-density academic ISO A4 reading:

```
Titles & Headers : Pure Black (#000000)
Body Prose       : Deep Charcoal (#222222)
Secondary Notes  : Slate Grey (#444444)
Dividing Rules   : Hairline Grey (#CCCCCC, 0.5pt)
Callout Fill     : Soft Light Grey (#F1F5F9)
Code Background  : Tinted Off-White (#F8F8F8)
Branding Line    : Prepared by @issparsh @sumitsingh097 𝕏
```

---

## 🧪 Test Architecture

The repository enforces a comprehensive **453-test test suite** passing at **100% success rate**:

```bash
# Run full suite
pytest tests/ -v

# Run targeted milestone suites
pytest tests/test_ingestion.py tests/test_ingestion_user_specs.py
pytest tests/test_grilling.py tests/test_challenger_m2_stress.py
pytest tests/test_synthesis.py
pytest tests/test_diagramming_and_qa.py
```

| Milestone | Test Suite File | Tests | Coverage Scope |
|---|---|---|---|
| **M1: Ingestion** | `test_ingestion.py`, `test_ingestion_user_specs.py`, `test_challenger_m1_*.py` | 270 | 720p downloads, rolling VTT deduplication, faster-whisper fallback, HTML DOM parsing |
| **M2: Grilling** | `test_grilling.py`, `test_challenger_m2_stress.py` | 71 | Clarification interview, relevance heuristics, word-boundary regex filtering |
| **M3: Synthesis** | `test_synthesis.py` | 40 | Zero Devanagari enforcement, 9-phase syllabus index, 3-part Phase Challenges, ES2024+ signals |
| **M4 & M5: Vector & QA** | `test_diagramming_and_qa.py` | 72 | Monochrome palette, markdown parser, vector diagrams, dual-pass QA audit |
| **Total** | **All 4 Tiers & Adversarial Suites** | **453** | **100% Pass Rate** |

---

## 🧹 Post-Clearance Data Cleanup

Large-scale video ingestion generates gigabytes of intermediate artifacts. Once user clearance is granted on the compiled PDF, run:

```bash
python thenuke_cli.py clean
```

This permanently purges:
- `~/thenuke_workspace/scratch/videos/` (downloaded 720p MP4 files)
- `~/thenuke_workspace/scratch/frames/` (extracted scene frames)
- `~/thenuke_workspace/scratch/audio/` (demuxed WAV/MP3 files)
- `~/thenuke_workspace/scratch/scrape_html/` (raw DOM scrapes)

---

## 👥 Authors & Attribution

- **Sparsh** ([@issparsh](https://x.com/issparsh))
- **Sumit Singh** ([@sumitsingh097](https://x.com/sumitsingh097))

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.
