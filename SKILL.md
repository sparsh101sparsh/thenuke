---
name: thenuke
description: >
  thenuke is a multi-agent documentation engine that ingests multi-modal learning
  resources (YouTube videos/playlists, web documentation, local PDFs/PPTs/videos/screenshots,
  and Competitive Programming problems from Codeforces, LeetCode, AtCoder, CodeChef,
  HackerRank, GeeksforGeeks, and InterviewBit via online-judge-tools and official APIs)
  and synthesizes high-density engineering reference manuals in 100% Roman-alphabet Hinglish
  (zero Devanagari characters) with PyMuPDF vector diagrams, monochrome aesthetic, and
  mandatory author branding (@issparsh @sumitsingh097 with the official X/Twitter glyph).
version: 2.3.0
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
  - competitive-programming
  - online-judge-tools
  - codeforces
  - leetcode
  - atcoder
  - codechef
  - hackerrank
  - geeksforgeeks
  - interviewbit
  - latex-math
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

# 🏆 Competitive Programming Problem Reference Manual:
# Inspect/fetch problem statement with full math and samples:
python thenuke_cli.py fetch-problem "https://www.codechef.com/problems/FLOW001"
python thenuke_cli.py fetch-problem "https://www.hackerrank.com/challenges/simple-array-sum/problem"
python thenuke_cli.py fetch-problem "https://www.geeksforgeeks.org/problems/missing-number-in-array1416/1"
python thenuke_cli.py fetch-problem "https://www.interviewbit.com/problems/max-sum-contiguous-subarray/"

# Full compilation to production-grade PDF:
python thenuke_cli.py run "https://codeforces.com/problemset/problem/1915/C" --preset senior_architect_faang --skip-cleanup

# 📚 Canonical Git Reference Manual Compiler:
python thenuke_cli.py compile-git --output output/Git_Reference_Manual.pdf

# 📝 Grounded Extractive Notes Synthesizer (from arbitrary ingested sources):
python thenuke_cli.py ingest-notes "https://youtu.be/..." --topic "Modern Distributed Systems" --output output/Notes.pdf

# Individual stages
python thenuke_cli.py ingest "https://youtube.com/..." # Fast path: subtitles only (use --download-video for full streams)
python thenuke_cli.py grill --preset senior_architect_faang
python thenuke_cli.py synthesize
python thenuke_cli.py compile output/thenuke_manual_*.md --branding "Prepared by @issparsh @sumitsingh097"
python thenuke_cli.py qa output/thenuke_manual_*.pdf --profile auto --report output/qa_report.json
python thenuke_cli.py clean
```

## Installation

```bash
# Editable install with core dependencies:
pip install -e .

# Or install from requirements.txt:
pip install -r requirements.txt

# Optional extras:
pip install -e ".[cp]"          # Competitive programming tools (online-judge-tools)
pip install -e ".[whisper]"     # Local audio transcription (faster-whisper)
pip install -e ".[dev]"         # Test suite runner (pytest)
pip install -e ".[cp,whisper,dev]" # All optional extras
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
              ├──► [Evidence Layer: CorpusIndexer]  →  EvidenceSpans (transcripts, code, tables, prose)
              │         │
              │         ▼
              │    [Extractive Notes Synthesizer]  →  Publication-grade grounded notes
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
  • PyMuPDF / ReportLab vector shapes: Call Stack, Heap, Event Loop, Commit DAGs
  • Monochrome palette: #000000 / #222222 / #CCCCCC / #F8F8F8
  • Official X/Twitter vector glyph + "Prepared by @issparsh @sumitsingh097"
  • ISO A4, Helvetica body, Courier code, running headers & footers
              │
              ▼
[R5: Multi-Profile QA Audit]  →  qa_report.json
  • Profiles: git | js | cp | notes | auto
  • Pass 1 Visual: 150 DPI rasterization, text overflow, orphan headers, margin bounds
  • Pass 2 Textual: zero Devanagari, macro escapes, profile-specific structure & branding
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

### Layout Geometry & Running Footers
- **Two-Column Boundary Pinning (Zero Overlap Invariant):**
  - **Left Margin ($x = 54.0\text{ pt}$):** Running page count and edition title: `Page {pno} of {total_pages} • Monochrome Reference Edition`.
  - **Right Margin ($x = 541.28\text{ pt}$):** Official author branding and vector 𝕏 glyph: `Prepared by @issparsh @sumitsingh097 𝕏`.
  - **Gutter:** Strict minimum $>150\text{ pt}$ clearance between strings. Text overlap is strictly prohibited across all pages.
- **Header Line:** Subtle 0.5 pt hairline at $y = 800\text{ pt}$ with uppercase running title and dynamic chapter tracker.

### Dynamic 100 Quotes Library
- Hand-curated library of 100 foundational quotes from legendary computing, engineering, philosophy, and polymath figures (Alan Turing, Donald Knuth, Edsger Dijkstra, Richard Feynman, Grace Hopper, Ada Lovelace, Fred Brooks, Leslie Lamport, Ludwig Wittgenstein, Claude Shannon, Albert Einstein, Leonardo da Vinci, Seneca, Marcus Aurelius, etc.).
- Tagged across 8 core domains (`systems`, `software_engineering`, `algorithms`, `debugging`, `curiosity`, `simplicity`, `learning`, `mastery`).
- Cover pages dynamically fetch quotes via `get_quote(topic=..., seed=...)` ensuring each manual receives an authoritative, contextual quote.

### Universal Domain Curricula & Unconstrained Phase Allocation
- **Universal Agnostic Architecture:** Capable of generating reference manuals for ANY topic (Computer Science, English Learning, Economics, Physics, Distributed Systems, Compilers, etc.).
- **Unconstrained Phase Count ($N$ Phases):** Never restricted to a fixed 9-phase model. Supports 4, 6, 8, 12, or arbitrary $N$ phases based on depth and topic needs.
- **Dynamic Syllabus Chunking:** Table of contents partitions phases into clean roman-numeral parts (`PART I`, `PART II`, etc.) with automatic page budgeting.

### Git Artifact Security & Repository Policy
- **ZERO PDF Binaries in Git:** All `.gitignore` configurations enforce `*.pdf`, `output/`, and `scratch/`. PDFs are strictly local artifacts generated to `~/Downloads/` or `~/thenuke_workspace/output/`.
- Repositories store 100% clean, reproducible source code, vector drawing engines, test suites, and documentation.

### Competitive Programming Problem Ingestion & Rendering (Codeforces, LeetCode, AtCoder)
- **Dedicated Ingestion Module (`scripts/ingestion/cp_problem.py`):**
  - Detects and specially routes URLs from:
    - Codeforces: `codeforces.com/problemset/problem/...`, `codeforces.com/contest/.../problem/...`, `codeforces.com/gym/...`
    - LeetCode: `leetcode.com/problems/...` (via official GraphQL query)
    - AtCoder: `atcoder.jp/contests/.../tasks/...` (converts `<var>` to LaTeX)
  - Extracts title, time limit, memory limit, difficulty, tags, problem statement, input/output specifications, constraints, and all sample inputs/outputs.
- **LaTeX Math Preservation & Vector Rendering:**
  - All mathematical expressions survive intact without entity corruption or math stripping (e.g. $(-1)^{a+b}S^2$, $1 \le n \le 10^5$, $\sum_{i=1}^n a_i = S^2$, fractions, sub/superscripts).
  - Converted via `latex_to_reportlab_html` into native ReportLab vector rich-text tags (`<super>`, `<sub>`, `&le;`, `&ge;`, `&Sigma;`, italicized math fonts) aligned directly on canvas baselines.
- **Monospaced Codeforces-Style Sample Boxes (`:::sample`):**
  - Samples are rendered as 2-column shaded tables with monospaced Courier font (`Input` vs `Output`) and optional editorial explanations.
  - Line breaks inside `<div class="test-example-line">` are strictly preserved (no line-collapsing bugs).
- **Structured Reference Manual Format:**
  - Document Title & Subtitle + Author Branding (`Prepared by @issparsh @sumitsingh097 𝕏`).
  - Shaded Metadata Badge (`Platform`, `Problem ID`, `Time Limit`, `Memory Limit`, `Tags`).
  - Mathematical Problem Statement, Input Specification, Output Specification, Constraints.
  - Formatted Sample Boxes.
  - Senior Architect Roman Hinglish Invariant Analysis (`[MENTAL MODEL]`, `[ENGINEERING GOTCHA]`, zero Devanagari).
  - Clean ISO A4 aesthetic with running headers and official vector Twitter/X footers on every page.

### Ingestion Invariants & Honest Communication (Strict Operational Rule)
- **Subtitles-First Priority (Fast Path):**
  - Always attempt subtitle extraction first using `--skip-download` (`hi-orig,hi,en,en.*,hi.*`). Subtitles download in 1–2 seconds with zero video bandwidth consumption.
  - **ABSOLUTE INVARIANT: NEVER invoke or mention Faster-Whisper when subtitles are available.** Whisper is strictly a fallback for videos with zero subtitle tracks. Mentioning Whisper or GPU overhead when captions were already available is a critical failure mode.
- **Explicit Ingestion Modes:**
  - `Fast Path` (`--subtitles-only`): 2-second subtitle ingestion. Ideal when narrative transcript + native ReportLab vector diagrams are sufficient.
  - `Full Visual Path` (`--download-video`): Downloads 720p MP4 and extracts scene-change frames via ffmpeg for direct multimodal vision analysis.
- **Video Frame Analysis Strategy & Interactive Intake Protocol (Token Economics vs. Visual Fidelity):**
  - **Mandatory User Inquiry Before Processing Video Frames:**
    When ingesting a video with visual slides, diagrams, or code demos, the AI assistant **MUST ask the user** (or prompt during the intake/grilling phase) which frame analysis strategy to use:
    1. **Direct AI Multimodal Visual Analysis (Frame-by-Frame):**
       - The AI assistant directly inspects extracted frames using multimodal vision (`view_file`).
       - *Capability:* Captures high-density architecture diagrams, complex data visualizations, fMRI scans, slide footnotes, and unread academic citations with zero OCR distortion.
       - *Token & Context Limit Warning:* Token-intensive. Best suited for short-to-medium videos (< 30–60 minutes, TED talks, keynotes, targeted tutorials). For a long video (e.g. 5–10 hours), inspecting thousands of frames will exhaust model context limits and consume massive token budgets.
    2. **Programmatic OCR Pipeline (`--ocr-frames` / `ocr_mode=True`):**
       - The ingestion engine runs local Apple Vision / OCR across extracted frames and saves text directly into metadata and transcript corpus (`ocr_text`).
       - *Capability:* Extremely token-efficient and fast. Extracts textual code, terminal commands, and bullet points without consuming vision context tokens.
       - *Recommended for:* Long multi-hour video courses, bootcamps, and semester lecture series (2h–10h+) where context preservation is critical.
  - **Interactive Inquiry Prompt Template:**
    When ingesting a video without an explicit user directive, prompt the user:
    > *"Video Frame Analysis Approach:*
    > *• Option 1: Direct AI Multimodal Visual Analysis (Highest visual fidelity for diagrams/slides; recommended for < 60 min videos; token-intensive).*
    > *• Option 2: Programmatic OCR Pipeline (Fast, token-efficient slide text extraction; recommended for long 2h–10h+ videos to avoid context exhaustion).*
    > *Which approach would you prefer for this video?"*
  - **Execution Rules:**
    - If user selects **AI Multimodal Visual Analysis**: Frames are cataloged into `extracted_images` with `ocr_text=""` and the AI inspects relevant scene frames directly via `view_file`.
    - If user selects **Programmatic OCR**: The ingestion pipeline runs OCR on the frames and populates `ocr_text` so the model reads the extracted text directly.
- **Zero-Pretense / Zero-Fluff Communication Policy:**
  - If a video is long (> 30 minutes, > 500 MB) and video downloading will take time:
    - State the reality to the user immediately in plain language:
      *"Subtitles downloaded in 2 seconds. Video is 140 min (~1.4 GB). Downloading video stream in background for visual frame extraction..."*
    - **NEVER silently kill a video download and pretend that visual frame analysis was done.**
    - If a download or command is cancelled or skipped due to size/timeout, state it plainly to the user in one sentence without deflection or technical jargon.
    - NEVER make up excuses or claim that frame-by-frame analysis occurred when frames were not extracted.

## Grilling Presets

| Preset | Level | Visual | Audience |
|--------|-------|--------|----------|
| `foundations` | foundations | strict_need_based | academic_foundations |
| `resource_parity` | resource_parity | balanced | production_engineering |
| `senior_architect_faang` | senior_architect | strict_need_based | faang_interview |

## 🏆 Multi-Platform Competitive Programming (CP) Ingestion Engine

`thenuke` provides a high-fidelity competitive programming problem ingestion engine across 7 major coding platforms:

| Platform | Best Strategy | Extraction Pipeline |
| :--- | :--- | :--- |
| **Codeforces** | Official API + DOM Parser | Extracts tags, rating, statement with `$$$...$$$` LaTeX math, multiline `test-example-line` samples, `oj-api` fallback |
| **LeetCode** | Official GraphQL API | Queries `question(titleSlug)` returning clean statement, topicTags, difficulty, hints, constraints, code stubs |
| **AtCoder** | DOM Parser (`.lang-en`) | Extracts limits, `<var>...</var>` / `\(...\)` LaTeX math, constraints, sample inputs/outputs, Kenkoooo API fallback |
| **CodeChef** | Official JSON API | Queries `api/contests/PRACTICE/problems/{code}`, extracts `problemComponents` (statement, constraints, input/output formats, `sampleTestCases`), hints |
| **HackerRank** | Official REST API | Queries `rest/contests/master/challenges/{slug}`, extracts native Markdown statement with LaTeX math (`$$t_{i+2} = ...$$`), constraints, sample cases |
| **GeeksforGeeks** | Next.js `__NEXT_DATA__` | Extracts `probData` with company tags (Amazon, Microsoft, Flipkart, etc.), topic tags, formatted examples, constraints, expected complexities |
| **InterviewBit** | Embedded `problemsData` | Extracts `meta.markdown_content` (description, constraints, input/output, example test cases), companies, hints |

### `online-judge-tools` (`oj` / `oj-api`) Integration
- `oj-api get-problem` CLI and python library `onlinejudge` are integrated as an automated testcase and limit verifier across AtCoder, Codeforces, CodeChef, and HackerRank.
- Uses browser user-agent (`BROWSER_HEADERS["User-Agent"]`) to avoid Cloudflare/bot bans.
- Normalizes contest paths (e.g. `codechef.com/PRACTICE/...`) automatically.
- CLI inspection helper: `python thenuke_cli.py fetch-problem <url> [--json]`.

## Environment Requirements

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | 3.14 tested on Apple M4 |
| PyMuPDF | 1.24+ | `pip install pymupdf` |
| reportlab | 4.1+ | `pip install reportlab>=4.1.0` (Publication PDF compiler) |
| online-judge-tools | 11.5+ | `pip install online-judge-tools` (`oj`, `oj-api`) |
| beautifulsoup4 | 4.15+ | `pip install beautifulsoup4` |
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
- `tests/test_cp_ingestion.py` — CP: Codeforces/LeetCode/AtCoder ingestion, LaTeX math preservation, sample boxes, end-to-end PDF & QA gate
- `tests/test_rendering_invariants.py` — Rendering Invariants: escape artifact defense, math parity scoping, typography fidelity, XML resilience, and Pass 2 textual QA audits

## Watertight Rendering Invariants Contract

To guarantee that broken formatting, raw escapes, unrendered math, or XML parsing errors **never occur**, the pipeline enforces the following invariants at all times:

### 1. Pre-Flight Input Normalization
- **Escape Character Sanitization:** All raw strings pass through `normalize_and_sanitize_markdown()`. Literal `\n- ` and `\n• ` are converted into real newline bullet points `\n• `.
- **LaTeX `\n` Protection:** Valid LaTeX commands beginning with `\n` (`\ne`, `\neq`, `\notin`, `\neg`, `\nu`, `\nabla`, `\natural`, etc.) are preserved verbatim, shielding them from naive newline splitting.
- **Tab Character Normalization:** Raw ASCII tab characters (`\t`) are expanded to 4 spaces, while raw string LaTeX macros like `\times`, `\theta`, `\to` remain untouched.
- **Inline Code Shielding:** Backtick fences (`...`) are extracted into placeholders before any character or delimiter transformations occur, preventing regex interference with internal symbols (e.g. `$`, `&`, `<`).

### 2. Math Parity & Scoped Delimiters
- **Strict Delimiter Scoping:** Inline math is matched via `(?<!\\)\$(?!\s)([^\$\n\r]+?)(?<!\s)\$`. Math expressions **cannot cross newlines** and **cannot have leading/trailing whitespace**, adhering strictly to Pandoc and KaTeX standards.
- **Parity Inversion Prevention:** Unmatched or trailing dollar signs on any line never bleed into subsequent lines or invert document math parity.
- **Currency Isolation:** Currency patterns (`$100`, `$50`) with trailing punctuation or whitespace are preserved verbatim as standard text.
- **Display Math Support:** Block math (`$$...$$`) is parsed independently with multi-line support and converted to ReportLab flowables.

### 3. Mathematical Typography Fidelity & Universal Macro Extinguisher
- **Universal Macro Extinguisher:** At the end of math translation, any unrecognized or platform-custom macro taking an argument (`\cmd{arg}`) automatically unpacks its content (`arg`), and any bare macro (`\cmd`) has its backslash stripped. Grouping braces `{}` and stray backslashes are eliminated. **Under zero circumstances can a raw LaTeX command or backslash escape into the document.**
- **Font-Safe Floor & Ceiling:** Functions `\lfloor ... \rfloor` and `\lceil ... \rceil` translate to `floor(...)` and `ceil(...)`, eliminating ReportLab Type 1 Helvetica encoding failures (which render as black tofu rectangles `■`).
- **Complete AMS-LaTeX & KaTeX Coverage:** Native translation for piecewise environments (`\begin{cases} ... \end{cases}`), matrices (`\begin{matrix}`), binomial coefficients (`\binom{n}{k}`, `{n \choose k}`, `{a \over b}`), nth roots (`\sqrt[n]{x}`), overlines/underlines, accents, and the entire Greek alphabet (`\alpha` ... `\Omega`).
- **Bare Operator Protection:** In prose outside math delimiters, bare LaTeX operators (`\le`, `\ge`, `\times`, `\cdot`, `\ne`, `\in`, `\notin`, `\to`, `\implies`) are automatically converted to valid HTML entities (`&le;`, `&ge;`, `&times;`, etc.).
- **Codeforces & Platform Delimiters:** Codeforces triple-dollars (`$$$...$$$`), alternative delimiters (`\(...\)`, `\[...\]`), and spaced delimiters (`$ x $`) are healed and normalized automatically.
- **AMS-LaTeX & KaTeX Alignment:** Superscripts and subscripts (`^`, `_`, `^{...}`, `_{...}`) are rendered with proportional downscaling (`<font size="6.5">`) for crisp, readable exponents.
- **Upright Roman Standards:** Digits, operators (`+`, `-`, `=`, `&minus;`), and mathematical functions (`gcd`, `lcm`, `min`, `max`, `log`, `ln`, `mod`, `sin`, `cos`, `tan`, `det`, `deg`, `dim`) are rendered upright; single Latin variables are italicized.
- **True Minus Signs:** Standalone negation and subtraction operators are rendered as `&minus;` rather than ambiguous ASCII hyphens.

### 4. Zero-Crash XML Resilience
- **Multi-Layer `safe_paragraph`:** All ReportLab `Paragraph` calls are wrapped with automatic fallback recovery:
  1. *Primary:* Direct ReportLab XML parse.
  2. *Secondary:* `emergency_xml_repair()` strips unknown font faces, balances open/close tags, and escapes bare `&` and `<`.
  3. *Tertiary:* Complete tag stripping with entity escaping (`&amp;`, `&lt;`, `&gt;`).
  4. *Ultimate:* Sanitized basic ASCII plain text.
- Under zero circumstances can a document compilation fail due to ExpatError, unclosed tags, or malformed user text.

### 5. Automated Textual QA Gate & Compilation Barrier
Pass 2 of `qa_audit_engine.py` inspects the compiled PDF text layer for:
- Zero Devanagari characters (100% Roman-alphabet Hinglish enforcement).
- Zero literal escape artifacts (`\n-`, `\n•`, `\n*`).
- Zero unrendered LaTeX macro commands (`\le`, `\ge`, `\times`, `\sum`, `\frac`, `\lfloor`, `\text`, etc.).
- Zero unrendered escaped symbols (`\%`, `\_`, `\&`, `\#`).
- Zero unrendered math delimiters (`$$$`).
- Zero leaked internal placeholders (`___CODE_PH_`, `___MATH_PH_`, etc.).
- Zero broken or tofu replacement characters (`\ufffd`, `\u25a0`, `■`).

Any violation halts publication immediately and triggers automatic remediation.

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
