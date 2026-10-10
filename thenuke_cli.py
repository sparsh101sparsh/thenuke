"""thenuke — Unified Pipeline CLI Runner.

Orchestrates the complete end-to-end documentation pipeline:
  1. Multi-source Ingestion (YouTube, Web, Local Files)
  2. Interactive Grilling Protocol (Scope Alignment)
  3. Reference Manual Synthesis (Roman Hinglish, Multi-Phase)
  4. Vector Diagramming & Branding (PyMuPDF, X glyph, Monochrome)
  5. Dual-Pass Visual QA & Quality Audit
  6. Post-Clearance Automated Data Cleanup

Usage:
  python thenuke_cli.py [command] [options]

Commands:
  run       Full pipeline: ingest → grill → synthesize → compile → qa
  ingest    Run only the ingestion engine
  grill     Run only the grilling protocol
  synthesize Run only the manual synthesizer
  compile   Run only the PDF compiler
  qa        Run only the QA audit on an existing PDF
  clean     Manually trigger post-clearance cleanup
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("thenuke")

# ---------------------------------------------------------------------------
# Path Constants
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = Path.home() / "thenuke_workspace"
CORPUS_PATH = WORKSPACE_ROOT / "nuke_ingestion_corpus.json"
GRILLING_PROFILE_PATH = WORKSPACE_ROOT / "grilling_profile.json"
OUTPUT_DIR = WORKSPACE_ROOT / "output"
SCRATCH_DIR = WORKSPACE_ROOT / "scratch"
QA_REPORT_PATH = OUTPUT_DIR / "qa_report.json"

BRANDING = "Prepared by @issparsh @sumitsingh097"

# Scratch subdirectories subject to post-clearance wipe
SCRATCH_SUBDIRS = [
    "frames",       # extracted video frames
    "audio",        # demuxed WAV / MP3 files
    "videos",       # downloaded 720p MP4 files
    "scrape_html",  # raw scraped HTML pages
]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _require_module(module_name: str, install_hint: str) -> Any:
    """Import a module or raise ImportError with install instructions."""
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError:
        raise ImportError(
            f"Required module '{module_name}' not found. Install via: {install_hint}"
        )


def _load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# Stage 1 — Ingestion
# ---------------------------------------------------------------------------

def run_ingest(
    sources: List[str],
    corpus_path: Path = CORPUS_PATH,
    download_video: bool = True,
) -> Path:
    """
    Run the multi-source ingestion engine on the provided source list.

    Sources can be:
    - YouTube URLs (video or playlist)
    - HTTP/HTTPS web URLs
    - Local file paths (PDF, PPTX, MP4, PNG, JPG)
    """
    from scripts.ingestion import run_ingestion

    logger.info("Stage 1 — Ingestion starting (%d source(s), download_video=%s)", len(sources), download_video)
    corpus = run_ingestion(sources, output_corpus_path=corpus_path, download_video=download_video)
    logger.info("Corpus written: %s (%d sources)", corpus_path, len(corpus.sources))
    return corpus_path


# ---------------------------------------------------------------------------
# Stage 2 — Grilling
# ---------------------------------------------------------------------------

def run_grill(
    corpus_path: Path = CORPUS_PATH,
    profile_path: Path = GRILLING_PROFILE_PATH,
    non_interactive: bool = False,
    preset: Optional[str] = None,
) -> Path:
    """
    Run the interactive grilling protocol to align document scope.

    In non-interactive mode (CI/scripting), applies the 'senior_architect'
    preset unless `preset` specifies otherwise.
    """
    from scripts.grilling.grilling_engine import (
        run_grilling_interview,
        GrillingProfile,
    )

    logger.info("Stage 2 — Grilling Protocol starting")
    corpus_data = _load_json(corpus_path) if corpus_path.exists() else {}

    # Extract detected topic from corpus if available
    detected_topic = "JavaScript"
    sources_list = corpus_data.get("sources", [])
    if sources_list:
        first_title = sources_list[0].get("title", "")
        if "git" in first_title.lower():
            detected_topic = "Git"
        elif "python" in first_title.lower():
            detected_topic = "Python"

    lod = "senior_architect"
    vit = "strict_need_based"
    focus = "faang_interview"

    if preset == "foundations":
        lod = "foundations"
        focus = "academic_foundations"
    elif preset == "resource_parity":
        lod = "resource_parity"
        focus = "production_engineering"
        vit = "balanced"
    elif preset and "architect" in preset:
        lod = "senior_architect"
        focus = "faang_interview"

    profile = run_grilling_interview(
        corpus=corpus_data if corpus_path.exists() else None,
        output_path=profile_path,
        interactive=not non_interactive and preset is None,
        level_of_detail=lod,
        visual_inclusion_threshold=vit,
        audience_focus=focus,
    )

    profile_dict = profile.to_dict()
    profile_dict["topic"] = detected_topic
    _save_json(profile_path, profile_dict)
    logger.info("Grilling profile written: %s (topic=%s)", profile_path, detected_topic)
    return profile_path


# ---------------------------------------------------------------------------
# Stage 3 — Synthesis
# ---------------------------------------------------------------------------

def run_synthesize(
    profile_path: Path = GRILLING_PROFILE_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    """
    Run the Reference Manual Synthesis Engine.
    Returns path to the synthesized Markdown file.
    """
    from scripts.synthesis.manual_synthesizer import SynthesisConfig, synthesize_and_write

    profile = _load_json(profile_path)
    logger.info("Stage 3 — Synthesis starting (level_of_detail=%s)", profile.get("level_of_detail", "senior_architect"))

    config = SynthesisConfig(
        topic=profile.get("topic", "JavaScript"),
        level_of_detail=profile.get("level_of_detail", "senior_architect"),
        visual_threshold=profile.get("visual_threshold", "strict_need_based"),
        audience_focus=profile.get("audience_focus", "faang_interview"),
        phases_to_include=profile.get("phases_to_include", list(range(1, 10))),
        include_appendices=profile.get("include_appendices", True),
        output_dir=str(output_dir),
    )

    md_path = synthesize_and_write(config)
    logger.info("Synthesis complete: %s", md_path)
    return md_path


# ---------------------------------------------------------------------------
# Stage 4 — Compile PDF
# ---------------------------------------------------------------------------

def run_compile(
    md_path: Path,
    output_dir: Path = OUTPUT_DIR,
    branding: str = BRANDING,
    topic: str = "Git",
) -> Path:
    """
    Compile the synthesized Markdown into a publication-grade branded PDF via ReportLab.
    """
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder

    logger.info("Stage 4 — Publication-Grade PDF Compilation starting: %s", md_path)
    md_text = Path(md_path).read_text(encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pdf_path = output_dir / f"thenuke_manual_{ts}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    builder = ReferenceManualBuilder(pdf_path, topic=topic)
    out = builder.compile(md_text)
    logger.info("Publication-grade PDF compiled: %s", out)
    return out


def run_multi_agent(
    topic: str = "Git",
    output_path: Optional[Path] = None,
    interactive: bool = False,
) -> Path:
    """
    Execute the full Multi-Agent Reference Manual authoring pipeline:
    1. Grilling (interactive interview or profile ingestion)
    2. ArchitectAgent: syllabus & contracts
    3. ResearchAgent: low-level systems briefings
    4. WriterAgent: Senior Staff Engineer Hinglish authoring
    5. DiagramAgent: ReportLab Drawing vector diagrams
    6. ReviewerAgent: 4-Pass QA gate
    7. ReportLab publication compilation
    """
    from scripts.multi_agent.agent_orchestrator import MultiAgentOrchestrator
    from scripts.grilling.grilling_engine import GrillingEngine

    profile = None
    if interactive:
        logger.info("Triggering interactive /grill-me clarification interview...")
        engine = GrillingEngine(topic=topic)
        profile = engine.conduct_interview()

    orchestrator = MultiAgentOrchestrator(topic=topic)
    if output_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"{topic}_Complete_Reference_Manual_{ts}.pdf"

    compiled_pdf, report = orchestrator.run_multi_agent_pipeline(output_path, profile=profile)
    if not report.passed:
        logger.error("Adversarial QA Gate reported issues: %s", report.issues)
    else:
        logger.info("Multi-Agent Publication Manual Ready: %s", compiled_pdf)
    return compiled_pdf


# ---------------------------------------------------------------------------
# Stage 5 — QA Audit
# ---------------------------------------------------------------------------

def run_qa(pdf_path: Path, report_path: Path = QA_REPORT_PATH) -> bool:
    """
    Run the dual-pass QA audit on the compiled PDF.
    Returns True if the audit passes.
    """
    from scripts.qa.qa_audit_engine import run_qa_audit

    logger.info("Stage 5 — QA Audit starting: %s", pdf_path)
    report = run_qa_audit(pdf_path, output_report_path=report_path)
    logger.info("QA Audit: %s", report.summary)

    if not report.overall_passed:
        logger.error("QA Audit FAILED. See report: %s", report_path)
        return False

    logger.info("QA Audit PASSED — PDF is production-ready.")
    return True


# ---------------------------------------------------------------------------
# Stage 6 — Post-Clearance Cleanup
# ---------------------------------------------------------------------------

def run_cleanup(scratch_dir: Path = SCRATCH_DIR, confirm: bool = True) -> None:
    """
    Wipe all intermediate artifacts after user clearance:
    - Downloaded 720p video files
    - Extracted video frames
    - Demuxed WAV audio files
    - Raw scraped HTML pages

    This is irreversible. Confirmation required unless `confirm=False`.
    """
    if confirm:
        print("\n⚠️  POST-CLEARANCE CLEANUP")
        print("The following scratch directories will be permanently deleted:")
        for sub in SCRATCH_SUBDIRS:
            p = scratch_dir / sub
            if p.exists():
                size_mb = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / (1024 * 1024)
                print(f"  {p}  ({size_mb:.1f} MB)")
        response = input("\nType 'DELETE' to confirm permanent deletion: ").strip()
        if response != "DELETE":
            print("Cleanup aborted.")
            return

    for sub in SCRATCH_SUBDIRS:
        p = scratch_dir / sub
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            logger.info("Deleted: %s", p)

    logger.info("Post-clearance cleanup complete.")


# ---------------------------------------------------------------------------
# Full Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_full_pipeline(
    sources: List[str],
    non_interactive: bool = False,
    preset: Optional[str] = None,
    skip_cleanup_prompt: bool = False,
    download_video: bool = True,
) -> Dict[str, Any]:
    """
    Execute the complete thenuke pipeline end-to-end.

    Returns a dict with paths to all produced artifacts and QA result.
    """
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    for sub in SCRATCH_SUBDIRS:
        (SCRATCH_DIR / sub).mkdir(parents=True, exist_ok=True)

    artifacts: Dict[str, Any] = {}

    # Stage 1
    corpus_path = run_ingest(sources, download_video=download_video)
    artifacts["corpus"] = str(corpus_path)

    # Stage 2
    profile_path = run_grill(corpus_path, non_interactive=non_interactive, preset=preset)
    artifacts["grilling_profile"] = str(profile_path)

    # Stage 3
    md_path = run_synthesize(profile_path)
    artifacts["markdown"] = str(md_path)

    # Stage 4
    pdf_path = run_compile(md_path)
    artifacts["pdf"] = str(pdf_path)

    # Stage 5
    qa_passed = run_qa(pdf_path)
    artifacts["qa_passed"] = qa_passed
    artifacts["qa_report"] = str(QA_REPORT_PATH)

    if not qa_passed:
        logger.error("Pipeline halted: QA audit did not pass. Review qa_report.json before distributing.")
        artifacts["status"] = "FAILED_QA"
        return artifacts

    # Stage 6 — Post-clearance cleanup
    if not skip_cleanup_prompt:
        print(f"\n✅ PDF is ready: {pdf_path}")
        print("Review the PDF, then confirm cleanup of intermediate files.")
        run_cleanup(SCRATCH_DIR, confirm=True)
    else:
        run_cleanup(SCRATCH_DIR, confirm=False)

    artifacts["status"] = "COMPLETE"
    return artifacts


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thenuke",
        description="thenuke — Multi-Modal Documentation Engine (Roman Hinglish Reference Manuals)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run — full pipeline
    run_p = sub.add_parser("run", help="Full pipeline: ingest → grill → synthesize → compile → qa")
    run_p.add_argument("sources", nargs="+", help="URLs or local file paths to ingest")
    run_p.add_argument("--subtitles-only", action="store_true", help="Fast path: ingest subtitles only (2s), skip 720p video stream download")
    run_p.add_argument("--non-interactive", action="store_true", help="Skip interactive grilling; use preset")
    run_p.add_argument("--preset", default=None, help="Grilling preset name (e.g. senior_architect_faang)")
    run_p.add_argument("--skip-cleanup", action="store_true", help="Auto-wipe scratch without confirmation")

    # ingest
    ingest_p = sub.add_parser("ingest", help="Run ingestion only")
    ingest_p.add_argument("sources", nargs="+", help="URLs or file paths")
    ingest_p.add_argument("--subtitles-only", action="store_true", help="Fast path: ingest subtitles only (2s), skip 720p video stream download")

    # grill
    grill_p = sub.add_parser("grill", help="Run grilling protocol only")
    grill_p.add_argument("--non-interactive", action="store_true")
    grill_p.add_argument("--preset", default=None)

    # synthesize
    synth_p = sub.add_parser("synthesize", help="Run synthesis only")
    synth_p.add_argument("--profile", default=str(GRILLING_PROFILE_PATH), help="Path to grilling_profile.json")

    # compile
    compile_p = sub.add_parser("compile", help="Compile Markdown → PDF only")
    compile_p.add_argument("markdown", help="Path to synthesized .md file")
    compile_p.add_argument("--branding", default=BRANDING)

    # qa
    qa_p = sub.add_parser("qa", help="QA audit only on existing PDF")
    qa_p.add_argument("pdf", help="Path to compiled PDF")
    qa_p.add_argument("--report", default=str(QA_REPORT_PATH))
    qa_p.add_argument("--strict", action="store_true", help="Fail on warnings too")

    # clean
    clean_p = sub.add_parser("clean", help="Manually wipe scratch directories")
    clean_p.add_argument("--yes", action="store_true", help="Skip confirmation")

    # multi-agent — collaborative authoring pipeline
    ma_p = sub.add_parser("multi-agent", help="Run collaborative multi-agent authoring & compilation")
    ma_p.add_argument("--topic", default="Git", help="Subject topic")
    ma_p.add_argument("--output", default=None, help="Target PDF path")
    ma_p.add_argument("--interactive", action="store_true", help="Run interactive /grill-me clarification interview")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "multi-agent":
        out_path = Path(args.output) if args.output else None
        pdf_path = run_multi_agent(
            topic=args.topic,
            output_path=out_path,
            interactive=args.interactive,
        )
        print(f"Multi-Agent Publication PDF: {pdf_path}")
        sys.exit(0)

    elif args.command == "run":
        result = run_full_pipeline(
            sources=args.sources,
            non_interactive=args.non_interactive,
            preset=args.preset,
            skip_cleanup_prompt=args.skip_cleanup,
            download_video=not getattr(args, "subtitles_only", False),
        )
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") == "COMPLETE" else 1)

    elif args.command == "ingest":
        corpus = run_ingest(args.sources, download_video=not getattr(args, "subtitles_only", False))
        print(f"Corpus: {corpus}")

    elif args.command == "grill":
        profile = run_grill(non_interactive=args.non_interactive, preset=args.preset)
        print(f"Profile: {profile}")

    elif args.command == "synthesize":
        profile_path = Path(args.profile)
        md_path = run_synthesize(profile_path)
        print(f"Markdown: {md_path}")

    elif args.command == "compile":
        md_path = Path(args.markdown)
        pdf_path = run_compile(md_path, branding=args.branding)
        print(f"PDF: {pdf_path}")

    elif args.command == "qa":
        pdf_path = Path(args.pdf)
        from scripts.qa.qa_audit_engine import run_qa_audit
        report = run_qa_audit(pdf_path, output_report_path=Path(args.report))
        print(report.summary)
        if not report.overall_passed:
            sys.exit(1)
        if args.strict and (report.pass1_visual.warning_count + report.pass2_textual.warning_count) > 0:
            sys.exit(1)

    elif args.command == "clean":
        run_cleanup(SCRATCH_DIR, confirm=not args.yes)


if __name__ == "__main__":
    main()
