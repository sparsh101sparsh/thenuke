"""Multi-Agent Authoring Orchestrator for thenuke.

Coordinates the collaborative pipeline across:
- Grilling Profile Ingestion
- ArchitectAgent: Curriculum planning & diagram contract definition
- ResearchAgent: Low-level systems briefings
- WriterAgent: High-density Senior Staff Engineer Hinglish authoring
- DiagramAgent: Publication-grade vector diagram validation
- ReviewerAgent: Adversarial 4-Pass QA auditing
- ReportLab Engine: Publication-grade PDF compilation
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from scripts.multi_agent.architect_agent import ArchitectAgent
from scripts.multi_agent.research_agent import ResearchAgent
from scripts.multi_agent.writer_agent import WriterAgent
from scripts.multi_agent.diagram_agent import DiagramAgent
from scripts.multi_agent.reviewer_agent import ReviewerAgent, AuditReport
from scripts.diagramming.reportlab_engine import ReferenceManualBuilder

logger = logging.getLogger("thenuke.multi_agent")


class MultiAgentOrchestrator:
    """Central orchestrator managing multi-agent authoring and quality gating."""

    def __init__(self, topic: str = "Git"):
        self.topic = topic
        self.architect = ArchitectAgent(topic=topic)
        self.researcher = ResearchAgent(topic=topic)
        self.writer = WriterAgent(topic=topic)
        self.diagrammer = DiagramAgent()
        self.reviewer = ReviewerAgent()

    def run_multi_agent_pipeline(
        self,
        output_pdf_path: Path,
        profile: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Path, AuditReport]:
        """Executes the complete multi-agent pipeline and outputs a verified publication PDF."""
        logger.info(f"=== Multi-Agent Pipeline Started for '{self.topic}' ===")

        if profile is None:
            profile = {
                "level_of_detail": "senior_architect",
                "visual_threshold": "diagram_dense",
                "audience_focus": "faang_interview",
            }

        # Step 1: Architect Agent plans the curriculum contract
        logger.info(f"[Agent 1: Architect] Planning syllabus and diagram slot contracts for '{self.topic}'...")
        if self.topic.strip().lower() == "git":
            syllabus = self.architect.plan_curriculum(profile)
        else:
            syllabus = self.architect.plan_universal_curriculum(profile)
        logger.info(f"[Agent 1: Architect] Syllabus contracted: {len(syllabus.phases)} phases, {len(syllabus.diagram_slots)} diagram slots.")

        # Step 2: Diagram Agent validates registered vector diagrams
        logger.info("[Agent 2: Diagrammer] Validating registered vector diagram flowables...")
        for slot in syllabus.diagram_slots:
            valid, err = self.diagrammer.validate_diagram(slot)
            if not valid:
                raise RuntimeError(f"Diagram validation failed for slot '{slot}': {err}")
        logger.info(f"[Agent 2: Diagrammer] All {len(syllabus.diagram_slots)} vector diagrams verified clean.")

        # Step 3: Writer Agent synthesizes the complete manual corpus
        logger.info("[Agent 3: Writer] Synthesizing high-density Roman Hinglish corpus with embedded diagram directives...")
        full_md = self.writer.assemble_full_manual(syllabus)
        logger.info(f"[Agent 3: Writer] Manual assembled: {len(full_md.splitlines())} lines, {len(full_md.split())} words.")

        # Step 4: Adversarial Reviewer audits the markdown source
        logger.info("[Agent 4: Reviewer] Pre-compilation adversarial audit on markdown source...")
        md_ok, md_issues = self.reviewer.audit_markdown_source(
            full_md,
            topic=self.topic,
            expected_phases=len(syllabus.phases),
        )
        if not md_ok:
            logger.warning(f"[Agent 4: Reviewer] Pre-compilation issues: {md_issues}")

        # Step 5: ReportLab Engine compiles publication PDF
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Compiler: ReportLab] Compiling publication-grade PDF to '{output_pdf_path}'...")
        builder = ReferenceManualBuilder(output_pdf_path, topic=self.topic)
        compiled_path = builder.compile(full_md)
        logger.info(f"[Compiler: ReportLab] Compilation finished: {compiled_path}")

        # Step 6: Adversarial Reviewer executes 4-Pass QA gate on compiled PDF
        logger.info("[Agent 4: Reviewer] Running 4-Pass Automated QA Gate on compiled PDF...")
        report = self.reviewer.audit_compiled_pdf(
            compiled_path,
            topic=self.topic,
            expected_phases=len(syllabus.phases),
        )
        logger.info(
            f"[Agent 4: Reviewer] Audit Complete: Pass1={report.pass_1_layout_clean}, "
            f"Pass2(0% Devanagari)={report.pass_2_zero_devanagari}, "
            f"Pass3(Diagrams)={report.pass_3_diagram_density}, "
            f"Pass4(Drills)={report.pass_4_drills_complete}, "
            f"Total Pages={report.total_pages}"
        )

        return compiled_path, report
