---
name: thenuke
description: >
  thenuke is a multi-agent documentation engine that ingests multi-modal learning
  resources (YouTube videos/playlists, web documentation, local PDFs/PPTs/videos/screenshots)
  and synthesizes high-density engineering reference manuals in 100% Roman-alphabet Hinglish
  (zero Devanagari characters) with PyMuPDF vector diagrams, monochrome aesthetic, and
  mandatory author branding (@issparsh @sumitsingh097 with the official X/Twitter glyph).
version: 2.0.0
authors:
  - "@issparsh"
  - "@sumitsingh097"
tags:
  - documentation
  - pdf
  - reference-manual
  - roman-hinglish
  - multi-agent
  - vector-diagrams
  - reportlab
  - youtube-ingestion
  - web-crawler
  - pymupdf
---

# thenuke — Multi-Modal Documentation Engine

> Koi bhi resource lo — YouTube playlist, web docs, local PDF — aur ek production-grade
> engineering reference manual banao in Roman Hinglish. Zero Devanagari characters. Always.

## Quick Start

```bash
# 🚀 Multi-Agent Autonomous Pipeline (Recommended):
# Coordinates Architect, Researcher, Writer, Diagrammer, and Reviewer agents
python thenuke_cli.py multi-agent --topic Git --output ~/Downloads/Git_Complete_Reference_Manual.pdf

# Interactive /grill-me Clarification Interview Mode:
python thenuke_cli.py multi-agent --topic Git --interactive

# Full Ingestion + Multi-Agent Pipeline:
python thenuke_cli.py run \
  "https://www.youtube.com/playlist?list=PLlasXeu85E9cQ32gLCvAvr9vNaUccPVNP" \
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide" \
  "/Users/yourname/Downloads/JS_Notes.pdf"

# Individual stages
python thenuke_cli.py ingest "https://youtube.com/..."
python thenuke_cli.py grill --preset senior_architect_faang
python thenuke_cli.py synthesize
python thenuke_cli.py compile output/thenuke_manual_*.md
python thenuke_cli.py qa output/thenuke_manual_*.pdf --report output/qa_report.json
python thenuke_cli.py clean
```

## Pipeline Stages

| Stage | Subsystem | Description |
|-------|-----------|-------------|
| **1. Ingest** | `scripts/ingestion/` | Multi-source crawler: YouTube (yt-dlp, faster-whisper), web, local files |
| **2. Grill** | `scripts/grilling/` | Interactive user interview (`/grill-me`): depth, visual threshold, focus |
| **3. Multi-Agent System** | `scripts/multi_agent/` | Autonomous team: Architect, Researcher, Writer, Diagrammer, Reviewer |
| **4. Vector Engine** | `scripts/diagramming/` | Native ReportLab `Drawing` vector diagrams (DAGs, 3-Trees, LCA merges) |
| **5. PDF Compiler** | `reportlab_engine.py` | Publication-grade ISO A4 layout matching standard engineering manuals |
| **6. 4-Pass QA Gate** | `scripts/qa/` + Reviewer | Automated layout, 0% Devanagari, diagram density, and drill audits |
| **7. Cleanup** | `thenuke_cli.py clean` | Post-clearance wipe of scratch frames, audio, and HTML |

## Pipeline Architecture

```
[Multi-Modal Sources]
   ├── YouTube URLs (video/playlist)   → yt-dlp + faster-whisper large-v3-turbo
   ├── Web URLs / GitHub Repos         → requests/headless Chrome + Markdown extraction
   └── Local Files (PDF/PPTX/MP4/PNG)  → PyMuPDF + python-pptx + ffmpeg
              │
              ▼
[R1: Ingestion Engine]  →  nuke_ingestion_corpus.json
              │
              ▼
[R2: Grilling Protocol] →  grilling_profile.json
  • Level of Detail: foundations | resource_parity | senior_architect
  • Visual Threshold: strict_need_based | balanced | diagram_dense
  • Audience Focus: faang_interview | production_engineering | academic
              │
              ▼
[R3: Synthesis Engine]  →  thenuke_manual_*.md
  • 100% Roman Hinglish (zero Devanagari)
  • Multi-part Syllabus Index (PART I–VI)
  • 9-Phase blueprint + Appendices
  • [MENTAL MODEL] / [ENGINEERING GOTCHA] / [INTERVIEW TIP] callouts
  • 3-Part Phase Challenges (Output Prediction, Algorithm, Mini-Project)
  • ES2024+ code, zero npm deps, anti-toy-code policy
              │
              ▼
[R4: Vector & Branding] →  thenuke_manual_*.pdf
  • PyMuPDF vector shapes: Call Stack, Heap, Event Loop, Prototype Chain
  • Monochrome palette: #000000 / #222222 / #CCCCCC / #F8F8F8
  • Official X/Twitter vector glyph + "Prepared by @issparsh @sumitsingh097"
  • ISO A4, Helvetica body, Courier code, running headers & footers
              │
              ▼
[R5: QA Audit]  →  qa_report.json
  • Pass 1 Visual: text overflow, orphan headers, margin violations
  • Pass 2 Textual: zero Devanagari, syllabus index, branding, ES2024+ signals
              │
              ▼
[R6: Cleanup]
  • Auto-wipe: downloaded videos, extracted frames, WAV audio, raw HTML
```

## Style Invariants (Non-Negotiable)

### Language
- **ZERO Devanagari** — every word in Roman/Latin alphabet (`a-z, A-Z`). Enforced at synthesis and QA.
- **Dual-Register Cadence:**
  - Narrative: spoken Hinglish bridges — `"Technically bolo toh..."`, `"Sabse pehle..."`, `"Gotcha ye hai ki..."`
  - Technical: 100% formal English — `Call Stack`, `Memory Heap`, `Lexical Environment Record`, `TurboFan JIT`
- **Challenge prompts:** 100% formal FAANG-style English.

### Code Policy
- Modern **ES2024+** — `Object.groupBy`, `Promise.withResolvers`, `Array.prototype.toSorted`, new `Set` methods.
- **Zero npm dependencies** — native runtime APIs only.
- **Anti-toy-code** — no `foo`, `bar`, `test123` identifiers. Real enterprise domain names.
- **Inline output comments** on every evaluatable expression.

### Typography (ISO A4)
| Element | Font | Size | Color |
|---------|------|------|-------|
| Document Title | Helvetica Bold | 14–15 pt | #000000 |
| Phase Header | Helvetica Bold | 13–13.5 pt | #000000 |
| Chapter Title | Helvetica Bold | 11–12 pt | #000000 |
| Section/Callout | Helvetica Bold | 9.5–10 pt | #000000 |
| Body Text | Helvetica Regular | 8.5 pt / 11.5 pt leading | #222222 |
| Code | Courier | 7.5 pt / 9.5 pt leading | #444444 |

## Grilling Presets

| Preset | Level | Visual | Audience |
|--------|-------|--------|----------|
| `foundations` | foundations | strict_need_based | academic_foundations |
| `resource_parity` | resource_parity | balanced | production_engineering |
| `senior_architect_faang` | senior_architect | strict_need_based | faang_interview |

## Environment Requirements

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | 3.14 tested on Apple M4 |
| PyMuPDF | 1.24+ | `pip install pymupdf` |
| faster-whisper | 1.2.1+ | `pip install faster-whisper` |
| ffmpeg | 7.0+ | `/opt/homebrew/bin/ffmpeg` |
| yt-dlp | latest | `pip install yt-dlp` |
| lxml | 5.x | HTML DOM parsing |

## Running Tests

```bash
cd ~/teamwork_projects/thenuke_skill
python3 -m pytest tests/ -q
```

**Expected:** All tests passing at 100% success rate.

Test architecture:
- `tests/test_ingestion.py` — M1: ingestion engine unit + integration tests
- `tests/test_ingestion_user_specs.py` — M1: 720p, dynamic frames, faster-whisper specs
- `tests/test_challenger_m1_1_empirical.py` — M1: adversarial boundary defects
- `tests/test_challenger_m1_stress.py` — M1: stress & pairwise combinations
- `tests/test_challenger_m1_iter2_specs.py` — M1 iter2: user spec validation
- `tests/test_grilling.py` — M2: grilling protocol unit + integration
- `tests/test_challenger_m2_stress.py` — M2: adversarial boundary stress
- `tests/test_synthesis.py` — M3: synthesis engine (zero Devanagari, challenges, callouts)
- `tests/test_diagramming_and_qa.py` — M4+M5: vector engine palette, MD parser, QA audit

## Branding

All generated PDFs are branded:
```
Prepared by @issparsh @sumitsingh097  𝕏
```
with the official Twitter/X vector glyph on the cover page and in each page footer.

## Post-Clearance Cleanup

Once you approve the final PDF, run:
```bash
python thenuke_cli.py clean
```
This permanently deletes all intermediate artifacts:
- `~/thenuke_workspace/scratch/videos/` — downloaded 720p MP4 files
- `~/thenuke_workspace/scratch/frames/` — extracted video frames  
- `~/thenuke_workspace/scratch/audio/` — demuxed WAV files
- `~/thenuke_workspace/scratch/scrape_html/` — raw scraped HTML pages

> [!CAUTION]
> Cleanup is irreversible. Confirm you are satisfied with the final PDF before running.
